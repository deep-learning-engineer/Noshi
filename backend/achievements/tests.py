import pytest

from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction

from bank_accounts.models import BankAccount, UserBankAccount
from .models import UserAchievement
from transactions.models import Transaction, TransactionType
from users.models import User


def create_user(email: str, phone: str, first: str = "Foo", last: str = "Bar") -> User:
    return User.objects.create_user(
        email=email,
        password="testpass123",
        phone=phone,
        first_name=first,
        last_name=last,
    )


def create_account(user: User, currency: str = "RUB") -> BankAccount:
    account = BankAccount.objects.create(owner=user, currency=currency)
    UserBankAccount.objects.create(user=user, bank_account=account)
    return account


def create_transfer(sender: BankAccount, receiver: BankAccount, amount: Decimal):
    t_type, _ = TransactionType.objects.get_or_create(name="Transfer")

    if sender.currency != receiver.currency:
        converted_amount = Transaction.convert_to(
            sender.currency,
            receiver.currency,
            amount
        )
    else:
        converted_amount = amount

    with db_transaction.atomic():
        Transaction.objects.create(
            type_id=t_type,
            status="completed",
            description="pytest",
            created_at=timezone.now(),
            amount=amount,
            converted_amount=converted_amount,
            sender_account=sender,
            receiver_account=receiver
        )

        sender.balance -= amount
        receiver.balance += converted_amount
        sender.save()
        receiver.save()


@pytest.fixture
def users():
    sender = create_user("sender@example.com", "70000000000", "Send", "User")
    receiver = create_user("receiver@example.com", "71111111111", "Recv", "User")
    return sender, receiver


@pytest.fixture
def accounts(users):
    sender_user, receiver_user = users
    sender_acc = create_account(sender_user, "RUB")
    receiver_acc_rub = create_account(receiver_user, "RUB")
    receiver_acc_usd = create_account(receiver_user, "USD")
    return sender_acc, receiver_acc_rub, receiver_acc_usd


@pytest.mark.django_db
def test_first_transaction_awarded(accounts):
    sender_acc, receiver_acc, _ = accounts

    create_transfer(sender_acc, receiver_acc, Decimal("1000.00"))

    sender_user = sender_acc.users.first().user
    assert UserAchievement.objects.filter(
        user=sender_user, achievement__name="Первый перевод"
    ).exists(), "Достижение 'Первый перевод' не выдано"


@pytest.mark.django_db
def test_loyal_client_after_ten_transfers(accounts):
    sender_acc, receiver_acc, _ = accounts

    for _ in range(10):
        create_transfer(sender_acc, receiver_acc, Decimal("50.00"))

    sender_user = sender_acc.users.first().user
    assert UserAchievement.objects.filter(
        user=sender_user, achievement__name="Лояльный клиент"
    ).exists(), "Достижение 'Лояльный клиент' не выдано после 10 переводов"


@pytest.mark.django_db
def test_currency_broker_different_currency(accounts):
    sender_acc, _, receiver_acc_usd = accounts

    create_transfer(sender_acc, receiver_acc_usd, Decimal("100.00"))

    sender_user = sender_acc.users.first().user
    assert UserAchievement.objects.filter(
        user=sender_user, achievement__name="Валютный брокер"
    ).exists(), "Достижение 'Валютный брокер' не выдано при переводе в другую валюту"


@pytest.mark.django_db
def test_big_wallet_over_100k_per_day(accounts):
    sender_acc, receiver_acc, _ = accounts

    create_transfer(sender_acc, receiver_acc, Decimal("150000.00"))

    sender_user = sender_acc.users.first().user
    assert UserAchievement.objects.filter(
        user=sender_user, achievement__name="Большой кошелёк"
    ).exists(), "Достижение 'Большой кошелёк' не выдано при сумме > 100000"
