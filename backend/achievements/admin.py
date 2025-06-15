from django.contrib import admin
from .models import Achievement, UserAchievement


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "condition")
    search_fields = ("name", "condition")
    inlines = (UserAchievementInline,)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "created_at")
    list_filter = ("achievement", "created_at")
    search_fields = ("user__email", "achievement__name")
    autocomplete_fields = ("user", "achievement")
