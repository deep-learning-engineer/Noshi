import calendar

from django.db import models
from django.db import transaction as db_transaction
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from transactions.models import Transaction
from bank_accounts.models import BankAccount


class ScheduledTransfers(models.Model):
    FREQUENCY_CHOICES = [
        ('once', 'Однократно'),
        ('daily', 'Ежедневно'),
        ('weekly', 'Еженедельно'),
        ('bi-weekly', 'Раз в две недели'),
        ('monthly', 'Ежемесячно'),
        ('annually', 'Ежегодно'),
    ]

    sender_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='outgoing_scheduled_transfers'
    )
    receiver_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='incoming_scheduled_transfers'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, default="Money Transfer")
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='once',
    )
    next_occurrence_date = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_transfers'
        ordering = ['next_occurrence_date', 'start_date']

    def __str__(self):
        return (f"Запланированный перевод с {self.sender_account.account_number} на "
                f"{self.receiver_account.account_number} ({self.amount} {self.sender_account.currency}) "
                f"с {self.start_date} по {self.end_date}")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.next_occurrence_date = self.start_date

        super().save(*args, **kwargs)

    def calculate_next_occurrence_date_for_scheduling(self):
        """
        Рассчитывает следующую запланированную дату выполнения на основе частоты.
        Возвращает новую дату или None, если серия должна завершиться.
        Использует start_date.day как базовый день для ежемесячных/ежегодных расчетов.
        """
        current_date_to_calculate_from = self.next_occurrence_date or self.start_date
        if not current_date_to_calculate_from:
            return None

        if self.frequency == 'once':
            return None

        next_date = current_date_to_calculate_from
        today = timezone.localdate()
        target_day_of_month = self.start_date.day

        while next_date <= today:
            if self.frequency == 'daily':
                next_date += timedelta(days=1)
            elif self.frequency == 'weekly':
                next_date += timedelta(weeks=1)
            elif self.frequency == 'bi-weekly':
                next_date += timedelta(weeks=2)
            elif self.frequency == 'monthly':
                year = next_date.year
                month = next_date.month + 1

                if month > 12:
                    month = 1
                    year += 1

                day = min(target_day_of_month, calendar.monthrange(year, month)[1])

                next_date = next_date.replace(year=year, month=month, day=day)
            elif self.frequency == 'annually':
                year = next_date.year + 1
                month = next_date.month
                day = min(target_day_of_month, calendar.monthrange(year, month)[1])

                next_date = next_date.replace(year=year, month=month, day=day)
            else:
                return None

            if self.end_date and next_date > self.end_date:
                return None

        return next_date

    def process_and_reschedule(self):
        """
        Attempts to execute the transfer.
        If successful, it reschedules the next occurrence or deletes if the series is complete.
        If the transfer fails due to insufficient funds or a similar *recoverable* error,
        it reschedules for the next occurrence without deleting the schedule.
        For *critical* errors, the scheduled transfer is deleted.
        Returns True if the operation (execution/reschedule/deletion) is handled, False otherwise.
        """
        scheduled_transfer_id = self.pk
        log_prefix = f"Scheduled Transfer ID {scheduled_transfer_id}:"

        next_calculated_date = None

        try:
            with db_transaction.atomic():
                next_calculated_date = self.calculate_next_occurrence_date_for_scheduling()

                Transaction.create_transaction(
                    sender_account=self.sender_account,
                    receiver_account=self.receiver_account,
                    amount=self.amount,
                    description=self.description
                )
                print(f"DEBUG: {log_prefix} Transaction successfully created.")

                if self.frequency == 'once' or next_calculated_date is None:
                    self.delete()
                    print(f"DEBUG: {log_prefix} Deleted as series completed or was 'once'.")
                else:
                    self.next_occurrence_date = next_calculated_date
                    self.save(update_fields=['next_occurrence_date', 'updated_at'])
                    print(f"DEBUG: {log_prefix} Rescheduled to {self.next_occurrence_date}.")

                return True

        except Exception as e:
            print(f"WARNING: {log_prefix} Failed due to recoverable error (e.g., insufficient funds): {e}")

            if self.frequency == 'once' or next_calculated_date is None:
                self.delete()
                print(f"DEBUG: {log_prefix} Deleted after single attempt failure (was 'once' or series ended).")
            else:
                self.next_occurrence_date = next_calculated_date
                self.save(update_fields=['next_occurrence_date', 'updated_at'])
                print(f"DEBUG: {log_prefix} Rescheduled to {self.next_occurrence_date} after recoverable failure.")

            return False
