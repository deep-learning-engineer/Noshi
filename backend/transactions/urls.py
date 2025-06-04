from django.urls import path
from .views import TransactionView, TransactionPreviewView, UserTransactionsView

urlpatterns = [
    path('transactions/', TransactionView.as_view(), name='money-transaction'),
    path('transactions/preview/', TransactionPreviewView.as_view(), name='money-transactions-preview'),
    path('transactions/history', UserTransactionsView.as_view(), name='money-transactions-history')
]
