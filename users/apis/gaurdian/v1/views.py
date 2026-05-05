from users.apis.serializers import SetInitialPasswordSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.apis.serializers import SendOtpSerializer, VerifyOtpSerializer, ResendOtpSerializer, SetNewPasswordSerializer
from users.models import GuardianUser
from users.services.otp_services import GuardianOtpService
from users.apis.serializers import GuardianProfileSerializer


class SendOtpView(APIView):
    """
    Validates Guardian credentials (email and password) and sends an OTP to their email.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = SendOtpSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        if user.type != 'GUARDIAN':
            return Response({"detail": _("User is not a Guardian.")}, status=status.HTTP_403_FORBIDDEN)

        if getattr(user, 'is_verified', False):
            # User is already verified, bypass OTP and return tokens directly
            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': _("Login successful."),
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        otp_service = GuardianOtpService(user)
        otp, created, remaining_time = otp_service.generate_or_get_otp()

        return Response({
            "message": _("OTP has been sent to your email."),
            "remaining_time": remaining_time,
        }, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    """
    Verifies the given OTP and returns JWT access and refresh tokens for Guardians.
    If the user has not verified (is_verified=False), returns a reset token instead to set an initial password.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_provided = serializer.validated_data['otp']

        try:
            user = GuardianUser.objects.get(email=email)
        except GuardianUser.DoesNotExist:
            return Response({"detail": _("No Guardian Account found with this email.")}, status=status.HTTP_404_NOT_FOUND)

        otp_service = GuardianOtpService(user)
        if otp_service.verify_otp(otp_provided):

            # If user hasn't set their initial password yet
            if not user.is_verified:
                token_generator = PasswordResetTokenGenerator()
                reset_token = token_generator.make_token(user)
                return Response({
                    "message": _("OTP verified. Please set your password."),
                    "requires_password_reset": True,
                    "reset_token": reset_token,
                    "email": user.email
                }, status=status.HTTP_200_OK)

            # If already verified, Generate JWT
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        return Response({"detail": _("Invalid or expired OTP.")}, status=status.HTTP_400_BAD_REQUEST)


class ResendOtpView(APIView):
    """
    Re-validates Guardian credentials and forces a new OTP to their email.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = ResendOtpSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        if user.type != 'GUARDIAN':
            return Response({"detail": _("User is not a Guardian.")}, status=status.HTTP_403_FORBIDDEN)

        otp_service = GuardianOtpService(user)
        otp, created, remaining_time = otp_service.generate_or_get_otp(
            force=True)

        return Response({
            "message": _("A new OTP has been sent to your email."),
            "remaining_time": remaining_time,
        }, status=status.HTTP_200_OK)


class SetNewPasswordView(APIView):
    """
    Allows an authenticated Guardian to change their password securely.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if getattr(user, 'type', None) != 'GUARDIAN':
            return Response({"detail": _("User is not a Guardian.")}, status=status.HTTP_403_FORBIDDEN)

        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"detail": _("Incorrect old password.")}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"message": _("Password has been changed successfully.")}, status=status.HTTP_200_OK)


class SetInitialPasswordView(APIView):
    """
    Allows a newly registered Guardian to set their initial password using the reset token.
    Raises errors if the password does not meet standard safety constraints.
    Returns JWT access and refresh tokens upon success.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = SetInitialPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        try:
            user = GuardianUser.objects.get(email=email)
        except GuardianUser.DoesNotExist:
            return Response({"detail": _("No Guardian Account found with this email.")}, status=status.HTTP_404_NOT_FOUND)

        if user.type != 'GUARDIAN':
            return Response({"detail": _("User is not a Guardian.")}, status=status.HTTP_403_FORBIDDEN)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, reset_token):
            return Response({"detail": _("Invalid or expired reset token.")}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.is_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': _("Password set successfully. Login successful."),
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class GuardianProfileAPIView(APIView):
    """
    E3. GET /api/v1/guardian/profile
    Returns the guardian's profile information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.type != 'GUARDIAN':
            return Response({"detail": _("Unauthorized.")}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = GuardianProfileSerializer(user)
        return Response(serializer.data)
