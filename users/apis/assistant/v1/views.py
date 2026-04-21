from users.apis.serializers import (
    SendOtpSerializer, VerifyOtpSerializer, ResendOtpSerializer,
    SetInitialPasswordSerializer, SetNewPasswordSerializer
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import AssistantUser
from users.services.otp_services import AssistantOtpService


class AssistantSendOtpView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = SendOtpSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        if user.type != 'ASSISTANT':
            return Response({"detail": _("User is not an Assistant.")}, status=status.HTTP_403_FORBIDDEN)

        if getattr(user, 'is_verified', False):
            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': _("Login successful."),
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        otp_service = AssistantOtpService(user)
        otp, created, remaining_time = otp_service.generate_or_get_otp()

        return Response({
            "detail": _("OTP has been sent to your email."),
            "remaining_time": remaining_time,
        }, status=status.HTTP_200_OK)


class AssistantVerifyOtpView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_provided = serializer.validated_data['otp']

        try:
            user = AssistantUser.objects.get(email=email)
        except AssistantUser.DoesNotExist:
            return Response({"detail": _("No Assistant Account found with this email.")}, status=status.HTTP_404_NOT_FOUND)

        otp_service = AssistantOtpService(user)
        if otp_service.verify_otp(otp_provided):
            if not user.is_verified:
                token_generator = PasswordResetTokenGenerator()
                reset_token = token_generator.make_token(user)
                return Response({
                    "detail": _("OTP verified. Please set your password."),
                    "requires_password_reset": True,
                    "reset_token": reset_token,
                    "email": user.email
                }, status=status.HTTP_200_OK)

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        return Response({"detail": _("Invalid or expired OTP.")}, status=status.HTTP_400_BAD_REQUEST)


class AssistantResendOtpView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = ResendOtpSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        if user.type != 'ASSISTANT':
            return Response({"detail": _("User is not an Assistant.")}, status=status.HTTP_403_FORBIDDEN)

        otp_service = AssistantOtpService(user)
        otp, created, remaining_time = otp_service.generate_or_get_otp(force=True)

        return Response({
            "detail": _("A new OTP has been sent to your email."),
            "remaining_time": remaining_time,
        }, status=status.HTTP_200_OK)


class AssistantSetInitialPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = SetInitialPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        try:
            user = AssistantUser.objects.get(email=email)
        except AssistantUser.DoesNotExist:
            return Response({"detail": _("No Assistant Account found with this email.")}, status=status.HTTP_404_NOT_FOUND)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, reset_token):
            return Response({"detail": _("Invalid or expired reset token.")}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.is_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': _("Password set successfully. Login successful."),
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class AssistantChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if getattr(user, 'type', None) != 'ASSISTANT':
            return Response({"detail": _("User is not an Assistant.")}, status=status.HTTP_403_FORBIDDEN)

        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"detail": _("Incorrect old password.")}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"detail": _("Password has been changed successfully.")}, status=status.HTTP_200_OK)
