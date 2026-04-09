"""
DashboardAdminSite — Vuexy-themed AdminSite subclass.

Activated automatically via VuexyAdminConfig.ready(), which swaps
admin.site.__class__.  No changes to urls.py are needed.

Configuration (all optional) in settings.py:

    VUEXY_ADMIN = {
        # Controls sidebar app/model ordering, icons, and display names.
        # See DEFAULT_SIDEBAR_CONFIG below for the shape.
        "SIDEBAR_CONFIG": { ... },

        # Dotted path to a callable that receives (request) and returns a
        # dict that gets merged into the admin index context.
        # Use this to inject KPI stats, chart configs, etc.
        # Example: "myapp.admin_context.get_dashboard_context"
        "DASHBOARD_CONTEXT_CALLBACK": None,
    }
"""

from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


# Sensible defaults — covers the built-in auth app.
# Projects extend or replace this via settings.VUEXY_ADMIN["SIDEBAR_CONFIG"].
DEFAULT_SIDEBAR_CONFIG = {
    "app_order": ["auth"],
    "apps": {
        "auth": {
            "name": _("Users & Authentication"),
            "models": {
                "User":  {"icon": "ti-users", "order": 1},
                "Group": {"icon": "ti-lock",  "order": 2},
            },
        },
    },
}


class DashboardAdminSite(AdminSite):
    """AdminSite subclass powering the Vuexy admin dashboard."""

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _vuexy_settings(self):
        from django.conf import settings
        return getattr(settings, "VUEXY_ADMIN", {})

    def _sidebar_config(self):
        return self._vuexy_settings().get("SIDEBAR_CONFIG", DEFAULT_SIDEBAR_CONFIG)

    # ------------------------------------------------------------------ #
    # Sidebar: icon injection, ordering, name overrides                   #
    # ------------------------------------------------------------------ #

    def get_app_list(self, request, app_label=None):
        """
        Annotate every model dict with ``icon`` and ``order`` from
        SIDEBAR_CONFIG, sort models within each app, then sort apps.
        The sidebar template reads ``model.icon`` directly — no template
        logic needed when you add a new model.
        """
        app_list = super().get_app_list(request, app_label)

        config    = self._sidebar_config()
        apps_cfg  = config.get("apps", {})
        app_order = config.get("app_order", [])

        for app in app_list:
            label   = app["app_label"]
            app_cfg = apps_cfg.get(label, {})

            # Optional app display-name override
            if "name" in app_cfg:
                app["name"] = app_cfg["name"]

            # Annotate and sort models
            model_cfg = app_cfg.get("models", {})
            for model in app["models"]:
                obj  = model["object_name"]
                mcfg = model_cfg.get(obj, {})
                model["icon"]  = mcfg.get("icon",  "ti-circle")
                model["order"] = mcfg.get("order", 999)
                if "name" in mcfg:
                    model["name"] = mcfg["name"]

            app["models"].sort(key=lambda m: m["order"])

        # Sort apps; apps not listed in app_order are appended at the end
        if app_order:
            app_list.sort(
                key=lambda a: (
                    app_order.index(a["app_label"])
                    if a["app_label"] in app_order
                    else len(app_order)
                )
            )

        return app_list

    # ------------------------------------------------------------------ #
    # Dashboard index: optional project-defined context injection         #
    # ------------------------------------------------------------------ #

    def index(self, request, extra_context=None):
        from django.utils.module_loading import import_string

        extra_context = extra_context or {}

        callback_path = self._vuexy_settings().get("DASHBOARD_CONTEXT_CALLBACK")
        if callback_path:
            callback = import_string(callback_path)
            extra_context.update(callback(request))

        return super().index(request, extra_context=extra_context)
