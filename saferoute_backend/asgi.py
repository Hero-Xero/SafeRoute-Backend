"""
ASGI config for saferoute_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saferoute_backend.settings')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from saferoute_backend.channelsmiddleware import JwtAuthMiddleware
from saferoute_backend.consumers import TripConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter([
            path("ws/trip/<int:trip_id>/", TripConsumer.as_asgi()),
        ])
    ),
})
