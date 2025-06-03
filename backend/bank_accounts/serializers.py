from rest_framework import serializers
from .models import BankAccount, UserBankAccount
from users.models import User
from users.serializers import UserSerializer


class BankAccountSerializer(serializers.ModelSerializer):    
    users = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            'account_number',
            'balance',
            'payment_system',
            'currency',
            'status',
            'users',
            'owner' 
        ]

        read_only_fields = ['account_number', 'balance', 'status', 'users']

    def get_users(self, obj):
        """Returns a list of users associated with an account."""
        return UserSerializer([ua.user for ua in obj.users.all()], many=True).data


class UserAccountsSerializer(serializers.ModelSerializer):
    account_numbers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'account_numbers']
    
    def get_account_numbers(self, obj):
        return list(
            obj.bank_accounts.filter(
                bank_account__status='active'
            ).values_list('bank_account__account_number', flat=True)
        )
        