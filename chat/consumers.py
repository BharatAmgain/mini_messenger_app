# chat/consumers.py - COMPLETE WITH REAL-TIME CALL SUPPORT
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, UserStatus, ChatCall
from accounts.models import Notification

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

            # Send online status to others in the conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'status': 'online'
                }
            )
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

            # Send offline status to others
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'status': 'offline'
                }
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(text_data_json)
        elif message_type == 'file_upload':
            await self.handle_file_upload(text_data_json)
        elif message_type == 'voice_message':
            await self.handle_voice_message(text_data_json)

    async def handle_chat_message(self, data):
        message_content = data['message']
        message = await self.save_message(message_content)

        # Create notification for other participants
        await self.create_message_notification(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': self.user.username,
                'sender_id': str(self.user.id),
                'timestamp': message.timestamp.isoformat(),
                'message_id': str(message.id),
                'message_type': 'text'
            }
        )

    async def handle_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': self.user.username,
                'user_id': str(self.user.id),
                'typing': data['typing']
            }
        )

    async def handle_read_receipt(self, data):
        await self.mark_message_as_read(data['message_id'])
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'message_id': data['message_id'],
                'user_id': str(self.user.id)
            }
        )

    async def handle_file_upload(self, data):
        message = await self.save_file_message(data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'file_message',
                'file_url': message.file.url,
                'file_name': message.file_name,
                'file_size': message.get_file_size_display(),
                'sender': self.user.username,
                'sender_id': str(self.user.id),
                'timestamp': message.timestamp.isoformat(),
                'message_id': str(message.id),
                'message_type': data['file_type']
            }
        )

    async def handle_voice_message(self, data):
        message = await self.save_voice_message(data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'voice_message',
                'file_url': message.file.url,
                'duration': message.voice_duration,
                'waveform': message.voice_waveform,
                'sender': self.user.username,
                'sender_id': str(self.user.id),
                'timestamp': message.timestamp.isoformat(),
                'message_id': str(message.id)
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps(event))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps(event))

    async def file_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def voice_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_status(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            message_type='text'
        )
        return message

    @database_sync_to_async
    def save_file_message(self, data):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=data.get('caption', ''),
            message_type=data['file_type'],
            file=data['file'],
            file_name=data['file_name'],
            file_size=data['file_size']
        )
        return message

    @database_sync_to_async
    def save_voice_message(self, data):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            message_type='voice',
            file=data['file'],
            voice_duration=data['duration'],
            voice_waveform=data['waveform']
        )
        return message

    @database_sync_to_async
    def update_user_status(self, online):
        UserStatus.objects.update_or_create(
            user=self.user,
            defaults={
                'online': online,
                'last_seen': timezone.now()
            }
        )

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if message.sender != self.user:
                message.is_read = True
                message.read_at = timezone.now()
                message.save()
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def create_message_notification(self, message):
        conversation = message.conversation
        for participant in conversation.participants.exclude(id=self.user.id):
            Notification.objects.create(
                user=participant,
                notification_type='message',
                title=f"New message from {self.user.username}",
                message=message.content[:100],
                related_url=f"/chat/{conversation.id}/"
            )


class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.status_group_name = 'global_status'

            await self.channel_layer.group_add(
                self.status_group_name,
                self.channel_name
            )

            # Update user status
            await self.update_user_status(True)

            await self.accept()

            # Broadcast online status
            await self.channel_layer.group_send(
                self.status_group_name,
                {
                    'type': 'status_update',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'online': True,
                    'last_seen': timezone.now().isoformat()
                }
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'status_group_name'):
            await self.channel_layer.group_discard(
                self.status_group_name,
                self.channel_name
            )

            # Update user status
            await self.update_user_status(False)

            # Broadcast offline status
            await self.channel_layer.group_send(
                self.status_group_name,
                {
                    'type': 'status_update',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'online': False,
                    'last_seen': timezone.now().isoformat()
                }
            )

    async def status_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def update_user_status(self, online):
        UserStatus.objects.update_or_create(
            user=self.user,
            defaults={
                'online': online,
                'last_seen': timezone.now()
            }
        )


