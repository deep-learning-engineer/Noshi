# admin_logs/mixins.py
from admin_logs.models import AdminActionLog


class LoggingMixin:
    def log_action(self, request, obj, action, details=None):
        if not request.user.is_authenticated or not obj.pk:
            return

        try:
            AdminActionLog.objects.create(
                admin=request.user,
                action=action,
                model=obj.__class__.__name__,
                object_id=str(obj.pk),
                object_repr=str(obj),
                details=details or {}
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log admin action: {e}")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = 'update' if change else 'create'
        self.log_action(request, obj, action)
