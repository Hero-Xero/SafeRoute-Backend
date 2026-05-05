from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from saferoute_backend.admin import saferoute_admin_site
from trips.models import (
    Bus, Route, RouteStop, RouteChild, Trip, TripChild, School
)
from trips.enums import TripStatusChoices, TripTypeChoices, BusStatusChoices
from users.models import DriverUser, AssistantUser


# ─── Resources ──────────────────────────────────────────────────────────────────

class BusResource(resources.ModelResource):
    driver_email = fields.Field(
        column_name='driver_email',
        attribute='driver',
        widget=ForeignKeyWidget(DriverUser, field='email')
    )

    class Meta:
        model = Bus
        fields = ('id', 'plate_number', 'model', 'capacity', 'driver_email', 'is_active', 'created_at')
        export_order = fields
        import_id_fields = ['id']


class RouteResource(resources.ModelResource):
    bus_plate = fields.Field(
        column_name='bus_plate',
        attribute='bus',
        widget=ForeignKeyWidget(Bus, field='plate_number')
    )

    class Meta:
        model = Route
        fields = (
            'id', 'name', 'description', 'school_name',
            'school_latitude', 'school_longitude', 'bus_plate', 'is_active', 'created_at'
        )
        export_order = fields
        import_id_fields = ['id']


class RouteStopResource(resources.ModelResource):
    route_name = fields.Field(
        column_name='route_name',
        attribute='route',
        widget=ForeignKeyWidget(Route, field='name')
    )

    class Meta:
        model = RouteStop
        fields = (
            'id', 'route_name', 'name', 'order',
            'latitude', 'longitude',
            'expected_pickup_time', 'expected_dropoff_time'
        )
        export_order = fields
        import_id_fields = ['id']


class TripResource(resources.ModelResource):
    route_name = fields.Field(
        column_name='route_name',
        attribute='route',
        widget=ForeignKeyWidget(Route, field='name')
    )
    driver_email = fields.Field(
        column_name='driver_email',
        attribute='driver',
        widget=ForeignKeyWidget(DriverUser, field='email')
    )
    bus_plate = fields.Field(
        column_name='bus_plate',
        attribute='bus',
        widget=ForeignKeyWidget(Bus, field='plate_number')
    )
    assistant_email = fields.Field(
        column_name='assistant_email',
        attribute='assistant',
        widget=ForeignKeyWidget(AssistantUser, field='email')
    )

    class Meta:
        model = Trip
        fields = (
            'id', 'route_name', 'trip_type', 'status',
            'driver_email', 'bus_plate', 'assistant_email',
            'scheduled_date', 'start_time', 'end_time', 'notes', 'created_at'
        )
        export_order = fields
        import_id_fields = ['id']


# ─── Route Stop Inline ──────────────────────────────────────────────────────────

class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ('order', 'name', 'latitude', 'longitude', 'expected_pickup_time', 'expected_dropoff_time')
    ordering = ['order']


class RouteChildInline(admin.TabularInline):
    model = RouteChild
    extra = 0
    fields = ('child', 'stop', 'subscription_days', 'is_active')
    autocomplete_fields = ['child']


class TripChildInline(admin.TabularInline):
    model = TripChild
    extra = 0
    fields = ('child', 'stop', 'status', 'picked_up_at', 'dropped_off_at')
    readonly_fields = ('picked_up_at', 'dropped_off_at')
    autocomplete_fields = ['child']


# ─── Bus Admin ──────────────────────────────────────────────────────────────────

class BusAdmin(ImportExportModelAdmin):
    resource_classes = [BusResource]

    list_display = ('plate_number', 'model', 'capacity', 'driver', 'status', 'is_active', 'created_at')
    list_filter = ('is_active', 'status')
    search_fields = ('plate_number', 'model', 'driver__first_name', 'driver__last_name')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['driver']

    fieldsets = (
        (_('Bus Info'), {
            'fields': ('plate_number', 'model', 'capacity', 'driver', 'status', 'is_active')
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ─── Route Admin ────────────────────────────────────────────────────────────────

class RouteAdmin(ImportExportModelAdmin):
    resource_classes = [RouteResource]

    list_display = ('name', 'school_name', 'bus', 'stop_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'school_name')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['bus']
    inlines = [RouteStopInline, RouteChildInline]

    fieldsets = (
        (_('Route Info'), {
            'fields': ('name', 'description', 'bus', 'is_active')
        }),
        (_('School Info'), {
            'fields': ('school_name', 'school_latitude', 'school_longitude')
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def stop_count(self, obj):
        return obj.stops.count()
    stop_count.short_description = _('Stops')


# ─── Trip Admin ─────────────────────────────────────────────────────────────────

class TripAdmin(ImportExportModelAdmin):
    resource_classes = [TripResource]

    list_display = (
        'route', 'trip_type', 'status_badge', 'driver', 'bus', 'assistant',
        'scheduled_date', 'start_time', 'end_time'
    )
    list_filter = ('status', 'trip_type', 'scheduled_date')
    search_fields = (
        'route__name', 'driver__first_name', 'driver__last_name', 'bus__plate_number'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'scheduled_date'
    autocomplete_fields = ['route', 'driver', 'bus', 'assistant']
    inlines = [TripChildInline]

    fieldsets = (
        (_('Trip Info'), {
            'fields': ('route', 'trip_type', 'status', 'scheduled_date')
        }),
        (_('Assigned Resources'), {
            'fields': ('driver', 'bus', 'assistant')
        }),
        (_('Timing'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('Live Location'), {
            'fields': ('current_latitude', 'current_longitude'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'SCHEDULED': '#6366f1',
            'IN_PROGRESS': '#f59e0b',
            'COMPLETED': '#10b981',
            'CANCELLED': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'is_active')
    search_fields = ('name',)

saferoute_admin_site.register(Bus, BusAdmin)
saferoute_admin_site.register(Route, RouteAdmin)
saferoute_admin_site.register(Trip, TripAdmin)
saferoute_admin_site.register(School, SchoolAdmin)
