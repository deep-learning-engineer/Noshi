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
         name='bank-account-invitation-action-by-account')
]

""""
- Сделать красивый вывод баланса (сейчас 1е7)
- Убрать переход на следующую строку при нажатии Enter (Ввода)
- Когда пользователь выбирает историю по Расходам/ Даходам, должна быть возможность снова увидить историю и по доходам, и по расходам
- Добавить фильтрацию истории транзакций по Дням и по Счетам (картам)
- Убрать кнопку удалить пользователей и добавить для не владельцев счёта
- Для получения месечных трат (для счёта) в url добавить номер счёта (...&&account=<account_number>)
- Добавить кнопку: "Закрыть счёт" 
- По нажатию на кнопку "Настроить"
"""
