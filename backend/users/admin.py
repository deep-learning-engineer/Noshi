from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from bank_accounts.models import UserBankAccount
from achievements.models import UserAchievement
from django.contrib.auth.models import Group
from admin_logs.mixins import LoggingMixin


admin.site.unregister(Group)


class UserBankAccountInline(admin.TabularInline):
    model = UserBankAccount
    extra = 0
    verbose_name = "Bank account"
    verbose_name_plural = "Bank accounts"
    autocomplete_fields = ("bank_account",)


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0
    verbose_name = "Achievement"
    verbose_name_plural = "Achievements"
    autocomplete_fields = ("achievement",)


@admin.register(User)
class UserAdmin(LoggingMixin, BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal data", {"fields": ("first_name", "last_name", "phone")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "phone", "password1", "password2"),
        }),
    )
    list_display = ("email", "first_name", "last_name", "is_active", "phone", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")
    inlines = (UserBankAccountInline, UserAchievementInline)

    actions = ["disable_users", "enable_users"]

    @admin.action(description="Block accounts")
    def disable_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Blocked: {updated} accounts")
        for user in queryset:
            self.log_action(request, user, action="block", details={"user_id": user.pk})

    @admin.action(description="Unblock accounts")
    def enable_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Unblocked: {updated} accounts")
        for user in queryset:
            self.log_action(request, user, action="unblock", details={"user_id": user.pk})

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
