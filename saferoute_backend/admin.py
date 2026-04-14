from collections import OrderedDict
from time import timezone
from saferoute_backend.admin_site.configs import ADMIN_ORDERING

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.timezone import now, timedelta
from django.utils.translation import gettext_lazy as _
from users.permissions import IsAdmin
from users.models import User

# Get ordering configuration from settings
admin_ordering = ADMIN_ORDERING


class ProxyAwareAutocompleteView(AutocompleteJsonView):
    """Autocomplete view that falls back to registered proxy models.

    Django's default autocomplete view calls
    ``admin_site.get_model_admin(remote_model)`` which fails when only a
    *proxy* of ``remote_model`` is registered (e.g. ``CompanyRenterUser``
    is registered but ``User`` is not).  This subclass catches the
    ``NotRegistered`` exception and searches for a proxy that IS
    registered, avoiding a 403 error.
    """

    def process_request(self, request):
        from django.contrib.admin.exceptions import NotRegistered
        try:
            return super().process_request(request)
        except PermissionDenied:
            # Re-derive the remote model and check for registered proxies.
            term = request.GET.get("term", "")
            try:
                app_label = request.GET["app_label"]
                model_name = request.GET["model_name"]
                field_name = request.GET["field_name"]
            except KeyError:
                raise

            from django.apps import apps as django_apps
            from django.core.exceptions import FieldDoesNotExist
            try:
                source_model = django_apps.get_model(app_label, model_name)
                source_field = source_model._meta.get_field(field_name)
                remote_model = source_field.remote_field.model
            except (LookupError, FieldDoesNotExist, AttributeError):
                raise

            # If remote_model itself is registered, re-raise (the 403 was
            # caused by something else, like lack of permission).
            try:
                self.admin_site.get_model_admin(remote_model)
                raise  # was a real perm error
            except NotRegistered:
                pass

            # Collect all registered proxies of remote_model that have
            # search_fields configured.
            limit_choices_to = source_field.get_limit_choices_to()
            candidates = []
            for registered_model, ma in self.admin_site._registry.items():
                if (
                    registered_model is not remote_model
                    and issubclass(registered_model, remote_model)
                    and ma.get_search_fields(request)
                ):
                    candidates.append((registered_model, ma))

            # Prioritize candidates based on the referring page to ensure the right
            # proxy is selected when multiple proxies are valid (e.g. User →
            referer = request.META.get('HTTP_REFERER', '')
            forced_proxy = None

            # If a specific proxy was forced by the referer, use it directly
            # (skip queryset check — empty results are valid for a new type)
            if forced_proxy:
                remote_model, model_admin = forced_proxy
            else:
                # When limit_choices_to is set on the FK, pick the proxy whose
                # queryset is compatible (i.e. returns non-empty results after
                # applying limit_choices_to).
                model_admin = None
                for candidate_model, ma in candidates:
                    if limit_choices_to:
                        qs = ma.get_queryset(request)
                        if qs.complex_filter(limit_choices_to).exists():
                            model_admin = ma
                            remote_model = candidate_model
                            break
                    else:
                        model_admin = ma
                        remote_model = candidate_model
                        break

            if model_admin is None:
                raise  # no proxy found, re-raise PermissionDenied

            to_field_name = getattr(
                source_field.remote_field,
                "field_name",
                remote_model._meta.pk.attname,
            )
            to_field_name = remote_model._meta.get_field(
                to_field_name).attname
            if not model_admin.to_field_allowed(request, to_field_name):
                raise

            return term, model_admin, source_field, to_field_name


