from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from users.enums import UserTypeChoices
from users.models import AdminUser


class AdminUserCreationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields required
        for field_name, field in self.fields.items():
            field.required = True

        # For boolean fields, they'll be required by default in HTML
        # but their validation works differently
        self.fields['is_superuser'].required = False
        self.fields['is_staff'].required = False
        self.fields['is_active'].required = False

        # Set initial values for boolean fields
        self.fields['is_superuser'].initial = False  # Default to not superuser
        self.fields['is_staff'].initial = True  # Default to staff user
        self.fields['is_active'].initial = True  # Default to active

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        validator = UserFieldValidator(
            user_type=UserTypeChoices.ADMIN)
        validator.validate_phone_number(
            phone_number, exclude_pk=self.instance.pk)
        return phone_number

    def save(self, commit=True):
        # Set the user type to SUPPLIER before saving
        user = super().save(commit=False)
        user.type = UserTypeChoices.ADMIN  # Make sure to import UserTypeChoices
        if commit:
            user.save()
        return user


class AdminUserChangeForm(forms.ModelForm):
    class Meta:
        model = AdminUser
        fields = ('first_name', 'last_name', 'email', 'phone_number',
                  'is_superuser', 'is_staff', 'is_active', )
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email'),
            'phone_number': _('Phone Number'),
            'is_superuser': _('Is Superuser'),
            'is_staff': _('Is Staff User'),
            'is_active': _('Is Active'),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        validator = UserFieldValidator(
            user_type=UserTypeChoices.ADMIN)
        validator.validate_phone_number(
            phone_number, exclude_pk=self.instance.pk)
        return phone_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields required except the boolean fields
        for field_name, field in self.fields.items():
            if field_name not in ['is_superuser', 'is_staff', 'is_active']:
                field.required = True

        self.fields['groups'].required = False
        self.fields['user_permissions'].required = False
