from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from users.enums import GenderChoices, UserTypeChoices
from users.managers import DriverManager, GuardianManager, AdminUserManager, AssistantManager


class User(AbstractBaseUser, PermissionsMixin):
    type = models.CharField(
        max_length=32,
        choices=UserTypeChoices.choices,
        verbose_name=_("User Type"),
        db_index=True
    )
    profile_image = models.ImageField(upload_to='profile_images/', default='default_images/profile.png', validators=[
        FileExtensionValidator(allowed_extensions=[
            'jpg', 'jpeg', 'png', 'svg', 'gif']),
    ], blank=True, null=True, verbose_name=_('Profile Image'))
    first_name = models.CharField(
        _('First Name'), max_length=30, blank=True, null=True, db_index=True)
    second_name = models.CharField(
        _('Second Name'), max_length=30, blank=True, null=True, db_index=True)
    third_name = models.CharField(
        _('Third Name'), max_length=30, blank=True, null=True, db_index=True)
    last_name = models.CharField(
        _('Last Name'), max_length=30, blank=True, null=True, db_index=True)
    email = models.EmailField(
        _('Email address'), unique=True, db_index=True)
    phone_number = PhoneNumberField(
        _('Mobile Number'), db_index=True)
    secondary_phone = PhoneNumberField(
        _('Secondary Mobile Number'), blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    date_of_birth = models.DateField(
        blank=True, null=True, verbose_name=_("Date of Birth"))
    gender = models.CharField(max_length=20, blank=True, null=True,
                              choices=GenderChoices, verbose_name=_("Gender"))
    date_joined = models.DateTimeField(_('Date Joined'), auto_now_add=True)
    is_active = models.BooleanField(
        _('Active'), default=True, help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts'))
    is_staff = models.BooleanField(
        _('Staff status'), default=False, help_text=_('Designates whether the user can log into this admin site.'))
    is_verified = models.BooleanField(
        _('Verified'), default=False, help_text=_('Designates whether the user has verified their email address.'))
    is_deleted = models.BooleanField(
        _('Deleted'), default=False, help_text=_('Designates whether the user has deleted their account.'))

    objects = AdminUserManager()


class AdminUser(User):
    objects = AdminUserManager()

    class Meta:
        proxy = True
        verbose_name = _("Admin")
        verbose_name_plural = _("Admins")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = UserTypeChoices.ADMIN

        return super().save(*args, **kwargs)


class DriverUser(User):
    objects = DriverManager()

    class Meta:
        proxy = True
        permissions = [
            ("can_operate_as_driver", "Can operate as driver"),
        ]
        verbose_name = _('Driver User')
        verbose_name_plural = _('Driver Users')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = UserTypeChoices.DRIVER
        return super().save(*args, **kwargs)


class GuardianUser(User):
    objects = GuardianManager()

    class Meta:
        proxy = True
        permissions = [
            ("can_act_as_guardian", "Can act as guardian"),
        ]
        verbose_name = _('Guardian User')
        verbose_name_plural = _('Guardian Users')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = UserTypeChoices.GUARDIAN
        return super().save(*args, **kwargs)
    
class AssistantUser(User):
    objects = AssistantManager()

    class Meta:
        proxy = True
        permissions = [
            ("can_act_as_assistant", "Can act as assistant"),
        ]
        verbose_name = _('Assistant User')
        verbose_name_plural = _('Assistant Users')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.type = UserTypeChoices.ASSISTANT
        return super().save(*args, **kwargs)
