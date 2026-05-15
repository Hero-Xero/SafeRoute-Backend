import os
import django

# Initialize Django environment for the RQ worker
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saferoute_backend.settings')
django.setup()

import json
import logging
from django.conf import settings
from django.utils import timezone
from notifications.models import Notification, DeviceToken

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

# Initialize Firebase app if not already initialized
if not firebase_admin._apps:
    # Look for the credentials file in the project root
    cred_path = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        logger.warning(f"Firebase credentials not found at {cred_path}")

def send_push_notification_task(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return

    tokens = DeviceToken.objects.filter(user=notification.user, is_active=True).values_list('token', flat=True)
    if not tokens:
        notification.status = 'FAILED'
        notification.error_message = 'No active device tokens found for user.'
        notification.save(update_fields=['status', 'error_message'])
        return

    if not firebase_admin._apps:
        logger.warning(f"Mock sending PUSH to {notification.user.email}. Tokens: {list(tokens)}")
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])
        return

    # Real FCM Logic using firebase-admin SDK
    try:
        # data payload values must be strings
        stringified_data = {str(k): str(v) for k, v in (notification.data or {}).items()}
        
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body,
            ),
            data=stringified_data,
            tokens=list(tokens),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        content_available=True,
                    )
                )
            )
        )
        
        response = messaging.send_each_for_multicast(message)
        
        if response.success_count > 0:
            notification.status = 'SENT'
            notification.sent_at = timezone.now()
            if response.failure_count > 0:
                notification.error_message = f"Sent to {response.success_count}, failed to {response.failure_count}"
        else:
            notification.status = 'FAILED'
            if response.responses:
                notification.error_message = str(response.responses[0].exception)
            else:
                notification.error_message = "All tokens failed."
                
    except Exception as e:
        notification.status = 'FAILED'
        notification.error_message = str(e)
    
    notification.save(update_fields=['status', 'sent_at', 'error_message'])
