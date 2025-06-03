from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import User
from .models import BankAccount, UserBankAccount
from .serializers import (
    BankAccountSerializer, 
    UserAccountsSerializer
)


class BankAccountCreateView(generics.CreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        bank_account = serializer.save(owner=self.request.user)
        UserBankAccount.objects.create(
            user=self.request.user,
            bank_account=bank_account
        )


class UserBankAccountsListView(generics.ListAPIView):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(
            users__user=self.request.user
        )


class BankAccountDetailView(generics.RetrieveAPIView):
    serializer_class = BankAccountSerializer
    lookup_field = 'account_number'
    lookup_url_kwarg = 'account_number'

    def get_queryset(self):
        return BankAccount.objects.filter(
            users__user=self.request.user
        )
        

class UserByPhoneView(APIView):
    permission_classes = [IsAuthenticated]  
    
    def get(self, request, phone):
        try:
            user = User.objects.get(phone=phone)   
            serializer = UserAccountsSerializer(user)
            return Response(serializer.data)  
        except User.DoesNotExist:
            return Response(
                {"error": "User with this phone number not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            