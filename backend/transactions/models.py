import requests

from decimal import Decimal
from django.db import models
from django.db import transaction as db_transaction

from bank_accounts.models import BankAccount
from core.config import AppConfig


class TransactionType(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "transaction_type"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_STATUS = [
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ]

    transaction_id = models.AutoField(primary_key=True)
    type_id = models.ForeignKey(TransactionType, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    converted_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Сумма в валюте получателя после конвертации",
    )
    sender_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='sent_transactions'
    )
    receiver_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='received_transactions'
    )

    class Meta:
        db_table = 'transactions'

    @staticmethod
    def convert_to(currency_sender, currency_receiver, amount):
        try:
            response = requests.get(
                AppConfig.CURRENCY_API_URL,
                params={"base_currency": currency_sender, "currencies": currency_receiver})
            response.raise_for_status()
            data = response.json()

            if 'data' not in data or currency_receiver not in data['data']:
                raise ValueError("Currency conversion data not available")

            rate = data['data'][currency_receiver]['value']
            return amount * Decimal(rate)
        except (requests.RequestException, ValueError) as e:
            raise ValueError("Currency conversion between different currencies is currently unavailable") from e

    @classmethod
    def create_transaction(cls, sender_account, receiver_account, amount, description=""):
        with db_transaction.atomic():
            transaction_type, _ = TransactionType.objects.get_or_create(
                name="Transfer",
                defaults={'name': 'Transfer'}
            )

            if sender_account.currency != receiver_account.currency:
                converted_amount = cls.convert_to(
                    sender_account.currency,
                    receiver_account.currency,
                    amount
                )
            else:
                converted_amount = amount

            transaction = cls.objects.create(
                type_id=transaction_type,
                status='completed',
                description=description,
                amount=amount,
                converted_amount=converted_amount,
                sender_account=sender_account,
                receiver_account=receiver_account
            )

            sender_account.balance = models.F('balance') - amount
            receiver_account.balance = models.F('balance') + converted_amount
            BankAccount.objects.bulk_update(
                [sender_account, receiver_account],
                ['balance']
            )

        return transaction

    def __str__(self):
        return (f"Transaction {self.transaction_id} - {self.amount} ({self.sender_account.currency}) → "
                f"{self.converted_amount or self.amount} ({self.receiver_account.currency})")
