from bank_accounts.models import BankAccount
from savings_accounts.models import SavingsAccount


def get_user_active_accounts_count(user):
    """
    Returns the number of active/frozen accounts of the user (including savings)

    Args:
        user: Django user object

    Returns:
        tuple[int]: Total number of active accounts (regular + savings), number of active savings accounts
    """
    base_accounts_count = BankAccount.objects.filter(
        users__user=user,
        status__in=['active', 'frozen']
    ).count()

    savings_accounts_count = SavingsAccount.objects.filter(
        bank_account__users__user=user,
        bank_account__status__in=['active', 'frozen']
    ).count()

    return base_accounts_count, savings_accounts_count
