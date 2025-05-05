from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
from django.db import transaction as db_transaction


class TransactionView(APIView):
    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            with db_transaction.atomic():
                transaction = Transaction.create_transaction(
                    sender_account=data['sender_account'],
                    receiver_account=data['receiver_account'],
                    amount=data['amount'],
                    description=data.get('description', '')
                )

                result_serializer = TransactionSerializer(transaction)
                return Response(
                    result_serializer.data,
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
