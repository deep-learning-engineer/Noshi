from django.contrib import admin

# Set admin titles (optional, for branding)
admin.site.site_header = "Noshi Admin"
admin.site.site_title = "Noshi Admin"
admin.site.index_title = "Welcome to Noshi Admin"

# Inject custom CSS for all ModelAdmins
for model, model_admin in admin.site._registry.items():
    if not hasattr(model_admin, 'Media'):
        class Media:
            css = {'all': ('admin/css/custom_admin.css',)}
        model_admin.Media = Media 
