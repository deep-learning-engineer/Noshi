from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .models import ScheduledTransfers
from .serializers import ScheduledTransferSerializer, ScheduledTransferListSerializer
from bank_accounts.models import BankAccount


class ScheduledTransferCreateView(generics.CreateAPIView):
    """
    API view for creating a new scheduled translation.
    User must be authenticated.
    """
    permission_classes = [IsAuthenticated]
    queryset = ScheduledTransfers.objects.all()
    serializer_class = ScheduledTransferSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {"detail": "The planned translation has been successfully created."},
            status=status.HTTP_201_CREATED
        )


class ScheduledTransferListView(generics.ListAPIView):
    """
    API view to view all scheduled transfers, where the current user is the sender.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduledTransferListSerializer

    def get_queryset(self):
        return ScheduledTransfers.objects.filter(
            sender_account__users__user=self.request.user
        )


class ScheduledTransferDetailView(generics.RetrieveDestroyAPIView):
    """
    View API to view details of a scheduled transfer (GET) or delete it (DELETE).
    The user must be the sender of the transfer.
    """
    permission_classes = [IsAuthenticated]
    queryset = ScheduledTransfers.objects.all()
    serializer_class = ScheduledTransferListSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        return ScheduledTransfers.objects.filter(
            sender_account__users__user=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        return Response(
            {"detail": "Scheduled translation successfully removed."},
            status=status.HTTP_200_OK
        )


class AccountNumberScheduledTransfersView(generics.GenericAPIView):
    """
    API view to get all scheduled transfers related to a specific account
    (both incoming and outgoing) by account number.
    Authenticated user must be a member of the account.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduledTransferListSerializer

    def get(self, request, account_number):
        try:
            requested_account = BankAccount.objects.get(
                users__user=request.user,
                account_number=account_number
            )
        except BankAccount.DoesNotExist:
            raise NotFound({"detail": "Bank account not found."})

        scheduled_transfers = ScheduledTransfers.objects.filter(
            Q(sender_account=requested_account)
        )

        serializer = self.get_serializer(scheduled_transfers, many=True)
        return Response(serializer.data)
