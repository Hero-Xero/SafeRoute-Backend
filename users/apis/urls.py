from django.urls import path, include

from users.apis import views as common_views

urlpatterns = [
    # Common Views
    path(f'api/common/auth/token/refresh', common_views.RefreshTokenAPIView.as_view(),
         name='token-refresh-api-view'),
    
    # Guardian and Driver 
    path('', include('users.apis.gaurdian.urls')),
    path('', include('users.apis.driver.urls')),
    path('', include('users.apis.assistant.urls')),
]