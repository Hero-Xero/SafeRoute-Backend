from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import DriverUser
from children.models import Child
from trips.enums import (
    TripStatusChoices, TripTypeChoices,
    TripChildStatusChoices, BusStatusChoices,
)


class Bus(models.Model):
    """Represents a physical school bus."""
    plate_number = models.CharField(_('Plate Number'), max_length=20, unique=True)
    model = models.CharField(_('Bus Model'), max_length=100, blank=True, null=True)
    capacity = models.PositiveIntegerField(
        _('Capacity'), default=0,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    driver = models.ForeignKey(
        DriverUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='buses',
        verbose_name=_('Driver')
    )
    status = models.CharField(
        _('Bus Status'), max_length=20,
        choices=BusStatusChoices.choices,
        default=BusStatusChoices.AVAILABLE
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Bus')
        verbose_name_plural = _('Buses')
        ordering = ['plate_number']

    def __str__(self):
        return self.plate_number


class Route(models.Model):
    """A named route (e.g., 'Morning Route - Zone A')."""
    name = models.CharField(_('Route Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True, null=True)
    school_name = models.CharField(_('School Name'), max_length=200, blank=True, null=True)
    school_latitude = models.DecimalField(
        _('School Latitude'), max_digits=10, decimal_places=7, blank=True, null=True
    )
    school_longitude = models.DecimalField(
        _('School Longitude'), max_digits=10, decimal_places=7, blank=True, null=True
    )
    bus = models.ForeignKey(
        Bus,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='routes',
        verbose_name=_('Assigned Bus')
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Route')
        verbose_name_plural = _('Routes')
        ordering = ['name']

    def __str__(self):
        return self.name


class RouteStop(models.Model):
    """An ordered stop on a route where children are picked up/dropped off."""
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='stops',
        verbose_name=_('Route')
    )
    name = models.CharField(_('Stop Name'), max_length=200)
    latitude = models.DecimalField(_('Latitude'), max_digits=10, decimal_places=7)
    longitude = models.DecimalField(_('Longitude'), max_digits=10, decimal_places=7)
    order = models.PositiveIntegerField(_('Order'), default=0)
    expected_pickup_time = models.TimeField(_('Expected Pickup Time'), blank=True, null=True)
    expected_dropoff_time = models.TimeField(_('Expected Drop-off Time'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Route Stop')
        verbose_name_plural = _('Route Stops')
        ordering = ['route', 'order']

    def __str__(self):
        return f"{self.route.name} - Stop {self.order}: {self.name}"


class RouteChild(models.Model):
    """Links a child to a specific stop on a route (their boarding stop)."""
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='route_children',
        verbose_name=_('Route')
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='route_assignments',
        verbose_name=_('Child')
    )
    stop = models.ForeignKey(
        RouteStop,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_children',
        verbose_name=_('Pickup/Dropoff Stop')
    )
    subscription_days = models.JSONField(
        _('Subscription Days'),
        default=list,
        help_text=_('Days of week this child is subscribed (e.g. ["SUNDAY","MONDAY"])')
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Route Child')
        verbose_name_plural = _('Route Children')
        unique_together = ('route', 'child')

    def __str__(self):
        return f"{self.child} on {self.route}"


class Trip(models.Model):
    """A single execution of a route on a given date."""
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='trips',
        verbose_name=_('Route')
    )
    trip_type = models.CharField(
        _('Trip Type'), max_length=20,
        choices=TripTypeChoices.choices,
        default=TripTypeChoices.PICKUP
    )
    status = models.CharField(
        _('Status'), max_length=20,
        choices=TripStatusChoices.choices,
        default=TripStatusChoices.SCHEDULED
    )
    driver = models.ForeignKey(
        DriverUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trips',
        verbose_name=_('Driver')
    )
    bus = models.ForeignKey(
        Bus,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trips',
        verbose_name=_('Bus')
    )
    scheduled_date = models.DateField(_('Scheduled Date'))
    start_time = models.DateTimeField(_('Actual Start Time'), blank=True, null=True)
    end_time = models.DateTimeField(_('Actual End Time'), blank=True, null=True)
    current_latitude = models.DecimalField(
        _('Current Latitude'), max_digits=10, decimal_places=7, blank=True, null=True
    )
    current_longitude = models.DecimalField(
        _('Current Longitude'), max_digits=10, decimal_places=7, blank=True, null=True
    )
    notes = models.TextField(_('Notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Trip')
        verbose_name_plural = _('Trips')
        ordering = ['-scheduled_date', '-created_at']

    def __str__(self):
        return f"{self.route.name} | {self.get_trip_type_display()} | {self.scheduled_date}"


class TripChild(models.Model):
    """Tracks the status of each child during a specific trip."""
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='trip_children',
        verbose_name=_('Trip')
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='trip_records',
        verbose_name=_('Child')
    )
    stop = models.ForeignKey(
        RouteStop,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trip_children',
        verbose_name=_('Stop')
    )
    status = models.CharField(
        _('Status'), max_length=20,
        choices=TripChildStatusChoices.choices,
        default=TripChildStatusChoices.WAITING
    )
    picked_up_at = models.DateTimeField(_('Picked Up At'), blank=True, null=True)
    dropped_off_at = models.DateTimeField(_('Dropped Off At'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Trip Child Record')
        verbose_name_plural = _('Trip Children Records')
        unique_together = ('trip', 'child')

    def __str__(self):
        return f"{self.child} - {self.trip} [{self.get_status_display()}]"
