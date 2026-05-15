from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from saferoute_backend.admin import saferoute_admin_site
from children.models import Child, StudentAbsence, LocationChangeRequest, StudentSavedLocation
from users.models import GuardianUser


# ─── Resource ───────────────────────────────────────────────────────────────────

class ChildResource(resources.ModelResource):
    guardian_email = fields.Field(
        column_name='guardian_email',
        attribute='guardian',
        widget=ForeignKeyWidget(GuardianUser, field='email')
    )

    class Meta:
        model = Child
        fields = (
            'id', 'guardian_email', 'first_name', 'last_name',
            'date_of_birth', 'gender', 'grade', 'school_name',
            'student_id', 'pickup_pin', 'is_active', 'created_at',
        )
        export_order = fields
        import_id_fields = ['id']

class StudentAbsenceResource(resources.ModelResource):
    student_name = fields.Field(
        column_name='student_name',
        attribute='student',
        widget=ForeignKeyWidget(Child, field='first_name')
    )

    class Meta:
        model = StudentAbsence
        fields = ('id', 'student_name', 'date', 'notes', 'created_at')
        export_order = fields


class LocationChangeRequestResource(resources.ModelResource):
    guardian_email = fields.Field(
        column_name='guardian_email',
        attribute='guardian',
        widget=ForeignKeyWidget(GuardianUser, field='email')
    )

    class Meta:
        model = LocationChangeRequest
        fields = ('id', 'guardian_email', 'target_date', 'change_type', 'new_location', 'status', 'notes', 'created_at')
        export_order = fields

# ─── Admin ───────────────────────────────────────────────────────────────────────

class ChildAdmin(ImportExportModelAdmin):
    resource_classes = [ChildResource]

    list_display = (
        'full_name', 'guardian', 'pickup_pin', 'school_name', 'grade', 'is_active'
    )
    list_filter = ('is_active', 'grade', 'gender')
    search_fields = (
        'first_name', 'last_name', 'student_id',
        'guardian__first_name', 'guardian__last_name', 'guardian__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['guardian']

    fieldsets = (
        (_('Personal Info'), {
            'fields': (
                'guardian', 'first_name', 'last_name',
                'date_of_birth', 'gender', 'profile_image'
            )
        }),
        (_('School Info'), {
            'fields': ('school_name', 'grade', 'student_id', 'pickup_pin')
        }),
        (_('Additional Info'), {
            'fields': ('notes', 'is_active')
        }),
        (_('Important Dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('Full Name')


class StudentAbsenceAdmin(ImportExportModelAdmin):
    resource_classes = [StudentAbsenceResource]
    list_display = ('student', 'date', 'created_at')
    list_filter = ('date', 'student__grade')
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id')
    autocomplete_fields = ['student']


class StudentSavedLocationAdmin(admin.ModelAdmin):
    list_display = ('description', 'guardian', 'is_active', 'created_at')
    list_filter = ('is_active', 'guardian')
    search_fields = ('description', 'guardian__first_name', 'guardian__last_name', 'guardian__email')


class LocationChangeRequestAdmin(ImportExportModelAdmin):
    resource_classes = [LocationChangeRequestResource]
    list_display = ('guardian', 'target_date', 'status', 'change_type', 'created_at')
    list_filter = ('status', 'target_date', 'change_type')
    search_fields = ('guardian__first_name', 'guardian__last_name', 'guardian__email')
    autocomplete_fields = ['guardian', 'students', 'new_location']


saferoute_admin_site.register(Child, ChildAdmin)
saferoute_admin_site.register(StudentAbsence, StudentAbsenceAdmin)
saferoute_admin_site.register(LocationChangeRequest, LocationChangeRequestAdmin)
saferoute_admin_site.register(StudentSavedLocation, StudentSavedLocationAdmin)
