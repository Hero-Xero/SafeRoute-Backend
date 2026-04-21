from django.db import models
from django.utils.translation import gettext_lazy as _


class UserTypeChoices(models.TextChoices):
    ADMIN = 'ADMIN', _('Admin')
    DRIVER = 'DRIVER', _('Driver')
    GUARDIAN = 'GUARDIAN', _('Guardian')
    ASSISTANT = 'ASSISTANT', _('Assistant')


class GenderChoices(models.TextChoices):
    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')
