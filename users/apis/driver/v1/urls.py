from django.urls import path

from users.apis.Driver.v1 import views

urlpatterns = [
    path('api/v1/auth/login', views.SendOtpView.as_view(), name='driver-auth-login'),
    path('api/v1/auth/verify', views.VerifyOtpView.as_view(), name='driver-auth-verify'),
    path('api/v1/auth/resend-otp', views.ResendOtpView.as_view(), name='driver-auth-resend'),
    path('api/v1/auth/change-password', views.SetNewPasswordView.as_view(), name='driver-auth-change-password'),
    path('api/v1/auth/set-initial-password', views.SetInitialPasswordView.as_view(), name='driver-auth-set-initial-password'),
]
