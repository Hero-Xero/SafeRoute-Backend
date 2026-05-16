from django.urls import path
from children.apis.v1 import views

urlpatterns = [
    # Guardian Features
    path('api/v1/guardian/pins',
         views.GuardianPinsAPIView.as_view(), name='guardian-pins'),
    path('api/v1/guardian/locations',
         views.StudentSavedLocationListCreateAPIView.as_view(), name='guardian-locations'),

    # Location Change Requests
    path('api/v1/guardian/location-change-requests/active', views.LocationChangeRequestListCreateAPIView.as_view(),
         {'active_only': 'true'}, name='location-change-requests-active'),
    path('api/v1/guardian/location-change-requests',
         views.LocationChangeRequestListCreateAPIView.as_view(), name='location-change-requests-list'),
    path('api/v1/guardian/location-change-requests/<int:id>',
         views.LocationChangeRequestDetailAPIView.as_view(), name='location-change-requests-detail'),

    # Absence
    path('api/v1/absence', views.AbsenceAPIView.as_view(), name='student-absence'),

    # Messages
    path('api/v1/guardian/messages',
         views.GuardianMessageAPIView.as_view(), name='guardian-messages'),
]
