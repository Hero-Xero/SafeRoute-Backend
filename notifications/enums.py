from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationTypeChoices(models.TextChoices):
    TRIP_STARTED = 'TRIP_STARTED', _('Trip Started')
    TRIP_COMPLETED = 'TRIP_COMPLETED', _('Trip Completed')
    TRIP_CANCELLED = 'TRIP_CANCELLED', _('Trip Cancelled')
    CHILD_PICKED_UP = 'CHILD_PICKED_UP', _('Child Picked Up')
    CHILD_DROPPED_OFF = 'CHILD_DROPPED_OFF', _('Child Dropped Off')
    CHILD_ABSENT = 'CHILD_ABSENT', _('Child Marked Absent')
    BUS_APPROACHING = 'BUS_APPROACHING', _('Bus Approaching Your Stop')
    BUS_DELAYED = 'BUS_DELAYED', _('Bus Delayed')
    GENERAL = 'GENERAL', _('General')
    SYSTEM = 'SYSTEM', _('System')
    SUBSCRIPTION_EXPIRING = 'SUBSCRIPTION_EXPIRING', _('Subscription Expiring')
    SUBSCRIPTION_EXPIRED = 'SUBSCRIPTION_EXPIRED', _('Subscription Expired')


class NotificationStatusChoices(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    SENT = 'SENT', _('Sent')
    FAILED = 'FAILED', _('Failed')
    READ = 'READ', _('Read')


class NotificationChannelChoices(models.TextChoices):
    PUSH = 'PUSH', _('Push Notification')
    IN_APP = 'IN_APP', _('In-App')
    EMAIL = 'EMAIL', _('Email')
    SMS = 'SMS', _('SMS')


class DeviceTypeChoices(models.TextChoices):
    ANDROID = 'ANDROID', _('Android')
    IOS = 'IOS', _('iOS')
    WEB = 'WEB', _('Web')
