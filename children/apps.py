from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChildrenConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "children"
    verbose_name = _("Children")
