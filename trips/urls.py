from django.urls import path, include

urlpatterns = [
    path('', include('trips.apis.v1.urls')),
]
