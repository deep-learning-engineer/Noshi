from django.db.models.signals import post_save
from django.dispatch import receiver

from transactions.models import Transaction
from .logic import (
    award_first_transaction,
    award_big_wallet,
    award_loyal_client,
    award_currency_broker,
    award_family_bank,
    award_reverse_transfer,
    award_generosity,
    award_self_transfer,
    award_chain_reaction,
    award_payment_explorer,
)


@receiver(post_save, sender=Transaction)
def on_transaction_save(sender, instance, created, **kwargs):
    if not created:
        return

    sender_account = instance.sender_account
    sender_users = sender_account.users.select_related('user').all()

    if not sender_users:
        return

    sender_currency = sender_account.currency
    receiver_currency = instance.receiver_account.currency
    transaction_date = instance.created_at.date()

    for user_bank_account in sender_users:
        user = user_bank_account.user
        account_ids = user.bank_accounts.values_list('bank_account_id',
                                                     flat=True)
        transaction_count = Transaction.objects.filter(
            sender_account_id__in=account_ids
        ).count()

        award_big_wallet(user, transaction_date, account_ids)
        award_first_transaction(user, transaction_count)
        award_loyal_client(user, transaction_count)
        award_currency_broker(user, sender_currency, receiver_currency)
        award_family_bank(user)
        award_reverse_transfer(user, instance.receiver_account.owner)
        award_generosity(user)
        award_self_transfer(user, instance.sender_account, instance.receiver_account)
        award_chain_reaction(user, instance.sender_account)
        award_payment_explorer(user)
