from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from users.models import User

@database_sync_to_async
def get_user(validated_token):
    try:
        user = User.objects.get(id=validated_token["user_id"])
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            try:
                token_name, token_key = headers[b'authorization'].decode().split()
                if token_name.lower() == 'bearer':
                    UntypedToken(token_key)
                    decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
                    scope['user'] = await get_user(decoded_data)
            except (ValueError, InvalidToken, TokenError, Exception):
                scope['user'] = AnonymousUser()
        else:
            # Also support token in query string for WebSockets (ws://...?token=...)
            query_string = scope.get("query_string", b"").decode()
            if "token=" in query_string:
                try:
                    token_key = query_string.split("token=")[1].split("&")[0]
                    UntypedToken(token_key)
                    decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
                    scope['user'] = await get_user(decoded_data)
                except Exception:
                    scope['user'] = AnonymousUser()
            else:
                scope['user'] = AnonymousUser()
        return await super().__call__(scope, receive, send)
