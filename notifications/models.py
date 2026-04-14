from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from notifications.enums import (
    NotificationTypeChoices,
    NotificationStatusChoices,
    NotificationChannelChoices,
    DeviceTypeChoices,
)


class DeviceToken(models.Model):
    """Stores FCM/APNs push notification tokens for user devices."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name=_('User')
    )
    token = models.TextField(_('Device Token'), unique=True)
    device_type = models.CharField(
        _('Device Type'), max_length=20,
        choices=DeviceTypeChoices.choices,
        blank=True, null=True
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Device Token')
        verbose_name_plural = _('Device Tokens')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.get_device_type_display() if self.device_type else 'Unknown'}"


class NotificationTemplate(models.Model):
    """Reusable notification templates for common events."""
    type = models.CharField(
        _('Notification Type'), max_length=50,
        choices=NotificationTypeChoices.choices,
        unique=True
    )
    title_en = models.CharField(_('Title (English)'), max_length=255)
    title_ar = models.CharField(_('Title (Arabic)'), max_length=255, blank=True, null=True)
    body_en = models.TextField(_('Body (English)'))
    body_ar = models.TextField(_('Body (Arabic)'), blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')

    def __str__(self):
        return f"{self.get_type_display()} Template"


class Notification(models.Model):
    """A notification sent or to be sent to a specific user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Recipient')
    )
    type = models.CharField(
        _('Notification Type'), max_length=50,
        choices=NotificationTypeChoices.choices,
        default=NotificationTypeChoices.GENERAL
    )
    channel = models.CharField(
        _('Channel'), max_length=20,
        choices=NotificationChannelChoices.choices,
        default=NotificationChannelChoices.IN_APP
    )
    status = models.CharField(
        _('Status'), max_length=20,
        choices=NotificationStatusChoices.choices,
        default=NotificationStatusChoices.PENDING
    )
    title = models.CharField(_('Title'), max_length=255)
    body = models.TextField(_('Body'))
    data = models.JSONField(
        _('Extra Data'), default=dict, blank=True,
        help_text=_('Additional JSON payload (e.g. trip_id, child_id, etc.)')
    )
    is_read = models.BooleanField(_('Read'), default=False)
    read_at = models.DateTimeField(_('Read At'), blank=True, null=True)
    sent_at = models.DateTimeField(_('Sent At'), blank=True, null=True)
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
        verbose_name=_('Related Trip')
    )
    child = models.ForeignKey(
        'children.Child',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
        verbose_name=_('Related Child')
    )
    error_message = models.TextField(
        _('Error Message'), blank=True, null=True,
        help_text=_('Populated if sending failed')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"[{self.get_type_display()}] → {self.user} | {self.get_status_display()}"


class BroadcastNotification(models.Model):
    """Admin-initiated broadcast notification to all or filtered users."""
    title = models.CharField(_('Title'), max_length=255)
    body = models.TextField(_('Body'))
    type = models.CharField(
        _('Notification Type'), max_length=50,
        choices=NotificationTypeChoices.choices,
        default=NotificationTypeChoices.GENERAL
    )
    target_all = models.BooleanField(_('Send to All Users'), default=True)
    target_guardians = models.BooleanField(_('Send to Guardians'), default=False)
    target_drivers = models.BooleanField(_('Send to Drivers'), default=False)
    is_sent = models.BooleanField(_('Sent'), default=False)
    sent_at = models.DateTimeField(_('Sent At'), blank=True, null=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_broadcasts',
        verbose_name=_('Sent By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Broadcast Notification')
        verbose_name_plural = _('Broadcast Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} | {'Sent' if self.is_sent else 'Pending'}"
