from rest_framework import serializers
from children.models import Child, StudentSavedLocation, LocationChangeRequest
from children.enums import LocationChangeStatus, LocationChangeType


class ChildPinSerializer(serializers.ModelSerializer):
    masterPin = serializers.CharField(source='guardian.pickup_pin')
    tempPin = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = ['id', 'masterPin', 'tempPin']

    def get_tempPin(self, obj):
        return obj.guardian.temp_pin or None


class StudentSavedLocationSerializer(serializers.ModelSerializer):
    coords = serializers.SerializerMethodField()

    class Meta:
        model = StudentSavedLocation
        fields = ['id', 'description', 'latitude', 'longitude', 'gmaps_url', 'coords', 'is_active']
        read_only_fields = ['id', 'is_active']

    def get_coords(self, obj):
        return [float(obj.latitude), float(obj.longitude)]

    def validate(self, data):
        # If coords are provided in a special way in request, handle here
        return data


class LocationChangeRequestSerializer(serializers.ModelSerializer):
    studentIds = serializers.PrimaryKeyRelatedField(
        source='students', many=True, queryset=Child.objects.all()
    )
    newLocationId = serializers.PrimaryKeyRelatedField(
        source='new_location', queryset=StudentSavedLocation.objects.all()
    )

    class Meta:
        model = LocationChangeRequest
        fields = [
            'id', 'guardian', 'studentIds', 'target_date', 'change_type',
            'newLocationId', 'status', 'effective_until', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'effective_until', 'created_at', 'guardian']

    def validate(self, data):
        # Implementation of the blocking rule:
        # While status is pending_review OR (accepted and not fulfilled for targetDate),
        # guardian cannot POST a new request for the same scope/date rules.
        guardian = self.context['request'].user
        target_date = data.get('target_date')
        
        existing_blocking = LocationChangeRequest.objects.filter(
            guardian=guardian,
            target_date=target_date,
            status__in=[LocationChangeStatus.PENDING_REVIEW, LocationChangeStatus.ACCEPTED]
        ).exists()

        if existing_blocking:
            raise serializers.ValidationError(
                "You already have a pending or active request for this date."
            )
        
        return data


class AbsenceRequestSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True
    )
    date = serializers.DateField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class GuardianMessageSerializer(serializers.Serializer):
    studentIds = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Child.objects.all()),
        min_length=1
    )
    content = serializers.CharField()
