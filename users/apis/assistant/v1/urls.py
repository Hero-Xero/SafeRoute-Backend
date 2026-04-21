from django.urls import path
from users.apis.assistant.v1 import views

urlpatterns = [
    path('api/v1/assistant/auth/login', views.AssistantSendOtpView.as_view(), name='assistant-auth-login'),
    path('api/v1/assistant/auth/verify', views.AssistantVerifyOtpView.as_view(), name='assistant-auth-verify'),
    path('api/v1/assistant/auth/resend-otp', views.AssistantResendOtpView.as_view(), name='assistant-auth-resend'),
    path('api/v1/assistant/auth/set-initial-password', views.AssistantSetInitialPasswordView.as_view(), name='assistant-auth-set-initial-password'),
    path('api/v1/assistant/auth/change-password', views.AssistantChangePasswordView.as_view(), name='assistant-auth-change-password'),
]
