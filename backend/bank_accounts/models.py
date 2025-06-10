from django.db import models
from django.db.models import CheckConstraint, Q

from users.models import User


class BankAccount(models.Model):
    ACCOUNT_STATUS = [
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('closed', 'Closed'),
    ]

    PAYMENT_SYSTEMS = [
        ('VISA', 'Visa'),
        ('MC', 'Mastercard'),
        ('MIR', 'Мир'),
        ('UPI', 'UnionPay'),
        ('JCB', 'Japan Credit Bureau')
    ]

    PREFIXES = {
        'VISA': '4',
        'MC': '5',
        'MIR': '2',
        'UPI': '6',
        'JCB': '3528'
    }

    CURRENCIES = [
        ('RUB', 'Ruble'),
        ('USD', 'Dollar'),
        ('EUR', 'Euro'),
        ('CNY', 'Yuan')
    ]

    bank_account_id = models.AutoField(primary_key=True)
    account_number = models.CharField(max_length=16, unique=True, editable=False)
    payment_system = models.CharField(max_length=4, choices=PAYMENT_SYSTEMS, default='MIR')
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='RUB')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=ACCOUNT_STATUS, default='active', editable=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_accounts'
    )

    class Meta:
        db_table = 'bank_accounts'
        constraints = [
            CheckConstraint(
                check=Q(balance__gte=0),
                name='balance_not_negative'
            )
        ]

    def __str__(self):
        return f"Bank Account: {self.account_number} - {self.balance}"

    def is_active(self):
        return self.status == 'active'

    def save(self, *args, **kwargs):
        if not self.account_number:
            prefix = self.PREFIXES[self.payment_system]
            last_number = PaymentSystemCounter.get_next_number(self.payment_system)

            number_length = 16 - len(prefix)
            self.account_number = f"{prefix}{str(last_number).zfill(number_length)}"

        super().save(*args, **kwargs)


class PaymentSystemCounter(models.Model):
    payment_system = models.CharField(max_length=4, choices=BankAccount.PAYMENT_SYSTEMS, unique=True)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'payment_system_counter'

    @classmethod
    def get_next_number(cls, payment_system):
        counter, _ = cls.objects.get_or_create(
            payment_system=payment_system,
            defaults={'last_number': 0}
        )
        counter.last_number += 1
        counter.save()
        return counter.last_number


class UserBankAccount(models.Model):
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='users'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='bank_accounts'
    )

    class Meta:
        db_table = 'user_bank_accounts'
        unique_together = (('bank_account', 'user'),)

    def __str__(self):
        return f"UserBankAccount: {self.user} - {self.bank_account}"


class BankAccountInvitation(models.Model):
    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invitee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_account_invitations'
        unique_together = (('account', 'invitee'),)

    def __str__(self):
        return f"Invitation for {self.invitee} to account {self.account}"
