from rest_framework import serializers
from .models import BankAccount, UserBankAccount
from users.models import User
from users.serializers import UserSerializer


class BankAccountSerializer(serializers.ModelSerializer):    
    users = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = [
            'account_number',
            'balance',
            'payment_system',
            'status',
            'users'
        ]

        read_only_fields = ['account_number', 'balance', 'status', 'users']

    def get_users(self, obj):
        """Returns a list of users associated with an account."""
        return UserSerializer([ua.user for ua in obj.users.all()], many=True).data


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    bank_account = BankAccountSerializer(read_only=True)
    bank_account_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccount.objects.all(),
        source='bank_account',
        write_only=True
    )

    class Meta:
        model = UserBankAccount
        fields = [
            'id',
            'user',
            'user_id',
            'bank_account',
            'bank_account_id'
        ]
        read_only_fields = ['id']


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
        