class SafeRouteAdminSite(admin.AdminSite):
    site_header = _("SafeRoute Admin")
    site_title = _("SafeRoute Admin Portal")
    index_title = _("Welcome to SafeRoute Admin Panel")

    def autocomplete_view(self, request):
        return ProxyAwareAutocompleteView.as_view(admin_site=self)(request)

    def index(self, request, extra_context=None):
        """
        Custom dashboard with rich live statistics grouped by domain.
        Defensive against missing tables (before migrations run).
        """
        if not request.user.is_superuser:
            return super().index(request, extra_context)

        from django.db import ProgrammingError, OperationalError
        from django.utils import timezone
        from datetime import date

        today = date.today()

        # ── Users ────────────────────────────────────────────────────────────
        try:
            from users.models import DriverUser, GuardianUser
            total_users = User.objects.count()
            total_drivers = DriverUser.objects.count()
            active_drivers = DriverUser.objects.filter(is_active=True).count()
            total_guardians = GuardianUser.objects.count()
            active_guardians = GuardianUser.objects.filter(
                is_active=True).count()
            inactive_users = User.objects.filter(is_active=False).count()
            unverified_users = User.objects.filter(
                is_verified=False, is_active=True).count()
        except (ProgrammingError, OperationalError):
            total_users = total_drivers = active_drivers = 0
            total_guardians = active_guardians = inactive_users = unverified_users = 0

        # ── Children ─────────────────────────────────────────────────────────
        try:
            from children.models import Child
            total_children = Child.objects.count()
            active_children = Child.objects.filter(is_active=True).count()
        except (ProgrammingError, OperationalError):
            total_children = active_children = 0

        # ── Trips & Routes ───────────────────────────────────────────────────
        try:
            from trips.models import Bus, Route, Trip
            from trips.enums import TripStatusChoices, BusStatusChoices
            total_routes = Route.objects.filter(is_active=True).count()
            total_buses = Bus.objects.count()
            active_buses = Bus.objects.filter(is_active=True).count()
            total_trips = Trip.objects.count()
            trips_today = Trip.objects.filter(scheduled_date=today).count()
            active_trips = Trip.objects.filter(
                status=TripStatusChoices.IN_PROGRESS).count()
            completed_trips = Trip.objects.filter(
                status=TripStatusChoices.COMPLETED).count()
            cancelled_trips = Trip.objects.filter(
                status=TripStatusChoices.CANCELLED).count()
        except (ProgrammingError, OperationalError):
            total_routes = total_buses = active_buses = 0
            total_trips = trips_today = active_trips = completed_trips = cancelled_trips = 0

        try:
            from trips.models import Bus
            from trips.enums import BusStatusChoices
            buses_on_trip = Bus.objects.filter(
                status=BusStatusChoices.ON_TRIP).count()
        except (ProgrammingError, OperationalError):
            buses_on_trip = 0

        # ── Notifications ────────────────────────────────────────────────────
        try:
            from notifications.models import Notification, BroadcastNotification, DeviceToken
            from notifications.enums import NotificationStatusChoices
            total_notifications = Notification.objects.count()
            unread_notifications = Notification.objects.filter(
                is_read=False).count()
            failed_notifications = Notification.objects.filter(
                status=NotificationStatusChoices.FAILED
            ).count()
            total_device_tokens = DeviceToken.objects.filter(
                is_active=True).count()
            total_broadcasts = BroadcastNotification.objects.count()
            pending_broadcasts = BroadcastNotification.objects.filter(
                is_sent=False).count()
        except (ProgrammingError, OperationalError):
            total_notifications = unread_notifications = failed_notifications = 0
            total_device_tokens = total_broadcasts = pending_broadcasts = 0

        context = {
            **self.each_context(request),
            "app_list": self.get_app_list(request),
            # Users
            "total_users": total_users,
            "total_drivers": total_drivers,
            "active_drivers": active_drivers,
            "total_guardians": total_guardians,
            "active_guardians": active_guardians,
            "inactive_users": inactive_users,
            "unverified_users": unverified_users,
            # Children
            "total_children": total_children,
            "active_children": active_children,
            # Trips & Routes
            "total_routes": total_routes,
            "total_buses": total_buses,
            "active_buses": active_buses,
            "buses_on_trip": buses_on_trip,
            "total_trips": total_trips,
            "trips_today": trips_today,
            "active_trips": active_trips,
            "completed_trips": completed_trips,
            "cancelled_trips": cancelled_trips,
            # Notifications
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "failed_notifications": failed_notifications,
            "total_device_tokens": total_device_tokens,
            "total_broadcasts": total_broadcasts,
            "pending_broadcasts": pending_broadcasts,
        }
        return TemplateResponse(request, "admin/index.html", context)

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps or a specific app,
        integrating labels, ordering, and icons from SIDEBAR_CONFIG.
        """
        app_dict = self._build_app_dict(request, app_label)
        sidebar_config = getattr(settings, "SIDEBAR_CONFIG", {})
        config_apps = sidebar_config.get("apps", {})
        app_order = sidebar_config.get("app_order", [])

        # ── APP_LABEL CASE (Single app view) ───────────────────────────
        if app_label:
            if app_label in app_dict:
                app_data = app_dict[app_label]
                app_cfg = config_apps.get(app_label, {})
                
                # Apply custom app name
                if "name" in app_cfg:
                    app_data["name"] = app_cfg["name"]
                
                # Apply model icons and ordering
                model_cfgs = app_cfg.get("models", {})
                ordered_models = []
                model_dict = {m["object_name"]: m for m in app_data["models"]}

                # Order based on 'order' key in model config
                sorted_model_names = sorted(
                    model_cfgs.keys(), 
                    key=lambda k: model_cfgs[k].get("order", 999)
                )

                for m_name in sorted_model_names:
                    if m_name in model_dict:
                        model_data = model_dict[m_name]
                        model_data["icon"] = model_cfgs[m_name].get("icon", "ti-circle")
                        ordered_models.append(model_data)

                # Add remaining models not in config
                for m_name, m_data in model_dict.items():
                    if m_name not in model_cfgs:
                        m_data["icon"] = "ti-circle"
                        ordered_models.append(m_data)

                app_data["models"] = ordered_models
                return [app_data]
            return []

        # ── FULL LIST CASE ─────────────────────────────────────────────
        ordered_apps = []

        # 1. Apps specified in app_order
        for label in app_order:
            if label in app_dict:
                app_data = app_dict.pop(label)
                app_cfg = config_apps.get(label, {})

                if "name" in app_cfg:
                    app_data["name"] = app_cfg["name"]
                
                # App-level icon if needed (some themes support app icons)
                app_data["icon"] = app_cfg.get("icon", "ti-folder")

                # Process models for this app
                model_cfgs = app_cfg.get("models", {})
                ordered_models = []
                model_dict = {m["object_name"]: m for m in app_data["models"]}

                # Order models by config 'order'
                sorted_model_names = sorted(
                    model_cfgs.keys(), 
                    key=lambda k: model_cfgs[k].get("order", 999)
                )

                for m_name in sorted_model_names:
                    if m_name in model_dict:
                        model_data = model_dict[m_name]
                        model_data["icon"] = model_cfgs[m_name].get("icon", "ti-circle")
                        ordered_models.append(model_data)

                # Add extra models
                for m_name, m_data in model_dict.items():
                    if m_name not in model_cfgs:
                        m_data["icon"] = "ti-circle"
                        ordered_models.append(m_data)

                app_data["models"] = ordered_models
                ordered_apps.append(app_data)

        # 2. Add remaining apps not in app_order
        for label, app_data in sorted(app_dict.items()):
            for m_data in app_data["models"]:
                m_data["icon"] = "ti-circle"
            ordered_apps.append(app_data)

        return ordered_apps

    def has_permission(self, request):
        """
        Only allow access to active admins
        """
        return IsAdmin().has_permission(request, None)

    def get_urls(self):
        urls = super().get_urls()
        return urls


saferoute_admin_site = SafeRouteAdminSite(name='admin')
