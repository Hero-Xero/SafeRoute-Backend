from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from trips.models import Trip, TripChild, Route, RouteStop
from trips.apis.v1.serializers import (
    TripDetailsSerializer, StudentDataSerializer, TripStatusUpdateSerializer
)
from trips.enums import TripStatusChoices, TripChildStatusChoices, TripTypeChoices
from users.models import DriverUser, AssistantUser


class CurrentTripAPIView(APIView):
    """
    B1. GET /api/v1/trips/current
    Returns a snapshot of the current active trip for the authenticated parent or driver.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        trip = None
        
        if user.type == 'GUARDIAN':
            # For guardians, find the active trip that has one of their children
            trip = Trip.objects.filter(
                status=TripStatusChoices.IN_PROGRESS,
                trip_children__child__guardian=user
            ).first()
        elif user.type == 'DRIVER':
            trip = Trip.objects.filter(
                status=TripStatusChoices.IN_PROGRESS,
                driver=user
            ).first()
        elif user.type == 'ASSISTANT':
            trip = Trip.objects.filter(
                status=TripStatusChoices.IN_PROGRESS,
                assistant=user
            ).first()

        if not trip:
            return Response({"tripActive": False, "message": _("No active trip found.")})

        serializer = TripDetailsSerializer(trip)
        data = serializer.data
        data["tripActive"] = True
        data["message"] = _("Active trip found.")
        return Response(data)


class TripLifecycleAPIView(APIView):
    """
    B2. POST /api/v1/trips/start
    B4. GET /api/v1/trips/active
    B5. POST /api/v1/trips/end
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # B4. Check if a trip is active
        user = request.user
        active_trip = Trip.objects.filter(
            status=TripStatusChoices.IN_PROGRESS,
            driver=user
        ).exists()
        return Response({"tripActive": active_trip})

    def post(self, request, action=None):
        user = request.user
        if user.type != 'DRIVER':
            return Response({"detail": _("Only drivers can manage trips.")}, status=status.HTTP_403_FORBIDDEN)

        if action == 'start':
            # Find a scheduled trip for today
            trip = Trip.objects.filter(
                driver=user,
                status=TripStatusChoices.SCHEDULED,
                scheduled_date=timezone.now().date()
            ).first()

            if not trip:
                # For demo purposes, create one if none exists (or return error)
                return Response({"detail": _("No scheduled trip found for today.")}, status=status.HTTP_404_NOT_FOUND)

            if Trip.objects.filter(driver=user, status=TripStatusChoices.IN_PROGRESS).exists():
                return Response({"detail": _("You already have an active trip.")}, status=status.HTTP_400_BAD_REQUEST)

            trip.status = TripStatusChoices.IN_PROGRESS
            trip.start_time = timezone.now()
            trip.save()
            return Response({"detail": _("Trip started successfully."), "trip_id": trip.id})

        elif action == 'end':
            trip = Trip.objects.filter(
                driver=user,
                status=TripStatusChoices.IN_PROGRESS
            ).first()

            if not trip:
                return Response({"detail": _("No active trip found to end.")}, status=status.HTTP_404_NOT_FOUND)

            trip.status = TripStatusChoices.COMPLETED
            trip.end_time = timezone.now()
            trip.save()
            return Response({"detail": _("Trip ended successfully.")})

        return Response({"detail": _("Invalid action.")}, status=status.HTTP_400_BAD_REQUEST)


class TripLocationAPIView(APIView):
    """
    B3. POST /api/v1/trips/location
    Driver pushes GPS while trip is active.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.type != 'DRIVER':
            return Response({"detail": _("Only drivers can update location.")}, status=status.HTTP_403_FORBIDDEN)

        trip = Trip.objects.filter(
            driver=user,
            status=TripStatusChoices.IN_PROGRESS
        ).first()

        if not trip:
            return Response({"detail": _("No active trip found.")}, status=status.HTTP_404_NOT_FOUND)

        serializer = TripStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        coords = serializer.validated_data['currentCoords']
        trip.current_latitude = coords[0]
        trip.current_longitude = coords[1]
        trip.save()

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'trip_{trip.id}',
            {
                'type': 'trip_location_update',
                'data': {
                    'currentCoords': coords
                }
            }
        )

        return Response({"message": _("Location updated.")})


class RouteStudentsAPIView(APIView):
    """
    B6. GET /api/v1/routes/students?direction=am|pm
    Assigned students for today’s route.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        direction = request.query_params.get('direction', 'am').upper()
        
        # Map am|pm to PICKUP|DROPOFF
        trip_type = TripTypeChoices.PICKUP if direction == 'AM' else TripTypeChoices.DROPOFF

        # Find trip for the driver/assistant
        trip_filter = {"status": TripStatusChoices.IN_PROGRESS, "trip_type": trip_type}
        if user.type == 'DRIVER':
            trip_filter["driver"] = user
        elif user.type == 'ASSISTANT':
            trip_filter["assistant"] = user
        else:
            return Response({"detail": _("Unauthorized.")}, status=status.HTTP_403_FORBIDDEN)

        trip = Trip.objects.filter(**trip_filter).first()
        if not trip:
            # Try to find scheduled trip if no active one
            trip = Trip.objects.filter(
                scheduled_date=timezone.now().date(),
                trip_type=trip_type,
                **( {"driver": user} if user.type == 'DRIVER' else {"assistant": user} )
            ).first()

        if not trip:
            return Response({"students": []})

        students = trip.trip_children.all()
        serializer = StudentDataSerializer(students, many=True)
        return Response({"students": serializer.data})


