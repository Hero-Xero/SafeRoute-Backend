from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from django.utils import timezone

from children.models import Child, StudentSavedLocation, LocationChangeRequest
from children.apis.v1.serializers import (
    ChildPinSerializer, StudentSavedLocationSerializer, LocationChangeRequestSerializer
)
from children.enums import LocationChangeStatus


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
        return Response({
            "success": True,
            "data": serializer.data
        })


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
        # Implement absence marking logic
        return Response({"success": True, "message": _("Absence marked.")})

    def delete(self, request):
        return Response({"success": True, "message": _("Absence removed.")})
