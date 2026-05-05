from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from notifications.models import DeviceToken, Notification
from notifications.apis.v1.serializers import DeviceTokenSerializer, NotificationSerializer


class FCMTokenAPIView(generics.CreateAPIView):
    """
    E1. POST /api/v1/devices/fcm-token
    Register FCM token for the authenticated user.
    """
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": _("FCM token registered successfully.")}, status=status.HTTP_201_CREATED)


class NotificationListAPIView(generics.ListAPIView):
    """
    E4. GET /api/v1/notifications
    Returns the user's notification history.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
