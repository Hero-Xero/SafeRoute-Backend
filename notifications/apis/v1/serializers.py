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


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        from notifications.models import Notification
        model = Notification
        fields = [
            'id', 'type', 'channel', 'status', 'title', 'body', 
            'data', 'is_read', 'read_at', 'sent_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at']
