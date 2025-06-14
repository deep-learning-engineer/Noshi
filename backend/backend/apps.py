from django.apps import AppConfig
from django.contrib import admin


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend"
    verbose_name = "Backend"

    def ready(self):
        admin.site.site_header = "Mobile bank – administration"
        admin.site.site_title = "Mobile bank"
        admin.site.index_title = "Control Panel"
