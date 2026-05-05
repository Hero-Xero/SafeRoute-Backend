from django.urls import path
from trips.apis.v1 import views

urlpatterns = [
    # Trip Lifecycle
    path('api/v1/trips/current', views.CurrentTripAPIView.as_view(), name='trip-current'),
    path('api/v1/trips/active', views.TripLifecycleAPIView.as_view(), name='trip-active-check'),
    path('api/v1/trips/start', views.TripLifecycleAPIView.as_view(), {'action': 'start'}, name='trip-start'),
    path('api/v1/trips/end', views.TripLifecycleAPIView.as_view(), {'action': 'end'}, name='trip-end'),
    path('api/v1/trips/location', views.TripLocationAPIView.as_view(), name='trip-location-update'),
    
    # Routes & Students
    path('api/v1/routes/students', views.RouteStudentsAPIView.as_view(), name='route-students-list'),
    path('api/v1/students/<int:student_id>/boarded', views.StudentActionAPIView.as_view(), {'action': 'boarded'}, name='student-boarded'),
    path('api/v1/students/<int:student_id>/dropped-off', views.StudentActionAPIView.as_view(), {'action': 'dropped-off'}, name='student-dropped-off'),
    
    # School
    path('api/v1/school/location', views.SchoolLocationAPIView.as_view(), name='school-location'),
]