class StudentActionAPIView(APIView):
    """
    B8. POST /api/v1/students/{studentId}/boarded
    B9. POST /api/v1/students/{studentId}/dropped-off
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, student_id=None, action=None):
        user = request.user
        # Logic to find the TripChild record
        # student_id here is usually the child's ID or trip_child id? 
        # Requirement says {studentId}. We'll assume Child.id.

        trip_child = TripChild.objects.filter(
            child_id=student_id,
            trip__status=TripStatusChoices.IN_PROGRESS
        ).first()

        if not trip_child:
            return Response({"detail": _("Student not found in an active trip.")}, status=status.HTTP_404_NOT_FOUND)

        if action == 'boarded':
            trip_child.status = TripChildStatusChoices.PICKED_UP
            trip_child.picked_up_at = timezone.now()
        elif action == 'dropped-off':
            trip_child.status = TripChildStatusChoices.DROPPED_OFF
            trip_child.dropped_off_at = timezone.now()
        else:
            return Response({"detail": _("Invalid action.")}, status=status.HTTP_400_BAD_REQUEST)

        trip_child.save()

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'trip_{trip_child.trip.id}',
            {
                'type': 'trip_student_status',
                'data': {
                    'student_id': student_id,
                    'status': action
                }
            }
        )

        # Send FCM notification to parent
        guardian = trip_child.child.guardian
        if guardian:
            from notifications.models import Notification, NotificationChannelChoices, NotificationStatusChoices
            from notifications.tasks import send_push_notification_task
            from rq import Queue
            from redis import Redis
            from django.conf import settings

            title = _("Student Picked Up") if action == 'boarded' else _("Student Dropped Off")
            status_text = _('picked up') if action == 'boarded' else _('dropped off')
            body = _(f"{trip_child.child.first_name} has been {status_text} successfully.")
            
            notification = Notification.objects.create(
                user=guardian,
                title=title,
                body=body,
                type='trip_update',
                channel=NotificationChannelChoices.PUSH,
                status=NotificationStatusChoices.PENDING,
                data={'student_id': str(student_id), 'action': action}
            )
            
            redis_conn = Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=int(getattr(settings, 'REDIS_PORT', 6379))
            )
            q = Queue('default', connection=redis_conn)
            q.enqueue(send_push_notification_task, notification.id)

        return Response({"message": _(f"Student marked as {action}.")})


class SchoolLocationAPIView(APIView):
    """
    B7. GET /api/v1/school/location
    Returns the school's name and Google Maps URL.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from trips.models import School
        school = School.objects.filter(is_active=True).first()
        
        if school:
            gmaps_url = school.gmaps_url or f"https://www.google.com/maps/search/?api=1&query={school.latitude},{school.longitude}"
            return Response({
                "name": school.name,
                "gMapsUrl": gmaps_url,
                "latitude": school.latitude,
                "longitude": school.longitude
            })

        # Fallback to Route logic if no global school is defined (for backward compatibility)
        route = Route.objects.filter(is_active=True).first()
        if not route:
            return Response({
                "name": "SafeRoute School",
                "gMapsUrl": "https://www.google.com/maps/search/?api=1&query=24.7136,46.6753"
            })
        
        gmaps_url = f"https://www.google.com/maps/search/?api=1&query={route.school_latitude},{route.school_longitude}"
        return Response({
            "name": route.school_name or "SafeRoute School",
            "gMapsUrl": gmaps_url,
            "latitude": route.school_latitude,
            "longitude": route.school_longitude
        })
