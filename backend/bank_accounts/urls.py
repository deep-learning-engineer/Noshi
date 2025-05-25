from django.urls import path
from .views import (
    BankAccountCreateView,
    UserBankAccountsListView,
    BankAccountDetailView,
    UserByPhoneView
)

urlpatterns = [
    path('accounts/create/', BankAccountCreateView.as_view(), name='account-create'),
    path('accounts/', UserBankAccountsListView.as_view(), name='account-list'),
    path('accounts/<str:account_number>/', BankAccountDetailView.as_view(), name='account-detail'),
    path('accounts/phone/<str:phone>/', UserByPhoneView.as_view(), name='account-phone')
]