from decimal import Decimal
from django.db.models import Sum, F
from .models import Achievement, UserAchievement
from transactions.models import TransactionDetail


def award_big_wallet(user, date) -> None:
    account_ids = user.bank_accounts.values_list('bank_account_id', flat=True)

    user_spent = (
            TransactionDetail.objects.filter(
                bank_account_id__in=account_ids,
                amount__lt = 0,
                transaction__created_at__date=date
            ).aggregate(total=Sum(F('amount') * -1))['total']
            or Decimal('0')
    )

    if user_spent > Decimal('100000'):
        achievement, _ = Achievement.objects.get_or_create(
            name='Большой кошелёк',
            defaults={'condition': 'Потратить больше 100000 рублей за день'}
        )
        UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement
        )


def _get_or_create(name: str, condition: str) -> Achievement:
    ach, _ = Achievement.objects.get_or_create(
        name=name, defaults={"condition": condition}
    )
    return ach


def _award(user, achievement: Achievement) -> None:
    UserAchievement.objects.get_or_create(user=user, achievement=achievement)


def award_first_transaction(user) -> None:
    total_sent = TransactionDetail.objects.filter(
        bank_account__users__user=user, amount__lt=0
    ).count()

    if total_sent == 1:
        ach = _get_or_create("Первый перевод",
                             "Совершить первый перевод денег")
        _award(user, ach)


def award_loyal_client(user) -> None:
    sent_total = TransactionDetail.objects.filter(
        bank_account__users__user=user, amount__lt=0
    ).count()

    if sent_total >= 10:
        ach = _get_or_create("Лояльный клиент",
                             "Совершить 10 переводов")
        _award(user, ach)


def award_currency_broker(user, sender_account, receiver_account) -> None:
    if sender_account.currency != receiver_account.currency:
        ach = _get_or_create("Валютный брокер",
                             "Отправить перевод в другой валюте")
        _award(user, ach)
