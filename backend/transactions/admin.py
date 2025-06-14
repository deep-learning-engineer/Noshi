from django.contrib import admin
from .models import Transaction, TransactionType


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = (
        "transaction_id",
        "created_at",
        "status",
        "sender_account",
        "receiver_account",
        "amount",
        "converted_amount",
    )
    list_filter = ("status", "sender_account__currency", "receiver_account__currency")
    search_fields = (
        "transaction_id",
        "sender_account__account_number",
        "receiver_account__account_number",
        "description",
    )
    autocomplete_fields = ("sender_account", "receiver_account", "type_id")
    readonly_fields = ("created_at",)

    @admin.action(description="Mark as failed")
    def mark_failed(self, request, queryset):
        updated = queryset.update(status="failed")
        self.message_user(request, f"Updated {updated} transactions.")


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "type_id")
    search_fields = ("name",)
