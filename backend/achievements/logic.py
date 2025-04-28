from decimal import Decimal

from django.db.models import Sum

from .models import Achievement, UserAchievement
from transactions.models import TransactionDetail


def award_big_wallet(user, date):
    account_ids = user.bank_accounts.values_list('bank_account_id', flat=True)

    user_spent = (
        TransactionDetail.objects.filter(
            bank_account_id__in=account_ids,
            transaction__created_at__date=date
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )

    if user_spent > Decimal('100000'):
        achievement, _ = Achievement.objects.get_or_create(
            name='Большой кошелёк',
            defaults={'condition': 'Потратить больше 100000 рублей за день'}
        )
        UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement
        )