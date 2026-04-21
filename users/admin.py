import random
import string

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from saferoute_backend.admin import saferoute_admin_site
from users.enums import UserTypeChoices
from users.models import AdminUser, DriverUser, GuardianUser, AssistantUser
from users.forms.admins import AdminUserChangeForm, AdminUserCreationForm


# ─── Resources ──────────────────────────────────────────────────────────────────

class DriverUserResource(resources.ModelResource):
    class Meta:
        model = DriverUser
        fields = (
            'id', 'email', 'first_name', 'second_name', 'third_name', 'last_name',
            'phone_number', 'gender', 'date_of_birth', 'is_active', 'is_verified',
            'is_deleted', 'date_joined',
        )
        export_order = fields


class GuardianUserResource(resources.ModelResource):
    class Meta:
        model = GuardianUser
        fields = (
            'id', 'email', 'first_name', 'second_name', 'third_name', 'last_name',
            'phone_number', 'gender', 'date_of_birth', 'is_active', 'is_verified',
            'is_deleted', 'date_joined',
        )
        export_order = fields


class AssistantUserResource(resources.ModelResource):
    class Meta:
        model = AssistantUser
        fields = (
            'id', 'email', 'first_name', 'second_name', 'third_name', 'last_name',
            'phone_number', 'gender', 'date_of_birth', 'is_active', 'is_verified',
            'is_deleted', 'date_joined',
        )
        export_order = fields


# ─── Admin Classes ───────────────────────────────────────────────────────────────

class AdminUserAdmin(UserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display = ('email', 'get_full_name', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('is_superuser', 'is_staff', 'is_active')
    search_fields = ('phone_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    readonly_fields = ['date_joined']

    fieldsets = (
        (_("Personal Info"), {
            "fields": ("first_name", "last_name", "phone_number", "email"),
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_superuser", "is_staff", "groups", "user_permissions"),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined",),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'password1', 'password2', 'is_superuser', 'is_staff', 'is_active'
            ),
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or obj.email
    get_full_name.short_description = _('Full Name')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=UserTypeChoices.ADMIN)


class DriverUserAdmin(ImportExportModelAdmin):
    resource_classes = [DriverUserResource]

    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined',)

    fieldsets = (
        (_("Personal Info"), {
            "fields": (
                "first_name", "second_name", "third_name", "last_name",
                "email", "phone_number", "profile_image", "gender", "date_of_birth"
            ),
        }),
        (_("Account Status"), {
            "fields": ("is_active", "is_verified", "is_deleted"),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            type=UserTypeChoices.DRIVER, is_superuser=False, is_staff=False
        )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.type = UserTypeChoices.DRIVER
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(8))
            obj.set_password(password)

            super().save_model(request, obj, form, change)

            subject = str(_("Your Driver Account Credentials"))
            html_message = render_to_string('users/emails/sign_in.html', {
                'first_name': obj.first_name,
                'email': obj.email,
                'password': password,
            })
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saferoute.com')
            send_mail(
                subject,
                '',
                from_email,
                [obj.email],
                html_message=html_message,
                fail_silently=False,
            )
        else:
            super().save_model(request, obj, form, change)


class GuardianUserAdmin(ImportExportModelAdmin):
    resource_classes = [GuardianUserResource]

    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined',)

    fieldsets = (
        (_("Personal Info"), {
            "fields": (
                "first_name", "second_name", "third_name", "last_name",
                "email", "phone_number", "profile_image", "gender", "date_of_birth"
            ),
        }),
        (_("Account Status"), {
            "fields": ("is_active", "is_verified", "is_deleted"),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            type=UserTypeChoices.GUARDIAN, is_superuser=False, is_staff=False
        )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.type = UserTypeChoices.GUARDIAN
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(8))
            obj.set_password(password)

            super().save_model(request, obj, form, change)

            subject = str(_("Your Guardian Account Credentials"))
            html_message = render_to_string('users/emails/sign_in.html', {
                'first_name': obj.first_name,
                'email': obj.email,
                'password': password,
            })
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saferoute.com')
            send_mail(
                subject,
                '',
                from_email,
                [obj.email],
                html_message=html_message,
                fail_silently=False,
            )
        else:
            super().save_model(request, obj, form, change)


class AssistantUserAdmin(ImportExportModelAdmin):
    resource_classes = [AssistantUserResource]

    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined',)

    fieldsets = (
        (_("Personal Info"), {
            "fields": (
                "first_name", "second_name", "third_name", "last_name",
                "email", "phone_number", "profile_image", "gender", "date_of_birth"
            ),
        }),
        (_("Account Status"), {
            "fields": ("is_active", "is_verified", "is_deleted"),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            type=UserTypeChoices.ASSISTANT, is_superuser=False, is_staff=False
        )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.type = UserTypeChoices.ASSISTANT
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(8))
            obj.set_password(password)

            super().save_model(request, obj, form, change)

            subject = str(_("Your Assistant Account Credentials"))
            html_message = render_to_string('users/emails/sign_in.html', {
                'first_name': obj.first_name,
                'email': obj.email,
                'password': password,
            })
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saferoute.com')
            send_mail(
                subject,
                '',
                from_email,
                [obj.email],
                html_message=html_message,
                fail_silently=False,
            )
        else:
            super().save_model(request, obj, form, change)


saferoute_admin_site.register(DriverUser, DriverUserAdmin)
saferoute_admin_site.register(GuardianUser, GuardianUserAdmin)
saferoute_admin_site.register(AssistantUser, AssistantUserAdmin)
saferoute_admin_site.register(AdminUser, AdminUserAdmin)
