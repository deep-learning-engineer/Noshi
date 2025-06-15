from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BankAccount, UserBankAccount


@receiver(post_save, sender=BankAccount)
def ensure_owner_in_user_bank_account(sender, instance, created, **kwargs):
    if created:
        UserBankAccount.objects.get_or_create(
            user=instance.owner,
            bank_account=instance
        )
