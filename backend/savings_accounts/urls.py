from django.urls import path
from .views import (
    UserSavingsAccountsListView,
    SavingsAccountCreateView,
    SavingsAccountCloseView,
    SavingsAccountDetailView
)

urlpatterns = [
    path('savings/', UserSavingsAccountsListView.as_view(), name='savings-account-list'),
    path('savings/create/', SavingsAccountCreateView.as_view(), name='savings-account-create'),
    path('savings/<str:account_number>/', SavingsAccountDetailView.as_view(), name='savings-account-detail'),
    path('savings/<str:account_number>/close', SavingsAccountCloseView.as_view(), name='savings-account-close'),
]
