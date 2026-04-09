from django.apps import AppConfig


class VuexyAdminConfig(AppConfig):
    name = "vuexy_admin"
    verbose_name = "Vuexy Admin"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django.contrib import admin
        from vuexy_admin.site import DashboardAdminSite

        admin.site.__class__ = DashboardAdminSite
