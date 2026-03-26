from django.urls import path

from users.apis.gaurdian.v1 import views

urlpatterns = [
    path('api/v1/guardian/auth/login',
         views.SendOtpView.as_view(), name='guardian-auth-login'),
    path('api/v1/guardian/auth/verify',
         views.VerifyOtpView.as_view(), name='guardian-auth-verify'),
    path('api/v1/guardian/auth/resend-otp',
         views.ResendOtpView.as_view(), name='guardian-auth-resend'),
    path('api/v1/guardian/auth/change-password',
         views.SetNewPasswordView.as_view(), name='guardian-auth-change-password'),
    path('api/v1/guardian/auth/set-initial-password',
         views.SetInitialPasswordView.as_view(), name='guardian-auth-set-initial-password'),
]
