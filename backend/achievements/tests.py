import json
from pathlib import Path
from unittest.mock import patch
import pytest
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from bank_accounts.models import BankAccount, UserBankAccount
from .models import UserAchievement
from transactions.models import Transaction, TransactionType
from users.models import User
from achievements.logic import (
    award_family_bank,
    award_reverse_transfer,
    award_generosity,
    award_payment_explorer,
)


@pytest.fixture(autouse=True)
def mock_currency_api():
    """
    Перехватывает вызовы requests.get в transactions.models.convert_to
    и подсовывает данные из локального latest.json.
    Срабатывает для всех тестов автоматически.
    """
    json_path = Path(__file__).parent / "latest.json"
    rates = json.loads(json_path.read_text())

    with patch("transactions.models.requests.get") as mock_get:
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = rates
        yield


def create_user(email: str, phone: str, first: str = "Foo", last: str = "Bar") -> User:
    return User.objects.create_user(
        email=email,
        password="testpass123",
        phone=phone,
        first_name=first,
        last_name=last,
    )


def create_account(user: User, currency: str = "RUB") -> BankAccount:
    account = BankAccount.objects.create(owner=user, currency=currency, balance=10000000)
    UserBankAccount.objects.create(user=user, bank_account=account)
    return account


def create_transfer(sender: BankAccount, receiver: BankAccount, amount: Decimal) -> None:
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
def users() -> tuple[User]:
    sender = create_user("sender@example.com", "70000000000", "Send", "User")
    receiver = create_user("receiver@example.com", "71111111111", "Recv", "User")
    return sender, receiver


@pytest.fixture
def accounts(users) -> tuple[BankAccount]:
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


@pytest.mark.django_db
def test_family_bank_awarded(accounts):
    sender_acc, _, _ = accounts
    user = sender_acc.owner
    other1 = User.objects.create_user("o1@example.com", "pass", phone="70100000001", first_name="O1", last_name="X")
    other2 = User.objects.create_user("o2@example.com", "pass", phone="70100000002", first_name="O2", last_name="X")
    UserBankAccount.objects.create(user=other1, bank_account=sender_acc)
    UserBankAccount.objects.create(user=other2, bank_account=sender_acc)

    award_family_bank(user)

    assert UserAchievement.objects.filter(user=user, achievement__name="Семейный банк").exists()


@pytest.mark.django_db
def test_reverse_transfer_awarded(accounts):
    sender_acc, receiver_acc, _ = accounts
    sender_user = sender_acc.owner
    receiver_user = receiver_acc.owner

    Transaction.objects.create(
        type_id=TransactionType.objects.get_or_create(name="Test")[0],
        status="completed",
        description="rev",
        amount=Decimal("100.00"),
        converted_amount=Decimal("100.00"),
        sender_account=receiver_acc,
        receiver_account=sender_acc,
        created_at=timezone.now()
    )

    award_reverse_transfer(sender_user, receiver_user)

    assert UserAchievement.objects.filter(user=sender_user, achievement__name="Обратная связь").exists()


@pytest.mark.django_db
def test_generosity_awarded(accounts):
    sender_acc, _, _ = accounts
    user = sender_acc.owner

    for i in range(5):
        rcv = User.objects.create_user(f"rcv{i}@e.com", "p", phone=f"7999999999{i}", first_name="X", last_name="Y")
        rcv_acc = BankAccount.objects.create(owner=rcv, currency="RUB")
        UserBankAccount.objects.create(user=rcv, bank_account=rcv_acc)
        Transaction.objects.create(
            type_id=TransactionType.objects.get_or_create(name="Test")[0],
            status="completed",
            description="",
            amount=Decimal("10.00"),
            converted_amount=Decimal("10.00"),
            sender_account=sender_acc,
            receiver_account=rcv_acc
        )

    award_generosity(user)
    assert UserAchievement.objects.filter(user=user, achievement__name="Щедрость").exists()


@pytest.mark.django_db
def test_chain_reaction_awarded(accounts):
    sender_acc, receiver_acc, _ = accounts
    user = sender_acc.owner

    Transaction.objects.create(
        type_id=TransactionType.objects.get_or_create(name="Test")[0],
        status="completed",
        description="rev",
        amount=Decimal("100.00"),
        converted_amount=Decimal("100.00"),
        sender_account=receiver_acc,
        receiver_account=sender_acc,
        created_at=timezone.now()
    )

    from achievements.logic import award_chain_reaction
    award_chain_reaction(user, sender_acc)

    assert UserAchievement.objects.filter(user=user, achievement__name="Цепная реакция").exists()


@pytest.mark.django_db
def test_payment_explorer_awarded(users):
    sender, _ = users

    for ps in ["VISA", "MIR", "MC"]:
        acc = BankAccount.objects.create(owner=sender, payment_system=ps)
        UserBankAccount.objects.create(user=sender, bank_account=acc)

    award_payment_explorer(sender)

    assert UserAchievement.objects.filter(user=sender, achievement__name="Платёжный путешественник").exists()
