from django.db import models
from users.models import User


class AdminActionLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('freeze', 'Freeze'),
        ('unfreeze', 'Unfreeze'),
        ('close', 'Close'),
        ('block', 'Block'),
        ('unblock', 'Unblock'),
        ('run_today', 'Run Today'),
    ]

    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Admins")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Action")
    model = models.CharField(max_length=255, verbose_name="Model")
    object_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Object ID")
    object_repr = models.CharField(max_length=255, blank=True, verbose_name="Object")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Valid date")
    details = models.JSONField(default=dict, blank=True, verbose_name="Details")

    class Meta:
        verbose_name = "administrator_logs"
        verbose_name_plural = "Administrator Action Logs"
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.admin} - {self.get_action_display()} - {self.model}"
