from datetime import date
from django.contrib import admin
from .models import ScheduledTransfers


@admin.register(ScheduledTransfers)
class ScheduledTransfersAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender_account",
        "receiver_account",
        "amount",
        "frequency",
        "next_occurrence_date",
        "start_date",
        "end_date",
    )
    list_filter = ("frequency", "sender_account__currency")
    search_fields = (
        "sender_account__account_number",
        "sender_account__owner__first_name",
        "sender_account__owner__last_name",
        "sender_account__owner__phone",
        "receiver_account__account_number",
        "receiver_account__owner__first_name",
        "receiver_account__owner__last_name",
        "receiver_account__owner__phone",
        "description",
    )
    autocomplete_fields = ("sender_account", "receiver_account")
    actions = ["run_today"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Complete selected translations today")
    def run_today(self, request, queryset):
        updated = queryset.update(next_occurrence_date=date.today())
        self.message_user(request, f"Updated {updated} schedules.")