class CallConsumer(AsyncWebsocketConsumer):
    """Complete WebRTC call handling with all features"""

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
            print(f"Call consumer connected for user: {self.user.username}")
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"Call consumer disconnected for user: {self.user.username if hasattr(self, 'user') else 'Unknown'}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']
            print(f"Received call message: {message_type} from {self.user.username}")

            if message_type == 'call_request':
                await self.handle_call_request(text_data_json)
            elif message_type == 'call_accept':
                await self.handle_call_accept(text_data_json)
            elif message_type == 'call_reject':
                await self.handle_call_reject(text_data_json)
            elif message_type == 'call_end':
                await self.handle_call_end(text_data_json)
            elif message_type == 'ice_candidate':
                await self.handle_ice_candidate(text_data_json)
            elif message_type == 'offer':
                await self.handle_offer(text_data_json)
            elif message_type == 'answer':
                await self.handle_answer(text_data_json)
            elif message_type == 'mute_toggle':
                await self.handle_mute_toggle(text_data_json)
            elif message_type == 'call_missed':
                await self.handle_call_missed(text_data_json)

        except Exception as e:
            print(f"Error in call consumer: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_call_request(self, data):
        """Initiate a new call"""
        target_user_id = data['target_user_id']
        call_type = data.get('call_type', 'video')  # 'video' or 'audio'
        call_id = str(uuid.uuid4())

        # Check if target user is online
        target_online = await self.check_user_online(target_user_id)

        if not target_online:
            await self.send(text_data=json.dumps({
                'type': 'call_error',
                'message': 'User is offline'
            }))
            return

        # Create call record in database
        call = await self.create_call_record(target_user_id, call_type, call_id)

        # Send call request to target user
        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'incoming_call',
                'call_id': call_id,
                'caller_id': str(self.user.id),
                'caller_name': self.user.username,
                'call_type': call_type,
                'conversation_id': data.get('conversation_id')
            }
        )

        # Send acknowledgment to caller
        await self.send(text_data=json.dumps({
            'type': 'call_request_sent',
            'call_id': call_id,
            'target_user_id': target_user_id
        }))

    async def handle_call_accept(self, data):
        """Accept an incoming call"""
        call_id = data['call_id']
        caller_id = data['caller_id']

        # Update call record
        await self.update_call_status(call_id, 'answered')

        # Send acceptance to caller
        await self.channel_layer.group_send(
            f'calls_user_{caller_id}',
            {
                'type': 'call_accepted',
                'call_id': call_id,
                'accepted_by': str(self.user.id),
                'accepted_by_name': self.user.username
            }
        )

        # Send confirmation to answerer
        await self.send(text_data=json.dumps({
            'type': 'call_connected',
            'call_id': call_id
        }))

    async def handle_call_reject(self, data):
        """Reject an incoming call"""
        call_id = data['call_id']
        caller_id = data['caller_id']

        # Update call record
        await self.update_call_status(call_id, 'rejected')

        # Send rejection to caller
        await self.channel_layer.group_send(
            f'calls_user_{caller_id}',
            {
                'type': 'call_rejected',
                'call_id': call_id,
                'rejected_by': str(self.user.id),
                'rejected_by_name': self.user.username
            }
        )

    async def handle_call_end(self, data):
        """End an active call"""
        call_id = data['call_id']
        target_user_id = data['target_user_id']

        # Update call record with duration
        await self.end_call_record(call_id)

        # Notify other participant
        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'call_ended',
                'call_id': call_id,
                'ended_by': str(self.user.id)
            }
        )

        # Send confirmation to caller
        await self.send(text_data=json.dumps({
            'type': 'call_ended_confirmation',
            'call_id': call_id
        }))

    async def handle_call_missed(self, data):
        """Handle missed call"""
        call_id = data['call_id']
        caller_id = data['caller_id']

        # Update call record
        await self.update_call_status(call_id, 'missed')

        # Create missed call notification
        await self.create_notification(
            user_id=caller_id,
            notification_type='call',
            title='Missed Call',
            message=f'You missed a call from {self.user.username}'
        )

    async def handle_ice_candidate(self, data):
        """Forward ICE candidates between peers"""
        target_user_id = data['target_user_id']
        candidate = data['candidate']

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'ice_candidate',
                'candidate': candidate,
                'sender_id': str(self.user.id)
            }
        )

    async def handle_offer(self, data):
        """Forward WebRTC offer to target user"""
        target_user_id = data['target_user_id']
        offer = data['offer']

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'offer',
                'offer': offer,
                'sender_id': str(self.user.id)
            }
        )

    async def handle_answer(self, data):
        """Forward WebRTC answer to target user"""
        target_user_id = data['target_user_id']
        answer = data['answer']

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'answer',
                'answer': answer,
                'sender_id': str(self.user.id)
            }
        )

    async def handle_mute_toggle(self, data):
        """Handle mute/unmute during call"""
        target_user_id = data['target_user_id']
        muted = data['muted']
        audio_type = data.get('audio_type', 'microphone')  # 'microphone' or 'speaker'

        await self.channel_layer.group_send(
            f'calls_user_{target_user_id}',
            {
                'type': 'mute_toggle',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'muted': muted,
                'audio_type': audio_type
            }
        )

    # Event handlers for receiving messages from channel layer
    async def incoming_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'call_id': event['call_id'],
            'caller_id': event['caller_id'],
            'caller_name': event['caller_name'],
            'call_type': event['call_type'],
            'conversation_id': event.get('conversation_id')
        }))

    async def call_accepted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_accepted',
            'call_id': event['call_id'],
            'accepted_by': event['accepted_by'],
            'accepted_by_name': event['accepted_by_name']
        }))

    async def call_rejected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_rejected',
            'call_id': event['call_id'],
            'rejected_by': event['rejected_by'],
            'rejected_by_name': event['rejected_by_name']
        }))

    async def call_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'call_id': event['call_id'],
            'ended_by': event['ended_by']
        }))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
            'sender_id': event['sender_id']
        }))

    async def offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'offer': event['offer'],
            'sender_id': event['sender_id']
        }))

    async def answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'answer',
            'answer': event['answer'],
            'sender_id': event['sender_id']
        }))

    async def mute_toggle(self, event):
        await self.send(text_data=json.dumps({
            'type': 'mute_toggle',
            'user_id': event['user_id'],
            'username': event['username'],
            'muted': event['muted'],
            'audio_type': event['audio_type']
        }))

    @database_sync_to_async
    def check_user_online(self, user_id):
        """Check if user is online"""
        try:
            user = User.objects.get(id=user_id)
            status = UserStatus.objects.filter(user=user).first()
            return status.online if status else False
        except User.DoesNotExist:
            return False

    @database_sync_to_async
    def create_call_record(self, target_user_id, call_type, call_id):
        """Create call record in database"""
        try:
            target_user = User.objects.get(id=target_user_id)
            conversation = Conversation.objects.filter(
                participants=self.user
            ).filter(
                participants=target_user,
                is_group=False
            ).first()

            call = ChatCall.objects.create(
                id=call_id,
                conversation=conversation,
                caller=self.user,
                recipient=target_user,
                call_type=call_type,
                status='initiated',
                started_at=timezone.now()
            )
            return call
        except Exception as e:
            print(f"Error creating call record: {e}")
            return None

    @database_sync_to_async
    def update_call_status(self, call_id, status):
        """Update call status"""
        try:
            call = ChatCall.objects.get(id=call_id)
            call.status = status
            if status == 'answered':
                call.answered_at = timezone.now()
            elif status in ['rejected', 'missed', 'cancelled']:
                call.ended_at = timezone.now()
            call.save()
        except ChatCall.DoesNotExist:
            pass

    @database_sync_to_async
    def end_call_record(self, call_id):
        """End call and calculate duration"""
        try:
            call = ChatCall.objects.get(id=call_id)
            call.status = 'completed'
            call.ended_at = timezone.now()
            if call.started_at:
                duration = (call.ended_at - call.started_at).total_seconds()
                call.duration = int(duration)
            call.save()
        except ChatCall.DoesNotExist:
            pass

    @database_sync_to_async
    def create_notification(self, user_id, notification_type, title, message):
        """Create notification for user"""
        try:
            user = User.objects.get(id=user_id)
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message
            )
        except User.DoesNotExist:
            pass