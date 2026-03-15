from django.urls import path, include

urlpatterns = [
    path('', include('users.apis.Gaurdian.v1.urls')),
]
