from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from saferoute_backend.admin import saferoute_admin_site
from notifications.models import (
    DeviceToken, NotificationTemplate, Notification, BroadcastNotification
)
from notifications.enums import (
    NotificationTypeChoices, NotificationStatusChoices,
    NotificationChannelChoices, DeviceTypeChoices,
)
from users.models import User


# ─── Resources ──────────────────────────────────────────────────────────────────

class DeviceTokenResource(resources.ModelResource):
    user_email = fields.Field(
        column_name='user_email',
        attribute='user',
        widget=ForeignKeyWidget(User, field='email')
    )

    class Meta:
        model = DeviceToken
        fields = ('id', 'user_email', 'token', 'device_type', 'is_active', 'created_at')
        export_order = fields
        import_id_fields = ['id']


class NotificationTemplateResource(resources.ModelResource):
    class Meta:
        model = NotificationTemplate
        fields = (
            'id', 'type', 'title_en', 'title_ar',
            'body_en', 'body_ar', 'is_active', 'created_at'
        )
        export_order = fields
        import_id_fields = ['id']


class NotificationResource(resources.ModelResource):
    user_email = fields.Field(
        column_name='user_email',
        attribute='user',
        widget=ForeignKeyWidget(User, field='email')
    )

    class Meta:
        model = Notification
        fields = (
            'id', 'user_email', 'type', 'channel', 'status',
            'title', 'body', 'is_read', 'read_at', 'sent_at', 'created_at'
        )
        export_order = fields
        import_id_fields = ['id']


class BroadcastNotificationResource(resources.ModelResource):
    sent_by_email = fields.Field(
        column_name='sent_by_email',
        attribute='sent_by',
        widget=ForeignKeyWidget(User, field='email')
    )

    class Meta:
        model = BroadcastNotification
        fields = (
            'id', 'title', 'body', 'type',
            'target_all', 'target_guardians', 'target_drivers',
            'is_sent', 'sent_at', 'sent_by_email', 'created_at'
        )
        export_order = fields
        import_id_fields = ['id']


# ─── Device Token Admin ─────────────────────────────────────────────────────────

class DeviceTokenAdmin(ImportExportModelAdmin):
    resource_classes = [DeviceTokenResource]

    list_display = ('user', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'token')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('Device Info'), {
            'fields': ('user', 'token', 'device_type', 'is_active')
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ─── Notification Template Admin ────────────────────────────────────────────────

class NotificationTemplateAdmin(ImportExportModelAdmin):
    resource_classes = [NotificationTemplateResource]

    list_display = ('type', 'title_en', 'is_active', 'created_at')
    list_filter = ('is_active', 'type')
    search_fields = ('title_en', 'title_ar', 'body_en', 'body_ar')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('Type'), {
            'fields': ('type', 'is_active')
        }),
        (_('English Content'), {
            'fields': ('title_en', 'body_en')
        }),
        (_('Arabic Content'), {
            'fields': ('title_ar', 'body_ar')
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ─── Notification Admin ─────────────────────────────────────────────────────────

class NotificationAdmin(ImportExportModelAdmin):
    resource_classes = [NotificationResource]

    list_display = (
        'title', 'user', 'type', 'channel', 'status_badge',
        'is_read', 'sent_at', 'created_at'
    )
    list_filter = ('status', 'type', 'channel', 'is_read')
    search_fields = ('title', 'body', 'user__email', 'user__first_name')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'read_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Recipient'), {
            'fields': ('user',)
        }),
        (_('Notification Content'), {
            'fields': ('type', 'channel', 'title', 'body', 'data')
        }),
        (_('Status'), {
            'fields': ('status', 'is_read', 'read_at', 'sent_at', 'error_message')
        }),
        (_('Related Objects'), {
            'fields': ('trip', 'child'),
            'classes': ('collapse',)
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': '#f59e0b',
            'SENT': '#10b981',
            'FAILED': '#ef4444',
            'READ': '#6366f1',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')


# ─── Broadcast Notification Admin ───────────────────────────────────────────────

class BroadcastNotificationAdmin(ImportExportModelAdmin):
    resource_classes = [BroadcastNotificationResource]

    list_display = (
        'title', 'type', 'target_summary', 'is_sent', 'sent_at', 'sent_by', 'created_at'
    )
    list_filter = ('is_sent', 'type', 'target_all', 'target_guardians', 'target_drivers')
    search_fields = ('title', 'body')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'sent_by')

    fieldsets = (
        (_('Notification Content'), {
            'fields': ('title', 'body', 'type')
        }),
        (_('Target Audience'), {
            'fields': ('target_all', 'target_guardians', 'target_drivers')
        }),
        (_('Sending Info'), {
            'fields': ('is_sent', 'sent_at', 'sent_by')
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        is_newly_sent = False
        if obj.is_sent and not obj.sent_at:
            obj.sent_at = timezone.now()
            obj.sent_by = request.user
            is_newly_sent = True
        
        super().save_model(request, obj, form, change)

        if is_newly_sent:
            from users.models import User
            from notifications.models import Notification
            from users.enums import UserTypeChoices

            users_qs = User.objects.none()
            if obj.target_all:
                users_qs = User.objects.all()
            else:
                if obj.target_guardians:
                    users_qs = users_qs | User.objects.filter(type=UserTypeChoices.GUARDIAN)
                if obj.target_drivers:
                    users_qs = users_qs | User.objects.filter(type=UserTypeChoices.DRIVER)

            notifications_to_create = [
                Notification(
                    user=u,
                    title=obj.title,
                    body=obj.body,
                    type=obj.type,
                    status='SENT',  # Mark as sent for testing
                    sent_at=timezone.now()
                ) for u in users_qs
            ]
            if notifications_to_create:
                Notification.objects.bulk_create(notifications_to_create)

    def target_summary(self, obj):
        if obj.target_all:
            return _('All Users')
        targets = []
        if obj.target_guardians:
            targets.append(_('Guardians'))
        if obj.target_drivers:
            targets.append(_('Drivers'))
        return ', '.join(str(t) for t in targets) or _('None')
    target_summary.short_description = _('Target')


saferoute_admin_site.register(DeviceToken, DeviceTokenAdmin)
saferoute_admin_site.register(NotificationTemplate, NotificationTemplateAdmin)
saferoute_admin_site.register(Notification, NotificationAdmin)
saferoute_admin_site.register(BroadcastNotification, BroadcastNotificationAdmin)
