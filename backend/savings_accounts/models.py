import calendar

from decimal import Decimal
from datetime import date

from django.db import models
from django.db import transaction as db_transaction

from bank_accounts.models import BankAccount
from core.config import AppConfig


class SavingsAccount(models.Model):
    INTEREST_PERIOD_CHOICES = [
        ('monthly', 'Ежемесячно'),
        ('yearly', 'Ежегодно'),
    ]

    bank_account = models.OneToOneField(
        BankAccount,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='saving_account'
    )
    goal_name = models.CharField(max_length=100)
    goal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    min_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        editable=False,
    )
    interest_period = models.CharField(
        max_length=10,
        choices=INTEREST_PERIOD_CHOICES,
    )
    next_interest_date = models.DateField(
        null=True,
        blank=True,
    )
    is_first_deposit = models.BooleanField(default=True)

    class Meta:
        db_table = 'savings_accounts'

    def __str__(self):
        return f"Savings account {self.bank_account.account_number} - {self.goal_name}"

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.next_interest_date = obj.calculate_next_interest_date(from_date=date.today())
        obj.save()
        return obj

    def save(self, *args, **kwargs):
        self.interest_rate = AppConfig.INTEREST_RATES[self.interest_period]

        if not self.pk:
            self.next_interest_date = self.calculate_next_interest_date(from_date=date.today())

        super().save(*args, **kwargs)

    def calculate_next_interest_date(self, from_date):
        creation_date = self.bank_account.created_at.date()
        creation_day = creation_date.day

        if self.interest_period == 'monthly':
            year = from_date.year
            month = from_date.month + 1
            if month > 12:
                month = 1
                year += 1

            last_day_of_month = calendar.monthrange(year, month)[1]
            day = min(creation_day, last_day_of_month)
            return date(year, month, day)
        else:
            year = from_date.year + 1
            month = creation_date.month

            last_day_of_month = calendar.monthrange(year, month)[1]
            day = min(creation_day, last_day_of_month)
            return date(year, month, day)

    def calculate_interest(self):
        with db_transaction.atomic():
            if self.is_first_deposit:
                self.next_interest_date = self.calculate_next_interest_date(from_date=date.today())
                self.min_balance = self.bank_account.balance
                self.save()

                return Decimal('0')

            interest = min(self.min_balance, AppConfig.MAXIMUM_ACCRUAL_BALANCE) * self.interest_rate
            self.bank_account.balance += interest
            self.bank_account.save()

            self.min_balance = min(self.bank_account.balance, AppConfig.MAXIMUM_ACCRUAL_BALANCE)
            self.next_interest_date = self.calculate_next_interest_date(from_date=date.today())
            self.save()

        return interest
