from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from trips.models import Trip, TripChild, Route, RouteStop, RouteChild
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
        today = timezone.now().date()
        trip = None

        if user.type == 'GUARDIAN':
            # Problem 2 Fix: Resolve guardian -> children -> today's trip -> check active
            children = list(user.children.filter(is_active=True).values_list('id', flat=True))
            if not children:
                return Response({"tripActive": False, "message": _("No children found for this guardian.")})

            # Find any trip today that has one of this guardian's children in it
            trip = Trip.objects.filter(
                scheduled_date=today,
                trip_children__child_id__in=children
            ).order_by('-status').first()  # IN_PROGRESS sorts above SCHEDULED

            if not trip:
                return Response({"tripActive": False, "message": _("No trip found for today for your children.")})

            # Determine status label for the frontend
            if trip.status == TripStatusChoices.IN_PROGRESS:
                status_label = 'ongoing'
            elif trip.status == TripStatusChoices.SCHEDULED:
                status_label = 'online'
            else:
                status_label = 'offline'

            serializer = TripDetailsSerializer(trip)
            data = serializer.data
            data['tripActive'] = trip.status == TripStatusChoices.IN_PROGRESS
            data['tripStatus'] = status_label
            data['message'] = _("Trip found.")
            return Response(data)

        elif user.type == 'DRIVER':
            trip = Trip.objects.filter(
                status=TripStatusChoices.IN_PROGRESS, driver=user
            ).first()
        elif user.type == 'ASSISTANT':
            trip = Trip.objects.filter(
                status=TripStatusChoices.IN_PROGRESS, assistant=user
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
    Assigned students for today's route.
    Shared endpoint for Driver and Assistant.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        direction = request.query_params.get('direction', 'am').upper()
        today = timezone.now().date()

        # Map am|pm to PICKUP|DROPOFF
        trip_type = TripTypeChoices.PICKUP if direction == 'AM' else TripTypeChoices.DROPOFF

        if user.type not in ('DRIVER', 'ASSISTANT'):
            return Response({"detail": _("Unauthorized.")}, status=status.HTTP_403_FORBIDDEN)

        # Build base filter by user type
        user_filter = {"driver": user} if user.type == 'DRIVER' else {"assistant": user}

        # First try IN_PROGRESS, then most recent SCHEDULED trip for this user
        trip = (
            Trip.objects.filter(
                trip_type=trip_type,
                status=TripStatusChoices.IN_PROGRESS,
                **user_filter
            ).first()
            or
            Trip.objects.filter(
                trip_type=trip_type,
                status=TripStatusChoices.SCHEDULED,
                **user_filter
            ).order_by('-scheduled_date').first()  # most recent scheduled trip
        )

        if not trip:
            # Fallback: find route directly assigned to this assistant/driver
            if user.type == 'ASSISTANT':
                route = (
                    Route.objects.filter(assistant=user).first()
                    or Route.objects.filter(trips__assistant=user).order_by('-trips__scheduled_date').first()
                )
            else:
                route = (
                    Route.objects.filter(driver=user).first()
                    or Route.objects.filter(trips__driver=user).order_by('-trips__scheduled_date').first()
                )

            if not route:
                return Response({"students": []})

            route_children = RouteChild.objects.filter(
                route=route, is_active=True
            ).select_related('child', 'child__guardian', 'stop')

            from children.models import GuardianMessage
            students_data = []
            for rc in route_children:
                child = rc.child
                guardian = child.guardian
                stop = rc.stop
                pickup = None
                if stop:
                    lat = float(stop.latitude)
                    lng = float(stop.longitude)
                    pickup = {
                        "description": stop.name,
                        "gMapsUrl": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
                        "coords": [lat, lng],
                    }
                # Latest message for this student
                msg = GuardianMessage.objects.filter(student=child).order_by('-created_at').first()
                latest_message = {"content": msg.content, "createdAt": msg.created_at.isoformat()} if msg else None

                students_data.append({
                    "id": child.id,
                    "name": child.full_name,
                    "grade": child.get_grade_display() if child.grade else None,
                    "pinCodes": {
                        "masterPin": guardian.pickup_pin if guardian else None,
                        "tempPin": guardian.temp_pin if guardian else None,
                    },
                    "guardianContact": {
                        "primaryContactNum": str(guardian.phone_number) if guardian and guardian.phone_number else None,
                        "primaryContactRole": str(_("Guardian")),
                        "secondaryContactNum": str(guardian.secondary_phone) if guardian and guardian.secondary_phone else None,
                        "secondaryContactRole": str(_("Secondary Guardian")) if guardian and guardian.secondary_phone else None,
                    } if guardian else None,
                    "pickedUp": False,
                    "droppedOff": False,
                    "latestMessage": latest_message,
                    "activePickup": pickup,
                })
            return Response({"students": students_data})

        # Trip found — use the serializer for live data
        students = trip.trip_children.select_related(
            'child', 'child__guardian', 'stop'
        ).all()
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

        # Rotate the guardian's temp_pin on every pickup/dropoff action
        guardian = trip_child.child.guardian
        if guardian:
            import random
            guardian.temp_pin = "".join([str(random.randint(0, 9)) for _ in range(4)])
            guardian.save(update_fields=['temp_pin'])

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
