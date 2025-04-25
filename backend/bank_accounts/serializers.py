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
            'status',
            'users'
        ]
        read_only_fields = ['__all__']
        extra_kwargs = {
            'account_number': {'read_only': True},
            'balance': {'read_only': True}
        }

    def get_users(self, obj):
        """Returns a list of users associated with an account."""
        user_accounts = obj.users.all()
        return UserBankAccountSerializer(user_accounts, many=True).data



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

