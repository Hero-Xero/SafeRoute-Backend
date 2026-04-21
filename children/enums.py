from django.db import models
from django.utils.translation import gettext_lazy as _


class GradeChoices(models.TextChoices):
    KG1 = 'KG1', _('KG 1')
    KG2 = 'KG2', _('KG 2')
    GRADE_1 = 'GRADE_1', _('Grade 1')
    GRADE_2 = 'GRADE_2', _('Grade 2')
    GRADE_3 = 'GRADE_3', _('Grade 3')
    GRADE_4 = 'GRADE_4', _('Grade 4')
    GRADE_5 = 'GRADE_5', _('Grade 5')
    GRADE_6 = 'GRADE_6', _('Grade 6')
    GRADE_7 = 'GRADE_7', _('Grade 7')
    GRADE_8 = 'GRADE_8', _('Grade 8')
    GRADE_9 = 'GRADE_9', _('Grade 9')
    GRADE_10 = 'GRADE_10', _('Grade 10')
    GRADE_11 = 'GRADE_11', _('Grade 11')
    GRADE_12 = 'GRADE_12', _('Grade 12')


class ChildGenderChoices(models.TextChoices):
    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')


class LocationChangeStatus(models.TextChoices):
    PENDING_REVIEW = 'pending_review', _('Pending Review')
    ACCEPTED = 'accepted', _('Accepted')
    REJECTED = 'rejected', _('Rejected')
    FULFILLED = 'fulfilled', _('Fulfilled')
    CANCELLED = 'cancelled', _('Cancelled')


class LocationChangeType(models.TextChoices):
    PICKUP = 'pickup', _('Pickup')
    DROPOFF = 'dropoff', _('Drop-off')
    BOTH = 'both', _('Both')
