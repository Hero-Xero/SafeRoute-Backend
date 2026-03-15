from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class SendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError({"detail": _("Unable to log in with provided credentials.")}, code='authorization')
        else:
            raise serializers.ValidationError({"detail": _("Must include 'email' and 'password'.")}, code='authorization')

        attrs['user'] = user
        return attrs


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError({"detail": _("Incorrect email or password.")}, code='authorization')
        else:
            raise serializers.ValidationError({"detail": _("Must include 'email' and 'password'.")}, code='authorization')

        attrs['user'] = user
        return attrs


class SetNewPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return attrs


class SetInitialPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    reset_token = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        
        # Enforce strong password policies
        from django.contrib.auth.password_validation import validate_password
        try:
            validate_password(attrs['new_password'])
        except Exception as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
            
        return attrs
from rest_framework_simplejwt.tokens import RefreshToken


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(write_only=True)
    access_token = ''

    def validate(self, data):
        try:
            # Create a RefreshToken object
            refresh = RefreshToken(data['refresh_token'])

            # Generate a new access token
            self.access_token = str(refresh.access_token)

            return data
        except Exception as e:
            raise serializers.ValidationError(
                {"detail": 'Invalid refresh token.'})

    def to_representation(self, instance):
        to_repr = super().to_representation(instance)
        to_repr.update({'access_token': self.access_token})

        return to_repr
