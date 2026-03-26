import random
import string
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import GroupAdmin, UserAdmin

from saferoute_backend.admin import saferoute_admin_site
from users.enums import UserTypeChoices
from users.models import DriverUser, GuardianUser
from users.forms.admins import AdminUserChangeForm, AdminUserCreationForm


class AdminUserAdmin(UserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display = ('email', 'full_name', 'is_superuser',
                    'is_staff', 'is_active')
    list_filter = ('is_superuser', 'is_staff', 'is_active')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (_("Personal Info"), {
            "fields": ("first_name", "last_name", "phone_number", 'email'),
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_superuser", "is_staff", "groups", "user_permissions"),
        }),
        (_("Important Dates"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'phone_number',
                       'password1', 'password2', 'is_superuser', 'is_staff', 'is_active'),
        }),
    )

    def change_password_action(self, obj):
        """
        Custom action to change the password of the user."""
        url = reverse(
            "admin:auth_user_password_change",
            args=[obj.pk],
        )
        return format_html(
            '<a class="button" href="{}">{}</a>',
            url,
            _("Change Password"),
        )

    change_password_action.short_description = _("Password")
    change_password_action.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=UserTypeChoices.ADMIN)


class DriverUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name',
                    'last_name', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined', )

    fieldsets = (
        (_("Personal Info"), {
            "fields": ("first_name", "second_name", "third_name", "last_name", "email", "phone_number", "profile_image", "gender", "date_of_birth"),
        }),
        (_("Account Status"), {
            "fields": ("is_active", "is_verified", "is_deleted"),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=UserTypeChoices.DRIVER, is_superuser=False, is_staff=False)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Generate a 8 character password
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(8))
            obj.set_password(password)

            # Save the object to ensure it has an ID
            super().save_model(request, obj, form, change)

            subject = str(_("Your Driver Account Credentials"))
            html_message = render_to_string('users/emails/sign_in.html', {
                'first_name': obj.first_name,
                'email': obj.email,
                'password': password,
            })
            from_email = getattr(
                settings, 'DEFAULT_FROM_EMAIL', 'noreply@saferoute.com')
            send_mail(
                subject,
                '',
                from_email,
                [obj.email],
                html_message=html_message,
                fail_silently=False
            )
        else:
            super().save_model(request, obj, form, change)


class GuardianUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name',
                    'last_name', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined', )

    fieldsets = (
        (_("Personal Info"), {
            "fields": ("first_name", "second_name", "third_name", "last_name", "email", "phone_number", "profile_image", "gender", "date_of_birth"),
        }),
        (_("Account Status"), {
            "fields": ("is_active", "is_verified", "is_deleted"),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type=UserTypeChoices.GUARDIAN, is_superuser=False, is_staff=False)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Generate a 8 character password
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(8))
            obj.set_password(password)

            # Save the object to ensure it has an ID
            super().save_model(request, obj, form, change)

            subject = str(_("Your Guardian Account Credentials"))
            html_message = render_to_string('users/emails/sign_in.html', {
                'first_name': obj.first_name,
                'email': obj.email,
                'password': password,
            })
            from_email = getattr(
                settings, 'DEFAULT_FROM_EMAIL', 'noreply@saferoute.com')
            send_mail(
                subject,
                '',
                from_email,
                [obj.email],
                html_message=html_message,
                fail_silently=False
            )
        else:
            super().save_model(request, obj, form, change)


saferoute_admin_site.register(DriverUser, DriverUserAdmin)
saferoute_admin_site.register(GuardianUser, GuardianUserAdmin)
