from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from notifications.models import DeviceToken
from notifications.apis.v1.serializers import DeviceTokenSerializer


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
        return Response({
            "success": True,
            "message": _("FCM token registered successfully.")
        }, status=status.HTTP_201_CREATED)
