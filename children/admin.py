from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from saferoute_backend.admin import saferoute_admin_site
from children.models import Child
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


saferoute_admin_site.register(Child, ChildAdmin)
