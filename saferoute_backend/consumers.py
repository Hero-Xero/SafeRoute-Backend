import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class TripConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.room_group_name = f'trip_{self.trip_id}'

        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close()
            return

        # TODO: Here we could verify if the user has access to this trip.
        # For MVP, we will accept the connection if they are authenticated.

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket (if clients need to send something directly)
    async def receive(self, text_data):
        pass

    # Receive location update from room group
    async def trip_location_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'data': event['data']
        }))

    # Receive student status update from room group
    async def trip_student_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'student_status',
            'data': event['data']
        }))

    # Receive guardian message from room group
    async def trip_guardian_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'guardian_message',
            'data': event['data']
        }))
