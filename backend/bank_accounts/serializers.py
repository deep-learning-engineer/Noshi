from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction as db_transaction

from .models import (
    BankAccount,
    BankAccountInvitation,
    UserBankAccount
)
from users.models import User
from users.serializers import UserSerializer
from core.config import AppConfig


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


class PublicBankAccountSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            'account_number',
            'owner',
            'currency',
        ]


class ChangeAccountUsersSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    phone = serializers.CharField()

    def validate(self, attrs):
        account_number = attrs['account_number']
        phone = attrs['phone']
        request = self.context['request']

        try:
            account = BankAccount.objects.get(
                account_number=account_number,
                owner=request.user
            )
            if account.status != 'active':
                raise serializers.ValidationError("Only an active bank account can be changed")

            user = User.objects.get(phone=phone)
            if user == request.user:
                raise serializers.ValidationError("Unable to change account owner")

            attrs['account'] = account
            attrs['user'] = user
            return attrs

        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Bank account not found or you are not the owner")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this phone number not found")


class UserInvitationSerializer(serializers.ModelSerializer):
    inviter_details = UserSerializer(source='account.owner', read_only=True)
    account_number = serializers.CharField(source='account.account_number', read_only=True)

    class Meta:
        model = BankAccountInvitation
        fields = ['account_number', 'inviter_details', 'created_at']


class BankAccountInvitationSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=16, write_only=True)
    action = serializers.ChoiceField(choices=['accept', 'reject'])

    def validate(self, data):
        user = self.context['request'].user
        account_number = data.get('account_number')

        active_accounts_count = user.bank_accounts.filter(
            bank_account__status__in=['active', 'frozen']
        ).count()
        if active_accounts_count >= AppConfig.MAX_ACCOUNTS_PER_USER:
            raise ValidationError(
                {"error": f"You cannot have more than {AppConfig.MAX_ACCOUNTS_PER_USER} active or frozen bank accounts"}, # noqa
                code=status.HTTP_400_BAD_REQUEST
            )

        if not account_number:
            raise ValidationError("Account number is required.")

        try:
            account = BankAccount.objects.get(account_number=account_number)
            invitation = BankAccountInvitation.objects.get(account=account, invitee=user)
            data['invitation'] = invitation

            return data
        except BankAccount.DoesNotExist:
            raise ValidationError({"account_number": "Bank account with this number does not exist."})
        except BankAccountInvitation.DoesNotExist:
            raise ValidationError({"account_number": "No pending invitation found for this account and user."})

    def save(self):
        invitation = self.validated_data['invitation']
        user = self.context['request'].user
        action = self.validated_data['action']
        account = invitation.account

        if action == 'accept':
            try:
                with db_transaction.atomic():
                    UserBankAccount.objects.create(
                        user=user,
                        bank_account=account
                    )

                    invitation.delete()
                    return {"message": "Invitation accepted successfully."}
            except IntegrityError:
                raise ValidationError("You are already a member of this bank account.")
            except Exception as e:
                raise ValidationError(f"An error occurred while accepting the invitation: {e}")

        elif action == 'reject':
            invitation.delete()
            return {"message": "Invitation rejected successfully."}
