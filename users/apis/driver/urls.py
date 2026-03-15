from django.urls import path, include

urlpatterns = [
    path('', include('users.apis.Driver.v1.urls')),
]
