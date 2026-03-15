from django.utils.translation import gettext_lazy as _

# Admin priorities for apps and models
# This dictionary defines the priority for each app and model in the admin interface.
ADMIN_ORDERING = [
    {
        'app': 'auth',
        'label': _('Groups and Permissions'),
        'models': [
            'Group',
        ],
    },
    {
        'app': 'users',
        'label': _('Users'),
        'models': [
            'AdminUser',
            'DriverUser',
            'GuardianUser',
        ]
    },
]
