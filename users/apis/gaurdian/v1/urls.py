from django.urls import path

from users.apis.Gaurdian.v1 import views

urlpatterns = [
    path('api/v1/auth/login', views.SendOtpView.as_view(), name='guardian-auth-login'),
    path('api/v1/auth/verify', views.VerifyOtpView.as_view(), name='guardian-auth-verify'),
    path('api/v1/auth/resend-otp', views.ResendOtpView.as_view(), name='guardian-auth-resend'),
    path('api/v1/auth/change-password', views.SetNewPasswordView.as_view(), name='guardian-auth-change-password'),
    path('api/v1/auth/set-initial-password', views.SetInitialPasswordView.as_view(), name='guardian-auth-set-initial-password'),
]
