from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from users.models import GuardianUser
from children.enums import GradeChoices, ChildGenderChoices, LocationChangeStatus, LocationChangeType


class Child(models.Model):
    guardian = models.ForeignKey(
        GuardianUser,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_('Guardian'),
    )
    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    date_of_birth = models.DateField(_('Date of Birth'), blank=True, null=True)
    gender = models.CharField(
        _('Gender'), max_length=10,
        choices=ChildGenderChoices.choices,
        blank=True, null=True
    )
    grade = models.CharField(
        _('Grade'), max_length=20,
        choices=GradeChoices.choices,
        blank=True, null=True
    )
    school_name = models.CharField(_('School Name'), max_length=200, blank=True, null=True)
    profile_image = models.ImageField(
        upload_to='children/profile_images/',
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'gif'])
        ],
        verbose_name=_('Profile Image')
    )
    student_id = models.CharField(_('Student ID'), max_length=100, blank=True, null=True)
    pickup_pin = models.CharField(
        _('Pickup PIN'), 
        max_length=6, 
        blank=True, 
        null=True, 
        help_text=_('4-6 digit code for pickup verification.')
    )
    notes = models.TextField(_('Notes'), blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Child')
        verbose_name_plural = _('Children')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.pickup_pin:
            import random
            self.pickup_pin = "".join([str(random.randint(0, 9)) for _ in range(4)])
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class StudentSavedLocation(models.Model):
    """Locations saved by guardians for their children's pickup/dropoff."""
    guardian = models.ForeignKey(
        GuardianUser,
        on_delete=models.CASCADE,
        related_name='saved_locations',
        verbose_name=_('Guardian')
    )
    description = models.CharField(_('Description'), max_length=255, help_text=_("e.g. Grandma's House"))
    latitude = models.DecimalField(_('Latitude'), max_digits=10, decimal_places=7)
    longitude = models.DecimalField(_('Longitude'), max_digits=10, decimal_places=7)
    gmaps_url = models.URLField(_('Google Maps URL'), blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Student Saved Location')
        verbose_name_plural = _('Student Saved Locations')

    def __str__(self):
        return f"{self.description} ({self.guardian})"


class LocationChangeRequest(models.Model):
    """Requests by guardians to change the pickup/dropoff location for students on a specific date."""
    guardian = models.ForeignKey(
        GuardianUser,
        on_delete=models.CASCADE,
        related_name='location_change_requests',
        verbose_name=_('Guardian')
    )
    students = models.ManyToManyField(
        Child,
        related_name='location_change_requests',
        verbose_name=_('Students')
    )
    target_date = models.DateField(_('Target Date'))
    change_type = models.CharField(
        _('Change Type'), max_length=20,
        choices=LocationChangeType.choices,
        default=LocationChangeType.BOTH
    )
    new_location = models.ForeignKey(
        StudentSavedLocation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='change_requests',
        verbose_name=_('New Location')
    )
    status = models.CharField(
        _('Status'), max_length=30,
        choices=LocationChangeStatus.choices,
        default=LocationChangeStatus.PENDING_REVIEW
    )
    effective_until = models.DateTimeField(
        _('Effective Until'),
        blank=True, null=True,
        help_text=_('When the lock on new requests for this scope/date clears.')
    )
    notes = models.TextField(_('Notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Location Change Request')
        verbose_name_plural = _('Location Change Requests')
        ordering = ['-created_at']

    def __str__(self):
        return f"Request {self.id} - {self.guardian} [{self.get_status_display()}]"
