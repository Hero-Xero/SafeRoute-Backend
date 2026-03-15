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
        Replace the default dashboard (with recent actions)
        with custom statistics. Support date range filtering.
        """
        if not request.user.is_superuser:
            return super().index(request, extra_context)

        context = {
            **self.each_context(request),
            "app_list": self.get_app_list(request),  # still show apps list
        }
        return TemplateResponse(request, "admin/index.html", context)

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps or a specific app if app_label is provided.
        """
        app_dict = self._build_app_dict(request, app_label)

        # If a specific app is requested
        if app_label:
            # Find the app config in our ordering
            app_config = next(
                (a for a in admin_ordering if a['app'] == app_label), None)

            if app_config and app_label in app_dict:
                app_data = app_dict[app_label]

                # Apply custom label if specified
                if 'label' in app_config:
                    app_data['name'] = app_config['label']

                # Order models according to our config
                ordered_models = []
                model_dict = {m['object_name']: m for m in app_data['models']}

                for model_name in app_config.get('models', []):
                    if model_name in model_dict:
                        ordered_models.append(model_dict[model_name])

                # Add remaining models not in our ordering config
                remaining_models = [
                    m for m in app_data['models']
                    if m['object_name'] not in app_config.get('models', [])
                ]

                app_data['models'] = ordered_models + remaining_models
                return [app_data]

            return [app_dict[app_label]] if app_label in app_dict else []

        # Full apps list case (no app_label specified)
        ordered_apps = []

        for app_config in admin_ordering:
            app_label = app_config['app']

            if app_label in app_dict:
                app_data = app_dict[app_label]

                if 'label' in app_config:
                    app_data['name'] = app_config['label']

                # Order models
                ordered_models = []
                model_dict = {m['object_name']: m for m in app_data['models']}

                for model_name in app_config.get('models', []):
                    if model_name in model_dict:
                        ordered_models.append(model_dict[model_name])

                remaining_models = [
                    m for m in app_data['models']
                    if m['object_name'] not in app_config.get('models', [])
                ]

                app_data['models'] = ordered_models + remaining_models
                ordered_apps.append(app_data)

        # Add remaining apps not in our ordering config
        remaining_apps = [
            app_data for label, app_data in app_dict.items()
            if label not in [a['app'] for a in admin_ordering]
        ]

        return ordered_apps + remaining_apps

    def has_permission(self, request):
        """
        Only allow access to active admins
        """
        return IsAdmin().has_permission(request, None)

    def get_urls(self):
        urls = super().get_urls()
        return urls


saferoute_admin_site = SafeRouteAdminSite(name='admin')
