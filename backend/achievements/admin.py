from django.contrib import admin

from .models import Achievement, UserAchievement
from admin_logs.mixins import LoggingMixin


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Achievement)
class AchievementAdmin(LoggingMixin, admin.ModelAdmin):
    list_display = ("name", "condition")
    search_fields = ("name", "condition")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserAchievement)
class UserAchievementAdmin(LoggingMixin, admin.ModelAdmin):
    list_display = ("user", "achievement", "created_at")
    list_filter = ("achievement", "created_at")
    search_fields = ("user__email", "achievement__name")
    autocomplete_fields = ("user", "achievement")
