from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from django.utils import timezone

from children.models import Child, StudentSavedLocation, LocationChangeRequest
from children.apis.v1.serializers import (
    ChildPinSerializer, StudentSavedLocationSerializer, LocationChangeRequestSerializer,
    AbsenceRequestSerializer, GuardianMessageSerializer
)
from children.enums import LocationChangeStatus
from children.services.absence_services import mark_students_absent, remove_students_absence


class GuardianPinsAPIView(APIView):
    """
    C1. GET /api/v1/guardian/pins
    Returns pickup pins for the guardian's children.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.type != 'GUARDIAN':
            return Response({"detail": _("Unauthorized.")}, status=status.HTTP_403_FORBIDDEN)
        
        children = user.children.filter(is_active=True)
        serializer = ChildPinSerializer(children, many=True)
        return Response(serializer.data)


class StudentSavedLocationListCreateAPIView(generics.ListCreateAPIView):
    """
    C2. GET /api/v1/guardian/locations
    C3. POST /api/v1/guardian/locations
    """
    serializer_class = StudentSavedLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentSavedLocation.objects.filter(guardian=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(guardian=self.request.user)


class LocationChangeRequestListCreateAPIView(generics.ListCreateAPIView):
    """
    D1. GET /api/v1/guardian/location-change-requests/active
    D2. POST /api/v1/guardian/location-change-requests
    """
    serializer_class = LocationChangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Specific rule for D1: active requests
        queryset = LocationChangeRequest.objects.filter(guardian=self.request.user)
        active_only = self.request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            queryset = queryset.filter(status__in=[LocationChangeStatus.PENDING_REVIEW, LocationChangeStatus.ACCEPTED])
        return queryset

    def perform_create(self, serializer):
        serializer.save(guardian=self.request.user)

    def list(self, request, *args, **kwargs):
        # Specific implementation for D1 contract: "request": LocationChangeRequest | null
        if request.query_params.get('active_only') == 'true':
            active_request = self.get_queryset().first()
            return Response({
                "request": self.get_serializer(active_request).data if active_request else None
            })
        return super().list(request, *args, **kwargs)


class LocationChangeRequestDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    D3. DELETE /api/v1/guardian/location-change-requests/{requestId}
    D4. GET /api/v1/guardian/location-change-requests/{requestId}
    """
    serializer_class = LocationChangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return LocationChangeRequest.objects.filter(guardian=self.request.user)

    def delete(self, request, *args, **kwargs):
        # D3 logic: can cancel if status is pending or accepted (and before deadline)
        instance = self.get_object()
        if instance.status not in [LocationChangeStatus.PENDING_REVIEW, LocationChangeStatus.ACCEPTED]:
            return Response(
                {"detail": _("Cannot cancel a request that is already processed.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deadline check (simplified: 3 AM of target date)
        if timezone.now().date() >= instance.target_date:
            return Response(
                {"detail": _("Cannot cancel on the day of the request.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = LocationChangeStatus.CANCELLED
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AbsenceAPIView(APIView):
    """
    E2. POST /api/v1/absence / DELETE /api/v1/absence
    Mark / undo absence for students.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AbsenceRequestSerializer(data=request.data)
        if serializer.is_valid():
            mark_students_absent(
                guardian=request.user,
                student_ids=serializer.validated_data['student_ids'],
                date=serializer.validated_data['date'],
                notes=serializer.validated_data.get('notes')
            )
            return Response({"message": _("Absence marked.")})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        serializer = AbsenceRequestSerializer(data=request.data)
        if serializer.is_valid():
            remove_students_absence(
                guardian=request.user,
                student_ids=serializer.validated_data['student_ids'],
                date=serializer.validated_data['date']
            )
            return Response({"message": _("Absence removed.")})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GuardianMessageAPIView(generics.CreateAPIView):
    """
    C4. POST /api/v1/guardian/messages
    Sends a message from a guardian regarding a student.
    """
    serializer_class = GuardianMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(guardian=self.request.user)
        # TODO: Trigger socket event 'guardian-message' (B11)
        # TODO: Send push notification to assistant
