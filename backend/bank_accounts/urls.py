from django.urls import path
from .views import (
    BankAccountCreateView,
    UserBankAccountsListView,
    BankAccountDetailView,
    BankAccountViewSet,
    UserByPhoneView,
    ChangeAccountUsersView,
    UserInvitationsListView,
    BankAccountInvitationsListView,
    BankAccountInvitationView
)

urlpatterns = [
    path('accounts/create/', BankAccountCreateView.as_view(), name='account-create'),
    path('accounts/', UserBankAccountsListView.as_view(), name='account-list'),
    path('accounts/<str:account_number>/', BankAccountDetailView.as_view(), name='account-detail'),
    path('accounts/<str:account_number>/close', BankAccountViewSet.as_view(), name='account-close'),
    path('accounts/phone/<str:phone>/', UserByPhoneView.as_view(), name='account-phone'),
    path('invitations/', UserInvitationsListView.as_view(), name='user-invitations-list'),
    path('invitations/<str:account_number>/',
         BankAccountInvitationsListView.as_view(),
         name='bank-account-invitations-list'),
    path('invitations/<str:account_number>/<str:phone>/',
         ChangeAccountUsersView.as_view(),
         name='change-user-to-account'),
    path('invitations/action',
         BankAccountInvitationView.as_view(),
         name='bank-account-invitation-action-by-account'),
]
