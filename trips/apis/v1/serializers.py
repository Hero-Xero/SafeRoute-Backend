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


class StudentDataSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='child.id')       # Child ID — use this in /students/{id}/boarded
    name = serializers.CharField(source='child.full_name')
    grade = serializers.SerializerMethodField()
    pinCodes = serializers.SerializerMethodField()
    guardianContact = serializers.SerializerMethodField()
    pickedUp = serializers.SerializerMethodField()
    droppedOff = serializers.SerializerMethodField()
    latestMessage = serializers.SerializerMethodField()
    activePickup = serializers.SerializerMethodField()

    class Meta:
        model = TripChild
        fields = [
            'id', 'name', 'grade', 'pinCodes', 'guardianContact',
            'pickedUp', 'droppedOff', 'latestMessage', 'activePickup',
        ]

    def get_grade(self, obj):
        return obj.child.get_grade_display() if obj.child.grade else None

    def get_pinCodes(self, obj):
        guardian = obj.child.guardian
        if not guardian:
            return {"masterPin": None, "tempPin": None}
        return {
            "masterPin": guardian.pickup_pin,   # auto-generated on guardian creation
            "tempPin": guardian.temp_pin or None,  # manually set, nullable
        }

    def get_guardianContact(self, obj):
        guardian = obj.child.guardian
        if not guardian:
            return None
        return {
            "primaryContactNum": str(guardian.phone_number) if guardian.phone_number else None,
            "primaryContactRole": str(_("Guardian")),
            "secondaryContactNum": str(guardian.secondary_phone) if guardian.secondary_phone else None,
            "secondaryContactRole": str(_("Secondary Guardian")) if guardian.secondary_phone else None,
        }

    def get_pickedUp(self, obj):
        from trips.enums import TripChildStatusChoices
        return obj.status in [
            TripChildStatusChoices.PICKED_UP,
            TripChildStatusChoices.DROPPED_OFF
        ]

    def get_droppedOff(self, obj):
        from trips.enums import TripChildStatusChoices
        return obj.status == TripChildStatusChoices.DROPPED_OFF

    def get_latestMessage(self, obj):
        from children.models import GuardianMessage
        msg = GuardianMessage.objects.filter(student=obj.child).order_by('-created_at').first()
        if msg:
            return {
                "content": msg.content,
                "createdAt": msg.created_at.isoformat(),
            }
        return None

    def get_activePickup(self, obj):
        """
        Priority:
        1. An accepted LocationChangeRequest for today for this child
        2. The student's assigned RouteStop
        3. None
        """
        from django.utils import timezone
        from children.models import LocationChangeRequest
        from children.enums import LocationChangeStatus

        today = timezone.now().date()

        change_request = LocationChangeRequest.objects.filter(
            students=obj.child,
            target_date=today,
            status=LocationChangeStatus.ACCEPTED,
        ).select_related('new_location').first()

        if change_request and change_request.new_location:
            loc = change_request.new_location
            lat = float(loc.latitude)
            lng = float(loc.longitude)
            gmaps = loc.gmaps_url or f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
            return {
                "description": loc.description,
                "gMapsUrl": gmaps,
                "coords": [lat, lng],
            }

        if obj.stop:
            lat = float(obj.stop.latitude)
            lng = float(obj.stop.longitude)
            gmaps = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
            return {
                "description": obj.stop.name,
                "gMapsUrl": gmaps,
                "coords": [lat, lng],
            }

        return None


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
            "eta": 0,
            "busCoords": [float(obj.current_latitude or 0), float(obj.current_longitude or 0)]
        }


class TripStatusUpdateSerializer(serializers.Serializer):
    currentCoords = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)
