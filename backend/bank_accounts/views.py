from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
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
    PublicBankAccountSerializer,
    ChangeAccountUsersSerializer,
    UserInvitationSerializer,
    BankAccountInvitationSerializer
)


class BankAccountCreateView(generics.CreateAPIView):
    """
    API view for authenticated users to create a new bank account.

    Users are restricted by the `MAX_ACCOUNTS_PER_USER` limit defined in `AppConfig`
    for active or frozen accounts. Upon successful creation, the user is automatically
    linked as a member of the new bank account.
    """
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
    """
    API view to list all bank accounts associated with the authenticated user.

    This view retrieves accounts where the user is either the owner or a linked member.
    """
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(
            users__user=self.request.user
        )


class BankAccountDetailView(generics.RetrieveAPIView):
    """
    API view to get details of a specific bank account by its number.

    Authenticated user must be a member of the account to view its full details
    otherwise can only get information about the owner and currency of the account.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BankAccountSerializer
    lookup_field = 'account_number'
    lookup_url_kwarg = 'account_number'

    def get(self, request, account_number):
        try:
            requested_account = BankAccount.objects.get(account_number=account_number)
        except BankAccount.DoesNotExist:
            raise NotFound({"detail": "Bank account not found."})

        is_user_member = BankAccount.objects.filter(
            pk=requested_account.pk,
            users__user=request.user
        ).exists()

        if is_user_member:
            serializer = BankAccountSerializer(requested_account)
        else:
            serializer = PublicBankAccountSerializer(requested_account)

        return Response(serializer.data)


class UserByPhoneView(APIView):
    """
    API view to retrieve user details by phone number.

    This view is typically used to find and verify a user by their phone number,
    for example, when inviting them to a shared bank account.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, phone):
        try:
            user_found_by_phone = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this phone number not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        active_accounts_for_user = BankAccount.objects.filter(
            users__user=user_found_by_phone,
            status='active'
        )

        serializer = PublicBankAccountSerializer(active_accounts_for_user, many=True)
        return Response(serializer.data)


class ChangeAccountUsersView(APIView):
    """
    API view to manage users associated with a bank account.

    Allows the account owner (implicitly, via permissions) to send invitations
    to other users (POST) or remove existing users (or user invitations) (DELETE) from the shared account.
    Prevents inviting users already in the account or those who have exceeded the account's
    maximum limit.
    """
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
            deleted_count, _ = BankAccountInvitation.objects.filter(
                account=account,
                invitee=user
            ).delete()

            if deleted_count == 0:
                raise ValidationError(
                    {"error": "The user was not invited or was not a member of this bank account"},
                    code=status.HTTP_400_BAD_REQUEST
                )

            return Response("The invitation was successfully removed", status=status.HTTP_200_OK)

        return Response("The user was successfully deleted", status=status.HTTP_200_OK)


class UserInvitationsListView(generics.ListAPIView):
    """
    API view for an authenticated user to list all bank account invitations they have received.

    This view provides a comprehensive list of pending invitations, allowing the user
    to see who invited them and to which account.
    """
    serializer_class = UserInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccountInvitation.objects.filter(
            invitee=self.request.user
        )


class BankAccountInvitationsListView(generics.ListAPIView):
    """
    An API representation for an authenticated user to retrieve a list of
    all invitations they have sent for a given bank account.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        account_number = self.kwargs['account_number']
        invitations = BankAccountInvitation.objects.filter(
            account__owner=self.request.user,
            account__account_number=account_number
        ).select_related('invitee')

        return User.objects.filter(
            id__in=invitations.values_list('invitee_id', flat=True)
        )


class BankAccountInvitationView(APIView):
    """
    API view for an authenticated user to accept or decline a bank account invitation
    using a bank account number.

    Upon acceptance, the user becomes a member of the bank account, unless its maximum account limit is exceeded,
    and the invitation is deleted. Upon rejection, the invitation is simply deleted.
    """
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
