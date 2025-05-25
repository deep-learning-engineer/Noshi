from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Transaction
from .serializers import TransactionSerializer
from bank_accounts.models import UserBankAccount


class TransactionView(APIView):
    permission_classes = [IsAuthenticated] 
    
    def post(self, request):
        serializer = TransactionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            with db_transaction.atomic():
                Transaction.create_transaction(
                    sender_account=data['sender_account'],
                    receiver_account=data['receiver_account'],
                    amount=data['amount'],
                    description=data.get('description')
                )

                receiver_user = UserBankAccount.objects.get(
                    bank_account=data['receiver_account']
                ).user

                response_data = {
                    "sender_account": data['sender_account'].account_number,
                    "receiver_account": data['receiver_account'].account_number,
                    "receiver_info": {
                        "first_name": receiver_user.first_name,
                        "last_name": receiver_user.last_name
                    },
                    "amount": str(data['amount']),
                    "description": data.get('description')
                }

                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# class TransactionHistoryView(APIView):
#     def get(self, request, account_number):
#         try:
#             account = BankAccount.objects.get(account_number=account_number)
#             transactions = Transaction.objects.filter(
#                 details__bank_account=account
#             ).distinct().order_by('-created_at')
            
#             serializer = TransactionSerializer(transactions, many=True)
#             return Response(serializer.data)

#         except BankAccount.DoesNotExist:
#             return Response(
#                 {"error": "Account not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )
