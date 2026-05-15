from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from trips.models import Trip, TripChild, Route, RouteStop, Bus
from children.models import Child
from users.models import DriverUser, AssistantUser


class RouteStopSerializer(serializers.ModelSerializer):
    coords = serializers.SerializerMethodField()

    class Meta:
        model = RouteStop
        fields = ['id', 'name', 'latitude', 'longitude', 'order', 'coords']

    def get_coords(self, obj):
        return [float(obj.latitude), float(obj.longitude)]


class ChildContactSerializer(serializers.Serializer):
    title = serializers.CharField()
    phoneNum = serializers.CharField()


class StudentLocationSerializer(serializers.Serializer):
    id = serializers.CharField()
    description = serializers.CharField()
    gMapsUrl = serializers.URLField(source='gmaps_url', allow_null=True)
    coords = serializers.SerializerMethodField()
    type = serializers.CharField()
    active = serializers.BooleanField(source='is_active')

    def get_coords(self, obj):
        return [float(obj.latitude), float(obj.longitude)]


class StudentDataSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='child.id')
    name = serializers.CharField(source='child.full_name')
    grade = serializers.CharField(source='child.get_grade_display')
    contacts = serializers.SerializerMethodField()
    primaryPin = serializers.CharField(source='child.pickup_pin')
    tempPin = serializers.CharField(default="") # TBD: implement temp pins if needed
    activePickup = serializers.SerializerMethodField()
    activeDropoff = serializers.SerializerMethodField()
    statusDesc = serializers.CharField(source='get_status_display')
    boardedBus = serializers.SerializerMethodField()
    droppedOff = serializers.SerializerMethodField()

    class Meta:
        model = TripChild
        fields = [
            'id', 'name', 'grade', 'contacts', 'primaryPin', 'tempPin',
            'activePickup', 'activeDropoff', 'statusDesc', 'boardedBus', 'droppedOff'
        ]

    def get_contacts(self, obj):
        guardian = obj.child.guardian
        return [
            {"title": _("Guardian"), "phoneNum": str(guardian.phone_number)}
        ]

    def get_activePickup(self, obj):
        # For now return the assigned stop
        if obj.stop:
            return {
                "id": str(obj.stop.id),
                "description": obj.stop.name,
                "gMapsUrl": "",
                "coords": [float(obj.stop.latitude), float(obj.stop.longitude)],
                "type": "pickup",
                "active": True
            }
        return None

    def get_activeDropoff(self, obj):
        # For now return the assigned stop
        if obj.stop:
            return {
                "id": str(obj.stop.id),
                "description": obj.stop.name,
                "gMapsUrl": "",
                "coords": [float(obj.stop.latitude), float(obj.stop.longitude)],
                "type": "dropoff",
                "active": True
            }
        return None

    def get_boardedBus(self, obj):
        from trips.enums import TripChildStatusChoices
        return obj.status == TripChildStatusChoices.PICKED_UP

    def get_droppedOff(self, obj):
        from trips.enums import TripChildStatusChoices
        return obj.status == TripChildStatusChoices.DROPPED_OFF


class TripUpdateSerializer(serializers.Serializer):
    eta = serializers.IntegerField(default=0)
    busCoords = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)


class TripDetailsSerializer(serializers.ModelSerializer):
    tripActive = serializers.SerializerMethodField()
    licencePlateLetters = serializers.SerializerMethodField()
    licencePlateNumbers = serializers.SerializerMethodField()
    driverName = serializers.SerializerMethodField()
    assistantName = serializers.SerializerMethodField()
    assistantPhoneNum = serializers.SerializerMethodField()
    tripUpdate = serializers.SerializerMethodField()
    routeName = serializers.CharField(source='route.name', read_only=True)
    routeId = serializers.IntegerField(source='route.id', read_only=True)

    class Meta:
        model = Trip
        fields = [
            'tripActive', 'licencePlateLetters', 'licencePlateNumbers',
            'driverName', 'assistantName', 'assistantPhoneNum', 'tripUpdate',
            'routeName', 'routeId'
        ]

    def get_tripActive(self, obj):
        from trips.enums import TripStatusChoices
        return obj.status == TripStatusChoices.IN_PROGRESS

    def get_licencePlateLetters(self, obj):
        # Assuming plate number format "ABC 123"
        if obj.bus and obj.bus.plate_number:
            parts = obj.bus.plate_number.split()
            return parts[0] if parts else ""
        return ""

    def get_licencePlateNumbers(self, obj):
        if obj.bus and obj.bus.plate_number:
            parts = obj.bus.plate_number.split()
            return parts[1] if len(parts) > 1 else parts[0]
        return ""

    def get_driverName(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name or ''} {obj.driver.last_name or ''}".strip()
        return ""

    def get_assistantName(self, obj):
        if obj.assistant:
            return f"{obj.assistant.first_name or ''} {obj.assistant.last_name or ''}".strip()
        return ""

    def get_assistantPhoneNum(self, obj):
        return str(obj.assistant.phone_number) if obj.assistant else ""

    def get_tripUpdate(self, obj):
        return {
            "eta": 0, # Skip for now
            "busCoords": [float(obj.current_latitude or 0), float(obj.current_longitude or 0)]
        }


class TripStatusUpdateSerializer(serializers.Serializer):
    currentCoords = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)
