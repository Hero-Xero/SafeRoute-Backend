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
    {
        'app': 'children',
        'label': _('Children'),
        'models': [
            'Child',
        ]
    },
    {
        'app': 'trips',
        'label': _('Trips & Routes'),
        'models': [
            'Bus',
            'Route',
            'Trip',
        ]
    },
    {
        'app': 'notifications',
        'label': _('Notifications'),
        'models': [
            'BroadcastNotification',
            'Notification',
            'NotificationTemplate',
            'DeviceToken',
        ]
    },
]
