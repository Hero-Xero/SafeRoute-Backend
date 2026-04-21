from django.urls import path
from notifications.apis.v1 import views

urlpatterns = [
    path('api/v1/devices/fcm-token', views.FCMTokenAPIView.as_view(), name='fcm-token-register'),
]
