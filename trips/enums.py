from django.db import models
from django.utils.translation import gettext_lazy as _


class TripStatusChoices(models.TextChoices):
    SCHEDULED = 'SCHEDULED', _('Scheduled')
    IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
    COMPLETED = 'COMPLETED', _('Completed')
    CANCELLED = 'CANCELLED', _('Cancelled')


class TripTypeChoices(models.TextChoices):
    PICKUP = 'PICKUP', _('Pickup (To School)')
    DROPOFF = 'DROPOFF', _('Drop-off (From School)')


class DayOfWeekChoices(models.TextChoices):
    SUNDAY = 'SUNDAY', _('Sunday')
    MONDAY = 'MONDAY', _('Monday')
    TUESDAY = 'TUESDAY', _('Tuesday')
    WEDNESDAY = 'WEDNESDAY', _('Wednesday')
    THURSDAY = 'THURSDAY', _('Thursday')
    FRIDAY = 'FRIDAY', _('Friday')
    SATURDAY = 'SATURDAY', _('Saturday')


class TripChildStatusChoices(models.TextChoices):
    WAITING = 'WAITING', _('Waiting')
    PICKED_UP = 'PICKED_UP', _('Picked Up')
    DROPPED_OFF = 'DROPPED_OFF', _('Dropped Off')
    ABSENT = 'ABSENT', _('Absent')


class BusStatusChoices(models.TextChoices):
    AVAILABLE = 'AVAILABLE', _('Available')
    ON_TRIP = 'ON_TRIP', _('On Trip')
    MAINTENANCE = 'MAINTENANCE', _('Under Maintenance')
    OUT_OF_SERVICE = 'OUT_OF_SERVICE', _('Out of Service')
