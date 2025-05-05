from django.urls import path
from .views import (
    BankAccountCreateView,
    UserBankAccountsListView,
    BankAccountDetailView,
)

urlpatterns = [
    path('accounts/create/', BankAccountCreateView.as_view(), name='account-create'),
    path('accounts/', UserBankAccountsListView.as_view(), name='account-list'),
    path('accounts/<str:account_number>/', BankAccountDetailView.as_view(), name='account-detail'),
]