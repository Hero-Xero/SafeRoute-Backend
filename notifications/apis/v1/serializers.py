from rest_framework import serializers
from notifications.models import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token', 'device_type', 'is_active']
        read_only_fields = ['is_active']

    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data.get('token')
        # Update or create to avoid duplicates for the same token
        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': user,
                'device_type': validated_data.get('device_type', 'UNKNOWN'),
                'is_active': True
            }
        )
        return device_token
