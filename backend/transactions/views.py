from datetime import timedelta, datetime
from decimal import Decimal

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import Transaction
from .serializers import TransactionSerializer
from bank_accounts.models import BankAccount
from users.serializers import UserSerializer


class TransactionView(APIView):
    """
    API view for creating new financial transactions between bank accounts.

    This endpoint facilitates the initiation of a direct money transfer
    from a sender's account to a receiver's account. It expects valid
    account numbers and an amount. Upon successful processing by the
    `Transaction.create_transaction` static method, it returns a
    summary of the initiated transfer, including receiver's basic
    information and currency details.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            Transaction.create_transaction(
                sender_account=data['sender_account'],
                receiver_account=data['receiver_account'],
                amount=data['amount'],
                description=data.get('description')
            )

            receiver_user = data['receiver_account'].owner
            receiver_info = UserSerializer(receiver_user).data

            response_data = {
                'sender_account': data['sender_account'].account_number,
                'receiver_account': data['receiver_account'].account_number,
                'receiver_info': receiver_info,
                'amount': str(data['amount']),
                'currency': data['sender_account'].currency,
                'description': data.get('description')
            }

            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionPreviewView(APIView):
    """
    API view for previewing potential financial transactions.

    This endpoint allows users to see the details of a transaction before
    committing it, especially useful for cross-currency transfers. It calculates
    and displays the converted amount based on the provided sender and receiver
    accounts' currencies. No transaction is created by this endpoint.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransactionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        converted_amount = Transaction.convert_to(
            data['sender_account'].currency,
            data['receiver_account'].currency,
            data['amount']
        )

        receiver_user = data['receiver_account'].owner
        receiver_info = UserSerializer(receiver_user).data

        response_data = {
            'sender_account': data['sender_account'].account_number,
            'receiver_account': data['receiver_account'].account_number,
            'receiver_info': receiver_info,
            'sender_currency': data['sender_account'].currency,
            'receiver_currency': data['receiver_account'].currency,
            'original_amount': str(data['amount']),
            'converted_amount': str(converted_amount),
            'description': data.get('description')
        }

        return Response(response_data)


class UserTransactionsView(APIView):
    """
    API view for retrieving a list of transactions associated with the authenticated user's accounts.

    This endpoint supports extensive filtering capabilities, allowing users to
    query transactions by:
        - `type`: 'all', 'income', or 'outcome' (default: 'all')
        - `period`: 'all', 'year', 'month', 'week', 'today', 'yesterday', or a specific date in 'YYYY-MM-DD' format (default: 'all')
        - `account`: A specific bank account number, or 'all' for all user's accounts (default: 'all')

    The response is structured to group transactions by date and provides
    summary statistics (total income/outcome per currency) for the filtered set.
    """ # noqa
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.query_params

        transaction_type = data.get('type', 'all')  # all, income, outcome
        period = data.get('period', 'all')  # all, year, month, week, today, yesterday, YYYY-MM-DD
        account_number = data.get('account', 'all')

        if account_number == 'all':
            user_accounts = BankAccount.objects.filter(
                users__user=user
            ).values_list('bank_account_id', flat=True)
        else:
            user_accounts = BankAccount.objects.filter(
                users__user=user,
                account_number=account_number
            )

        if not user_accounts:
            return Response(
                {"detail": "The user has no accounts"},
                status=status.HTTP_404_NOT_FOUND
            )

        transactions = Transaction.objects.filter(
            Q(sender_account_id__in=user_accounts) |  # noqa: W504
            Q(receiver_account_id__in=user_accounts)
        )

        # Filter by transaction type
        if transaction_type == 'income':
            transactions = transactions.filter(receiver_account_id__in=user_accounts)
        elif transaction_type == 'outcome':
            transactions = transactions.filter(sender_account_id__in=user_accounts)

        # Filter by period
        now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        match period:
            case 'all':
                pass
            case 'year':
                start_date = now - timedelta(days=365)
                transactions = transactions.filter(created_at__gte=start_date)
            case 'month':
                start_date = now - timedelta(days=30)
                transactions = transactions.filter(created_at__gte=start_date)
            case 'week':
                start_date = now - timedelta(days=7)
                transactions = transactions.filter(created_at__gte=start_date)
            case 'today':
                transactions = transactions.filter(created_at__gte=now.date())
            case 'yesterday':
                yesterday_start = now - timedelta(days=1)
                yesterday_end = yesterday_start + timedelta(days=1)
                transactions = transactions.filter(created_at__gte=yesterday_start, created_at__lt=yesterday_end)
            case _:
                try:
                    target_date = datetime.strptime(period, '%Y-%m-%d').date()
                    start_of_day = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
                    end_of_day = start_of_day + timedelta(days=1)
                    transactions = transactions.filter(created_at__gte=start_of_day, created_at__lt=end_of_day)
                except ValueError:
                    return Response(
                        {"error": "Invalid date format. Use YYYY-MM-DD."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        transactions_data = {}
        total_income = {}
        total_outcome = {}
        count = 0

        for transaction in transactions:
            create_at = transaction.created_at
            date = create_at.strftime("%Y-%m-%d")
            time = create_at.strftime("%Y-%m-%d %H:%M")
            is_income = transaction.receiver_account_id in user_accounts
            currency = transaction.receiver_account.currency if is_income else transaction.sender_account.currency

            user_for_info = transaction.sender_account.owner if is_income else transaction.receiver_account.owner
            user_info = UserSerializer(user_for_info).data

            if is_income:
                amount = transaction.converted_amount
                total_income[currency] = total_income.setdefault(currency, Decimal('0')) + amount
            else:
                amount = transaction.amount
                total_outcome[currency] = total_outcome.setdefault(currency, Decimal('0')) + amount

            transaction_data = {
                'date': time,
                'type': 'income' if is_income else 'outcome',
                'amount': amount,
                'currency': currency,
                'description': transaction.description,
                'user_info': user_info
            }

            transactions_data.setdefault(date, []).append(transaction_data)
            count += 1

            if is_income and transaction.sender_account_id in user_accounts:
                currency = transaction.sender_account.currency
                amount = transaction.amount
                total_outcome[currency] = total_outcome.setdefault(currency, Decimal('0')) + amount

                transaction_data = {
                    'date': time,
                    'type': 'outcome',
                    'amount': amount,
                    'currency': currency,
                    'description': transaction.description,
                    'user_info': user_info
                }

                transactions_data.setdefault(date, []).append(transaction_data)
                count += 1

        stats = {
            'total_income': total_income,
            'total_outcome': total_outcome,
            'count': count
        }

        return Response({
            'transactions': transactions_data,
            'stats': stats
        })
