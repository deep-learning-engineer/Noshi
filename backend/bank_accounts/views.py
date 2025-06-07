from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError

from core.config import AppConfig
from users.models import User
from users.serializers import UserSerializer
from .models import (
    BankAccount,
    UserBankAccount,
    BankAccountInvitation
)
from .serializers import (
    BankAccountSerializer,
    UserAccountsSerializer,
    ChangeAccountUsersSerializer,
    UserInvitationSerializer,
    BankAccountInvitationSerializer
)


class BankAccountCreateView(generics.CreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        active_accounts_count = user.bank_accounts.filter(
            bank_account__status__in=['active', 'frozen']
        ).count()

        if active_accounts_count >= AppConfig.MAX_ACCOUNTS_PER_USER:
            raise ValidationError(
                {"error": f"You cannot have more than {AppConfig.MAX_ACCOUNTS_PER_USER} active or frozen bank accounts"}, # noqa
                code=status.HTTP_400_BAD_REQUEST
            )

        bank_account = serializer.save(owner=user)
        UserBankAccount.objects.create(
            user=user,
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


class ChangeAccountUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, account_number, phone):
        serializer = ChangeAccountUsersSerializer(
            data={'account_number': account_number, 'phone': phone},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        account = serializer.validated_data['account']
        user = serializer.validated_data['user']

        if UserBankAccount.objects.filter(user=user, bank_account=account).exists():
            raise ValidationError(
                {"error": "This user is already a member of this account."},
                code=status.HTTP_400_BAD_REQUEST
            )

        active_accounts_count = user.bank_accounts.filter(
            bank_account__status__in=['active', 'frozen']
        ).count()

        if active_accounts_count >= AppConfig.MAX_ACCOUNTS_PER_USER:
            raise ValidationError(
                {"error": f"User cannot have more than {AppConfig.MAX_ACCOUNTS_PER_USER} active or frozen bank accounts"},  # noqa
                code=status.HTTP_400_BAD_REQUEST
            )

        try:
            BankAccountInvitation.objects.create(
                account=account,
                invitee=user
            )
        except IntegrityError:
            raise ValidationError(
                {"error": "The user has already been invited to the account"},
                code=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, account_number, phone):
        serializer = ChangeAccountUsersSerializer(
            data={'account_number': account_number, 'phone': phone},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        account = serializer.validated_data['account']
        user = serializer.validated_data['user']

        deleted_count, _ = UserBankAccount.objects.filter(
            user=user,
            bank_account=account
        ).delete()

        if deleted_count == 0:
            raise ValidationError(
                {"error": "The user is not present in this account"},
                code=status.HTTP_400_BAD_REQUEST
            )

        return Response("The user was successfully deleted", status=status.HTTP_200_OK)


class UserInvitationsListView(generics.ListAPIView):
    serializer_class = UserInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccountInvitation.objects.filter(
            invitee=self.request.user
        )


class BankAccountInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = BankAccountInvitationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            result = serializer.save()
            return Response(
                {"message": result["message"]},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
