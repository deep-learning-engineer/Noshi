from django.contrib import admin
from .models import BankAccount, UserBankAccount


class UserBankAccountInline(admin.TabularInline):
    model = UserBankAccount
    extra = 1
    autocomplete_fields = ("user",)
    verbose_name = "Owner"
    verbose_name_plural = "Co-owners"


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "account_number",
        "owner",
        "balance",
        "currency",
        "payment_system",
        "status",
    )
    list_filter = ("currency", "payment_system", "status")
    search_fields = ("account_number", "owner__email", "owner__first_name", "owner__last_name")
    autocomplete_fields = ("owner",)
    readonly_fields = ("currency", "payment_system", "balance", "account_number", "owner")
    inlines = (UserBankAccountInline,)

    actions = ["freeze_accounts", "unfreeze_accounts", "close_accounts"]

    @admin.action(description="Froze selected accounts")
    def freeze_accounts(self, request, queryset):
        updated = queryset.update(status="frozen")
        self.message_user(request, f"Frozen accounts: {updated}")

    @admin.action(description="Unfroze selected accounts")
    def unfreeze_accounts(self, request, queryset):
        updated = queryset.filter(status="frozen").update(status="active")
        self.message_user(request, f"Unfrozen accounts: {updated}")

    @admin.action(description="Close selected accounts")
    def close_accounts(self, request, queryset):
        updated, errors = 0, 0
        for acc in queryset:
            try:
                acc.close_account()
                updated += 1
            except ValueError:
                errors += 1
        if updated:
            self.message_user(request, f"Closed accounts: {updated}")
        if errors:
            self.message_user(
                request,
                f"Failed to close {errors} accounts (balance is not 0)",
                level="warning"
            )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "bank_account")
    search_fields = ("user__email", "bank_account__account_number")
    autocomplete_fields = ("user", "bank_account")
