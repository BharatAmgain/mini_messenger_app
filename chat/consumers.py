import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message, UserStatus

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f'chat_{self.conversation_id}'

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Update user status to online
            await self.update_user_status(True)

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Update user status to offline
            await self.update_user_status(False)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'chat_message':
            message_content = text_data_json['message']
            message = await self.save_message(message_content)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'timestamp': message.timestamp.isoformat(),
                    'message_id': message.id,
                }
            )

        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user': self.user.username,
                    'typing': text_data_json['typing']
                }
            )

        elif message_type == 'read_receipt':
            await self.mark_message_as_read(text_data_json['message_id'])

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user': event['user'],
            'typing': event['typing']
        }))

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        return message

    @database_sync_to_async
    def update_user_status(self, online):
        status, created = UserStatus.objects.get_or_create(user=self.user)
        status.online = online
        status.save()

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            message.read = True
            message.save()
        except Message.DoesNotExist:
            pass


class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.status_group_name = 'user_status'

            await self.channel_layer.group_add(
                self.status_group_name,
                self.channel_name
            )

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'status_group_name'):
            await self.channel_layer.group_discard(
                self.status_group_name,
                self.channel_name
            )

    async def user_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'user_id': event['user_id'],
            'online': event['online'],
            'username': event['username'],
        }))


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.room_name = f"user_{self.user.id}"
            self.room_group_name = f'calls_{self.room_name}'

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'call_request':
            await self.handle_call_request(text_data_json)
        elif message_type == 'call_answer':
            await self.handle_call_answer(text_data_json)
        elif message_type == 'ice_candidate':
            await self.handle_ice_candidate(text_data_json)
        elif message_type == 'end_call':
            await self.handle_end_call(text_data_json)

    async def handle_call_request(self, data):
        target_user_id = data['target_user_id']
        call_type = data.get('call_type', 'video')  # 'video' or 'audio'

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'incoming_call',
                'caller_id': self.user.id,
                'caller_name': self.user.username,
                'call_type': call_type,
                'call_id': data['call_id']
            }
        )

    async def handle_call_answer(self, data):
        caller_id = data['caller_id']
        accepted = data['accepted']

        await self.channel_layer.group_send(
            f'calls_user_{caller_id}',
            {
                'type': 'call_answered',
                'accepted': accepted,
                'answerer_id': self.user.id,
                'answerer_name': self.user.username
            }
        )

    async def handle_ice_candidate(self, data):
        target_user_id = data['target_user_id']
        candidate = data['candidate']

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'ice_candidate',
                'candidate': candidate,
                'sender_id': self.user.id
            }
        )

    async def handle_end_call(self, data):
        target_user_id = data['target_user_id']

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'call_ended',
                'ended_by': self.user.id
            }
        )

    async def incoming_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'caller_id': event['caller_id'],
            'caller_name': event['caller_name'],
            'call_type': event['call_type'],
            'call_id': event['call_id']
        }))

    async def call_answered(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_answered',
            'accepted': event['accepted'],
            'answerer_id': event['answerer_id'],
            'answerer_name': event['answerer_name']
        }))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
            'sender_id': event['sender_id']
        }))

    async def call_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'ended_by': event['ended_by']
        }))