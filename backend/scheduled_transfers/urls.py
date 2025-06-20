# scheduled_transfers/urls.py
from django.urls import path
from .views import (
    ScheduledTransferCreateView,
    ScheduledTransferListView,
    ScheduledTransferDetailView,
    AccountNumberScheduledTransfersView
)

urlpatterns = [
    path('scheduled-transfers/create/', ScheduledTransferCreateView.as_view(), name='scheduled-transfer-create'),
    path('scheduled-transfers/', ScheduledTransferListView.as_view(), name='scheduled-transfer-list'),
    path('scheduled-transfers/<int:pk>/', ScheduledTransferDetailView.as_view(), name='scheduled-transfer-detail-or-destroy'), # noqa
    path('scheduled-transfers/account/<str:account_number>/',
         AccountNumberScheduledTransfersView.as_view(),
         name='account-number-scheduled-transfers'),
]
