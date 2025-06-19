from django.contrib import admin
from .models import Transaction, TransactionType
from django.contrib.admin import SimpleListFilter


class SenderCurrencyFilter(SimpleListFilter):
    title = 'Sender currency'
    parameter_name = 'sender_currency'

    def lookups(self, request, model_admin):
        return [
            ('RUB', 'Ruble'),
            ('USD', 'Dollar'),
            ('EUR', 'Euro'),
            ('CNY', 'Yuan'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(sender_account__currency=self.value())
        return queryset


class ReceiverCurrencyFilter(SimpleListFilter):
    title = 'Receiver currency'
    parameter_name = 'receiver_currency'

    def lookups(self, request, model_admin):
        return [
            ('RUB', 'Ruble'),
            ('USD', 'Dollar'),
            ('EUR', 'Euro'),
            ('CNY', 'Yuan'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(receiver_account__currency=self.value())
        return queryset


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    actions = ["mark_failed"]
    date_hierarchy = "created_at"
    fields = (
        "type_id",
        "status",
        "description",
        "amount",
        "sender_account",
        "receiver_account",
        "created_at"
    )
    list_display = (
        "transaction_id",
        "sender_account_number",
        "sender_currency",
        "receiver_account_number",
        "receiver_currency",
        "amount",
        "converted_amount",
        "status",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        self.message_user(
            request,
            "Transactions cannot be created or modified through the admin panel",
            level="error"
        )
        return

    def sender_currency(self, obj):
        return obj.sender_account.currency

    sender_currency.short_description = "Sender Currency"

    def receiver_currency(self, obj):
        return obj.receiver_account.currency

    receiver_currency.short_description = "Receiver Currency"

    def sender_account_number(self, obj):
        return obj.sender_account.account_number

    sender_account_number.short_description = "Sender account"

    def receiver_account_number(self, obj):
        return obj.receiver_account.account_number

    receiver_account_number.short_description = "Receiver account"

    list_filter = ("status", SenderCurrencyFilter, ReceiverCurrencyFilter)
    search_fields = (
        "transaction_id",
        "sender_account__account_number",
        "receiver_account__account_number",
        "sender_account__owner__first_name",
        "sender_account__owner__last_name",
        "sender_account__owner__phone",
        "receiver_account__owner__first_name",
        "receiver_account__owner__last_name",
        "receiver_account__owner__phone",
        "description",
    )
    ordering = ("transaction_id",)
    autocomplete_fields = ("sender_account", "receiver_account", "type_id")
    readonly_fields = [field.name for field in Transaction._meta.fields] + ['created_at']


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "type_id")
    search_fields = ("name",)
