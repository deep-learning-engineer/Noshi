from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db import connections

from savings_accounts.models import SavingsAccount


class Command(BaseCommand):
    help = "Calculates interest on active or frozen savings accounts with today's accrual date"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Interest accrual on savings accounts begins..."))

        today = timezone.localdate()

        with db_transaction.atomic():
            savings_accounts = SavingsAccount.objects.filter(
                next_interest_date=today,
                bank_account__status__in=['active', 'frozen']
            ).select_related('bank_account').select_for_update()

            if not savings_accounts.exists():
                self.stdout.write("There are no savings accounts to earn interest today.")
                self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Interest accrual completed."))
                return

            self.stdout.write(f"Found {savings_accounts.count()} accounts to accrue interest.")

            for account in savings_accounts:
                self.stdout.write(f"Invoice processing {account.bank_account.account_number}...")

                try:
                    with db_transaction.atomic():
                        min_balance = account.min_balance
                        interest = account.calculate_interest()
                        self.stdout.write(self.style.SUCCESS(
                            f"The amount on which interest will be charged: {min_balance:.2f}\n" +  # noqa
                            f"Interest has been accrued: {interest:.2f} {account.bank_account.currency}"
                        ))
                        self.stdout.write(self.style.SUCCESS(
                            f"Next accrual date: {account.next_interest_date}"
                        ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Error in calculating interest on the account {account.bank_account.account_number}: {str(e)}"
                    ))

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Interest accrual completed."))
