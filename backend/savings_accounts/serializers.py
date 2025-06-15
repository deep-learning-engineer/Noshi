from rest_framework import serializers

from .models import SavingsAccount
from bank_accounts.serializers import BankAccountSerializer


class SavingsAccountSerializer(serializers.ModelSerializer):
    bank_account = BankAccountSerializer(read_only=True)

    class Meta:
        model = SavingsAccount
        fields = [
            'bank_account',
            'goal_name',
            'goal_amount',
            'min_balance',
            'interest_rate',
            'interest_period',
            'next_interest_date',
        ]
        read_only_fields = ['interest_rate', 'next_interest_date', 'min_balance']
