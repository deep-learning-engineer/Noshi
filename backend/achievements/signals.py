from django.db.models.signals import post_save
from django.dispatch import receiver

from transactions.models import TransactionDetail
from .logic import (
    award_first_transaction,
    award_big_wallet,
    award_loyal_client,
    award_currency_broker,
)


@receiver(post_save, sender=TransactionDetail)
def on_transaction_detail_save(sender, instance, created, **kwargs):
    if not created or instance.amount >= 0:
        return

    user_bank_account = instance.bank_account.users.first()
    if not user_bank_account:
        return

    user = user_bank_account.user

    transaction_date = instance.transaction.created_at.date()

    award_big_wallet(user=user, date=transaction_date)

    sender_acc = instance.bank_account
    receiver_detail = instance.transaction.details.exclude(pk=instance.pk).first()
    receiver_acc = receiver_detail.bank_account if receiver_detail else None

    award_first_transaction(user)
    award_loyal_client(user)
    if receiver_acc:
        award_currency_broker(user, sender_acc, receiver_acc)
