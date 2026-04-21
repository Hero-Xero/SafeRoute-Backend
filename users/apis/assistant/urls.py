from django.urls import path, include

urlpatterns = [
    path('', include('users.apis.assistant.v1.urls')),
]
