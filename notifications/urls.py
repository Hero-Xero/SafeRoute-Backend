from django.urls import path, include

urlpatterns = [
    path('', include('notifications.apis.v1.urls')),
]
