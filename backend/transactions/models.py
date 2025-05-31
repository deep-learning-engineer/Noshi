import os
import requests

from django.db import models
from bank_accounts.models import BankAccount
from django.db import transaction as db_transaction
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv() 


class TransactionType(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

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

    @staticmethod 
    def convert_to(currency_sender, currency_receiver, amount):
        URL = os.getenv("CURRENCY_API")
        try:
            response = requests.get(URL, params={"base_currency": currency_sender, "currencies": currency_receiver})
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data or currency_receiver not in data['data']:
                raise ValueError("Currency conversion data not available")
                
            exp = data['data'][currency_receiver]['value']
            return amount * Decimal(exp)
        except (requests.RequestException, ValueError) as e:
            raise ValueError("Currency conversion between different currencies is currently unavailable") from e

    @classmethod
    def create_transaction(cls, sender_account, receiver_account, amount, description=""):
        with db_transaction.atomic():
            transaction_type, _ = TransactionType.objects.get_or_create(
                name="Transaction",
                defaults={'name': 'Transaction'}
            )

            transaction = cls.objects.create(
                type_id=transaction_type,
                status='completed',
                description=description
            )

            TransactionDetail.objects.bulk_create([
                TransactionDetail(
                    transaction=transaction,
                    bank_account=sender_account,
                    amount=-amount
                ),
                TransactionDetail(
                    transaction=transaction,
                    bank_account=receiver_account,
                    amount=amount
                )
            ])

            sender_account.balance = models.F('balance') - amount
            receiver_account.balance = models.F('balance') + cls.convert_to(sender_account.currency, receiver_account.currency, amount)
            BankAccount.objects.bulk_update(
                [sender_account, receiver_account],
                ['balance']
            )

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.type.name}"
    
    
class TransactionDetail(models.Model):
    transaction = models.ForeignKey(
        Transaction, 
        on_delete=models.CASCADE,
        related_name='details'
    )
    bank_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.PROTECT,
        related_name='transaction_details'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = (('transaction', 'bank_account'),)

    def __str__(self):
        return f"{self.transaction} - {self.bank_account} - {self.amount}"
    