from decimal import Decimal
from django.db.models import Sum
from .models import Achievement, UserAchievement
from transactions.models import Transaction


def _get_or_create(name: str, description: str) -> Achievement:
    return Achievement.objects.get_or_create(
        name=name,
        defaults={"condition": description}
    )[0]


def _award(user, achievement: Achievement) -> None:
    UserAchievement.objects.get_or_create(user=user, achievement=achievement)


def award_big_wallet(user, date, user_account_ids) -> None:
    user_spent = (
        Transaction.objects.filter(
            sender_account_id__in=user_account_ids,
            created_at__date=date,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    )

    if user_spent >= Decimal('100000'):
        ach = _get_or_create(
            'Большой кошелёк',
            'Потратить больше 100000 за день'
        )
        _award(user, ach)


def award_first_transaction(user, user_account_ids, transaction_count) -> None:
    if transaction_count == 1:
        ach = _get_or_create(
            "Первый перевод",
            "Совершить первый перевод денег"
        )
        _award(user, ach)


def award_loyal_client(user, transaction_count) -> None:
    if transaction_count >= 10:
        ach = _get_or_create(
            "Лояльный клиент",
            "Совершить 10 переводов"
        )
        _award(user, ach)


def award_currency_broker(user, sender_currency, receiver_currency) -> None:
    if sender_currency != receiver_currency:
        ach = _get_or_create(
            "Валютный брокер",
            "Отправить перевод в другой валюте"
        )
        _award(user, ach)
