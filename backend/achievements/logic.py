from datetime import timedelta
from typing import Iterable

from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from bank_accounts.models import UserBankAccount, BankAccount
from users.models import User
from .models import Achievement, UserAchievement
from transactions.models import Transaction


def _get_or_create(name: str, description: str) -> Achievement:
    return Achievement.objects.get_or_create(
        name=name,
        defaults={"condition": description}
    )[0]


def _award(user: User, achievement: Achievement) -> None:
    UserAchievement.objects.get_or_create(user=user, achievement=achievement)


def award_big_wallet(user: User, date, user_account_ids: Iterable[int]) -> None:
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


def award_first_transaction(user: User, transaction_count: int) -> None:
    if transaction_count == 1:
        ach = _get_or_create(
            "Первый перевод",
            "Совершить первый перевод денег"
        )
        _award(user, ach)


def award_loyal_client(user: User, transaction_count: int) -> None:
    if transaction_count >= 10:
        ach = _get_or_create(
            "Лояльный клиент",
            "Совершить 10 переводов"
        )
        _award(user, ach)


def award_currency_broker(user: User, sender_currency: str, receiver_currency: str) -> None:
    if sender_currency != receiver_currency:
        ach = _get_or_create(
            "Валютный брокер",
            "Отправить перевод в другой валюте"
        )
        _award(user, ach)


def award_family_bank(user: User) -> None:
    shared_accounts = UserBankAccount.objects.filter(user=user).values('bank_account')

    for entry in shared_accounts:
        count = UserBankAccount.objects.filter(bank_account=entry['bank_account']).exclude(user=user).count()
        if count >= 2:
            ach = _get_or_create("Семейный банк", "Вы владелец счёта с двумя и более другими пользователями")
            _award(user, ach)
            break


def award_reverse_transfer(sender_user: BankAccount, receiver_user: BankAccount) -> None:
    now = timezone.now()
    since = now - timedelta(hours=24)
    reverse_exists = Transaction.objects.filter(
        sender_account__owner=receiver_user,
        receiver_account__owner=sender_user,
        created_at__gte=since
    ).exists()

    if reverse_exists:
        ach = _get_or_create("Обратная связь", "Получить деньги обратно от получателя в течение 24 часов")
        _award(sender_user, ach)


def award_generosity(user: User) -> None:
    recent = Transaction.objects.filter(sender_account__owner=user).order_by('-created_at')[:5]
    unique_receivers = {t.receiver_account.owner_id for t in recent}

    if len(unique_receivers) >= 5:
        ach = _get_or_create("Щедрость", "Сделать 5 переводов подряд разным пользователям")
        _award(user, ach)


def award_self_transfer(user: User, sender_account: BankAccount, receiver_account: BankAccount) -> None:
    if sender_account == receiver_account:
        ach = _get_or_create("Проверка связи", "Совершить перевод самому себе")
        _award(user, ach)


def award_chain_reaction(user: User, sender_account: BankAccount) -> None:
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    recent_incoming = Transaction.objects.filter(
        receiver_account=sender_account,
        created_at__gte=five_minutes_ago
    ).exists()
    if recent_incoming:
        ach = _get_or_create("Цепная реакция", "Совершить перевод в течение 5 минут после получения денег")
        _award(user, ach)


def award_payment_explorer(user: User) -> None:
    used_systems = (
        BankAccount.objects
        .filter(users__user=user)
        .values_list('payment_system', flat=True)
        .distinct()
    )
    if len(set(used_systems)) >= 3:
        ach = _get_or_create("Платёжный путешественник", "Совершить переводы с 3 и более разных платёжных систем")
        _award(user, ach)
