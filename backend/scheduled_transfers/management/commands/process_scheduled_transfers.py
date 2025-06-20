from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Q

from scheduled_transfers.models import ScheduledTransfers


class Command(BaseCommand):
    help = 'Checks and completes scheduled bank transfers that are due. Deletes completed ones.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Starting scheduled transfers processing..."))

        today = timezone.localdate()

        due_transfers = ScheduledTransfers.objects.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today),
            next_occurrence_date__lte=today,
            start_date__lte=today
        ).select_for_update()

        if not due_transfers.exists():
            self.stdout.write("No scheduled transfers to process today.")
            self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Finished processing scheduled transfers."))
            return

        self.stdout.write(f"Found {due_transfers.count()} scheduled transfers due for processing.")

        for scheduled_transfer in list(due_transfers):
            pk = scheduled_transfer.pk
            self.stdout.write(f"Attempting to process scheduled transfer ID: {pk}...")

            try:
                with db_transaction.atomic():
                    success = scheduled_transfer.process_and_reschedule()

                    if success:
                        self.stdout.write(self.style.SUCCESS(
                            f"Scheduled transfer ID: {pk} processed successfully."
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"Failed to process scheduled transfer ID: {pk}."
                        ))
            except ScheduledTransfers.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Scheduled transfer ID: {pk} was already deleted in current operation."
                ))

        self.stdout.write(self.style.SUCCESS(f"[{timezone.now()}] Finished processing scheduled transfers."))
