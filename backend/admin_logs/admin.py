from django.contrib import admin
from .models import AdminActionLog


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'model', 'object_repr', 'created_at')
    list_filter = ('action', 'model', 'created_at')
    search_fields = ('admin__username', 'model', 'object_repr')
    readonly_fields = ('admin', 'action', 'model', 'object_id', 'object_repr', 'created_at', 'details')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
