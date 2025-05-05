from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import BankAccount, UserBankAccount
from .serializers import BankAccountSerializer, UserBankAccountSerializer


class BankAccountCreateView(generics.CreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        bank_account = serializer.save()
        UserBankAccount.objects.create(
            user=self.request.user,
            bank_account=bank_account
        )


class UserBankAccountsListView(generics.ListAPIView):
    serializer_class = UserBankAccountSerializer

    def get_queryset(self):
        return UserBankAccount.objects.filter(
            user=self.request.user
        ).select_related('bank_account')


class BankAccountDetailView(generics.RetrieveAPIView):
    serializer_class = BankAccountSerializer
    lookup_field = 'account_number'
    lookup_url_kwarg = 'account_number'

    def get_queryset(self):
        return BankAccount.objects.filter(
            users__user=self.request.user
        )
