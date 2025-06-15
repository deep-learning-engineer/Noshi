from datetime import date

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import Prefetch

from backend.utils import get_user_active_accounts_count
from core.config import AppConfig
from .models import SavingsAccount
from .serializers import SavingsAccountSerializer
from bank_accounts.models import UserBankAccount
from bank_accounts.serializers import BankAccountSerializer


class SavingsAccountCreateView(generics.CreateAPIView):
    """
    API view for creating a savings account.
    First creates a regular bank account, then attaches a savings account to it.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BankAccountSerializer

    def create(self, request, *args, **kwargs):
        try:
            with db_transaction.atomic():
                active_accounts_count, active_savings_accounts_counts = get_user_active_accounts_count(request.user)
                if active_accounts_count >= AppConfig.MAX_ACCOUNTS_PER_USER:
                    raise ValidationError(
                        {"detail": f"You cannot have more than {AppConfig.MAX_ACCOUNTS_PER_USER} active or frozen bank accounts"}, # noqa
                    )
                elif active_savings_accounts_counts >= AppConfig.MAX_SAVINGS_ACCOUNTS_PER_USER:
                    raise ValidationError(
                        {"detail": f"You cannot have more than {AppConfig.MAX_SAVINGS_ACCOUNTS_PER_USER} active or frozen savings bank accounts"}, # noqa
                    )

                bank_account_serializer = self.get_serializer(data=request.data)
                bank_account_serializer.is_valid(raise_exception=True)
                bank_account = bank_account_serializer.save(owner=request.user)

                UserBankAccount.objects.create(
                    user=request.user,
                    bank_account=bank_account
                )

                savings_data = {
                    'goal_name': request.data.get('goal_name'),
                    'goal_amount': request.data.get('goal_amount'),
                    'interest_period': request.data.get('interest_period', 'monthly'),
                }

                savings_serializer = SavingsAccountSerializer(data=savings_data)
                savings_serializer.is_valid(raise_exception=True)

                savings_account = SavingsAccount.create(
                    bank_account=bank_account,
                    **savings_data
                )

                savings_serializer = SavingsAccountSerializer(savings_account)
                return Response({
                    'savings_account': savings_serializer.data
                }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavingsAccountCloseView(generics.DestroyAPIView):
    """
    API view for closing a savings account.
    The associated bank account can only be closed if the savings account balance is zero.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = SavingsAccount.objects.all()
    lookup_field = 'bank_account__account_number'
    lookup_url_kwarg = 'account_number'

    def destroy(self, request, *args, **kwargs):
        try:
            savings_account = self.get_object()

            if savings_account.bank_account.owner != request.user:
                return Response(
                    {'error': 'You are not the owner of this account'},
                    status=status.HTTP_403_FORBIDDEN
                )

            savings_account.bank_account.close_account()

            return Response(
                {'message': 'Savings account closed successfully'},
                status=status.HTTP_200_OK
            )

        except SavingsAccount.DoesNotExist:
            return Response(
                {'error': 'Savings account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SavingsAccountDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve details of a savings account.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsAccountSerializer
    lookup_field = 'bank_account__account_number'
    lookup_url_kwarg = 'account_number'

    def get_queryset(self):
        return SavingsAccount.objects.filter(
            bank_account__owner=self.request.user
        )


class UserSavingsAccountsListView(generics.ListAPIView):
    """
    API view to list all savings accounts associated with the authenticated user.
    Returns both accounts where user is owner and shared accounts.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsAccountSerializer

    def get_queryset(self):
        return SavingsAccount.objects.filter(
            bank_account__owner=self.request.user
        ).select_related('bank_account').prefetch_related(
            Prefetch('bank_account__users', queryset=UserBankAccount.objects.select_related('user'))
        )
