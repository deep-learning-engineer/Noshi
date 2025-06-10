from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ScheduledTransfers
from .serializers import ScheduledTransferSerializer, ScheduledTransferListSerializer


class ScheduledTransferCreateView(generics.CreateAPIView):
    """
    API view for creating a new scheduled translation.
    User must be authenticated.
    """
    permission_classes = [IsAuthenticated]
    queryset = ScheduledTransfers.objects.all()
    serializer_class = ScheduledTransferSerializer


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
            {"detail": "Scheduled translation ID successfully removed."},
            status=status.HTTP_200_OK
        )
