from django.db.models.signals import post_save
from django.dispatch import receiver
from .logic import award_big_wallet
from transactions.models import TransactionDetail


@receiver(post_save, sender=TransactionDetail)
def on_transaction_detail_save(sender, instance, created, **kwargs):
    if not created:
        return

    transaction_date = instance.transaction.created_at.date()
    trans_action_user = instance.bank_account.users.first()

    if not trans_action_user:
        return
    award_big_wallet(user=trans_action_user, date=transaction_date)