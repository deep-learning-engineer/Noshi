from rest_framework import serializers
from .models import Transaction, BankAccount
from django.db import transaction as db_transaction
from decimal import Decimal


class TransactionSerializer(serializers.Serializer):
    sender_account = serializers.CharField(max_length=20)
    receiver_account = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True,
        default="Money Transfer"
    )

    def validate_sender_account(self, value):
        try:
            return BankAccount.objects.get(account_number=value)
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Sender account does not exist")

    def validate_receiver_account(self, value):
        try:
            return BankAccount.objects.get(account_number=value)
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Receiver account does not exist")

    def validate(self, data):
        sender = data['sender_account']
        receiver = data['receiver_account']
        amount = data['amount']

        if not sender.is_active():
            raise serializers.ValidationError({"sender_account": "Sender account is not active"})

        if not receiver.is_active():
            raise serializers.ValidationError({"receiver_account": "Receiver account is not active"})

        if sender.balance < amount:
            raise serializers.ValidationError({"amount": "Insufficient funds in sender's account"})

        if sender == receiver:
            raise serializers.ValidationError("Cannot transfer to the same account")

        return data
