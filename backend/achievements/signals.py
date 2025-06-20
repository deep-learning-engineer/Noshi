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
    award_first_account,
    award_chain_reaction,
    award_payment_explorer,
)
from bank_accounts.models import UserBankAccount

from bank_accounts.models import BankAccount


@receiver(post_save, sender=BankAccount)
def on_account_created(sender, instance, created, **kwargs):
    if created:
        award_first_account(instance.owner)


@receiver(post_save, sender=UserBankAccount)
def on_co_owner_added(sender, instance, created, **kwargs):
    if created:
        owner = instance.bank_account.owner
        award_family_bank(owner)


@receiver(post_save, sender=Transaction)
def on_transaction_save(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.sender_account.owner
    account_ids = user.bank_accounts.values_list('bank_account_id', flat=True)
    txn_count = Transaction.objects.filter(sender_account_id__in=account_ids).count()

    award_big_wallet(user, instance.created_at.date(), account_ids)
    award_first_transaction(user, txn_count)
    award_loyal_client(user, txn_count)
    award_currency_broker(user, instance.sender_account.currency, instance.receiver_account.currency)
    award_reverse_transfer(user, instance.receiver_account.owner)
    award_generosity(user)
    award_chain_reaction(user, instance.sender_account)
    award_payment_explorer(user)
