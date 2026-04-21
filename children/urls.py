from django.urls import path, include

urlpatterns = [
    path('', include('children.apis.v1.urls')),
]
