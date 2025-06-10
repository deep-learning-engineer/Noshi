from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal

from .models import ScheduledTransfers
from bank_accounts.models import BankAccount
from bank_accounts.serializers import PublicBankAccountSerializer


class ScheduledTransferSerializer(serializers.ModelSerializer):
    sender_account = serializers.CharField(write_only=True, required=True)
    receiver_account = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = ScheduledTransfers
        fields = [
            'sender_account',
            'receiver_account',
            'amount',
            'description',
            'frequency',
            'start_date',
            'end_date',
        ]
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'end_date': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        request = self.context.get('request')
        user = request.user

        sender_account = data.get('sender_account')
        receiver_account = data.get('receiver_account')
        amount = data.get('amount')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        frequency = data.get('frequency')
        today = timezone.localdate()

        try:
            sender_account = BankAccount.objects.get(
                account_number=sender_account,
                status='active',
                users__user=user
            )
            data['sender_account'] = sender_account
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(
                {"sender_account": "The sender's account was not found, was not activated, or you do not have access to it."} # noqa
            )

        try:
            receiver_account = BankAccount.objects.get(account_number=receiver_account)
            data['receiver_account'] = receiver_account
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError({"receiver_account": "Recipient account not found."})

        if sender_account.pk == receiver_account.pk:
            raise serializers.ValidationError(
                {"receiver_account": "The sender and recipient account cannot be the same."}
            )

        if amount <= Decimal('0.01'):
            raise serializers.ValidationError({"amount": "The transfer amount must be at least 0.01"})

        if start_date < today:
            raise serializers.ValidationError({"start_date": "The start date cannot be in the past."})

        if end_date:
            if end_date < start_date:
                raise serializers.ValidationError({"end_date": "The end date cannot be earlier than the start date."})
            if frequency == 'once' and end_date != start_date:
                 raise serializers.ValidationError( # noqa
                     {"end_date": "For a one-time transfer the end date must match the start date or be empty."}
                 )

        return data

    def create(self, validated_data):
        scheduled_transfer = ScheduledTransfers.objects.create(
            **validated_data
        )
        return scheduled_transfer


class ScheduledTransferListSerializer(serializers.ModelSerializer):
    sender_account = PublicBankAccountSerializer
    receiver_account = PublicBankAccountSerializer

    class Meta:
        model = ScheduledTransfers
        fields = [
            'id',
            'sender_account',
            'receiver_account',
            'amount',
            'description',
            'frequency',
            'next_occurrence_date',
            'start_date',
            'end_date',
            'created_at',
        ]
        read_only_fields = fields
