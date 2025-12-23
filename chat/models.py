# chat/models.py - COMPLETE VERSION
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Conversation(models.Model):
    """Represents a conversation between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        through='ConversationParticipant'
    )
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    group_description = models.TextField(blank=True, null=True)
    group_picture = models.ImageField(
        upload_to='group_pictures/',
        blank=True,
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_conversations',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_message_at', '-updated_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        if self.is_group and self.group_name:
            return self.group_name
        participants = list(self.participants.all())
        if len(participants) == 2:
            names = [p.username for p in participants]
            return f"{names[0]} & {names[1]}"
        return f"Group: {self.id}"

    def get_display_name(self, user):
        """Get display name for the conversation from a user's perspective"""
        if self.is_group and self.group_name:
            return self.group_name

        other_users = self.participants.exclude(id=user.id)
        if other_users.count() == 1:
            return other_users.first().username
        else:
            names = [u.username for u in other_users[:3]]
            return ', '.join(names) + (f' and {other_users.count() - 3} more' if other_users.count() > 3 else '')

    def get_other_participants(self, user):
        """Get participants other than the specified user"""
        return self.participants.exclude(id=user.id)

    def get_last_message(self):
        """Get the last message in the conversation"""
        return self.messages.filter(is_deleted=False).order_by('-timestamp').first()

    def update_last_message_time(self):
        """Update the last_message_at field"""
        last_message = self.get_last_message()
        if last_message:
            self.last_message_at = last_message.timestamp
            self.save(update_fields=['last_message_at'])

    def get_unread_count(self, user):
        """Get unread message count for a user"""
        return self.messages.filter(is_deleted=False, is_read=False).exclude(sender=user).count()

    def get_participant_count(self):
        """Get number of participants in the conversation"""
        return self.participants.count()

    def add_participant(self, user, is_admin=False):
        """Add a participant to the conversation"""
        ConversationParticipant.objects.get_or_create(
            conversation=self,
            user=user,
            defaults={'is_admin': is_admin}
        )

    def remove_participant(self, user):
        """Remove a participant from the conversation"""
        ConversationParticipant.objects.filter(conversation=self, user=user).delete()


class ConversationParticipant(models.Model):
    """Intermediate model for conversation participants with additional info"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['conversation', 'user']
        ordering = ['-joined_at']
        verbose_name = 'Conversation Participant'
        verbose_name_plural = 'Conversation Participants'

    def __str__(self):
        return f"{self.user.username} in {self.conversation}"

    def mark_as_read(self):
        """Mark all messages as read for this participant"""
        from django.utils import timezone
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])

        # Mark all unread messages in this conversation as read
        unread_messages = self.conversation.messages.filter(
            is_deleted=False,
            is_read=False
        ).exclude(sender=self.user)

        for message in unread_messages:
            message.is_read = True
            message.save(update_fields=['is_read'])


class Message(models.Model):
    """Represents a message in a conversation"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('location', 'Location'),
        ('sticker', 'Sticker'),
        ('gif', 'GIF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='message_images/', blank=True, null=True)
    video = models.FileField(upload_to='message_videos/', blank=True, null=True)
    audio = models.FileField(upload_to='message_audio/', blank=True, null=True)
    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='message_thumbnails/', blank=True, null=True)

    # Location fields
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True, null=True)
    location_address = models.TextField(blank=True, null=True)

    # Message status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_messages'
    )

    # Read receipts
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_messages',
        through='MessageReadReceipt',
        blank=True
    )

    # Reply to another message
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Reactions
    reactions = models.JSONField(default=dict, blank=True)  # Store as {"user_id": "emoji"}

    # Forwarding
    forwarded_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forwarded_messages'
    )
    is_forwarded = models.BooleanField(default=False)

    # Encryption (if needed)
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.CharField(max_length=255, blank=True, null=True)

    # Metadata
    client_message_id = models.CharField(max_length=100, blank=True, null=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['is_deleted', 'timestamp']),
            models.Index(fields=['message_type', 'timestamp']),
        ]
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        if self.content:
            preview = self.content[:50]
            if len(self.content) > 50:
                preview += "..."
            return f"{self.sender.username}: {preview}"
        elif self.message_type != 'text':
            return f"{self.sender.username}: [{self.get_message_type_display()}]"
        return f"{self.sender.username}: [Empty message]"

    def save(self, *args, **kwargs):
        # Update conversation's last_message_at when saving
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.conversation.last_message_at = self.timestamp
            self.conversation.save(update_fields=['last_message_at'])

            # Create read receipt for sender
            MessageReadReceipt.objects.create(
                message=self,
                user=self.sender,
                read_at=timezone.now()
            )

    def mark_as_read(self, user):
        """Mark message as read by a specific user"""
        receipt, created = MessageReadReceipt.objects.get_or_create(
            message=self,
            user=user,
            defaults={'read_at': timezone.now()}
        )

        if not created and not receipt.read_at:
            receipt.read_at = timezone.now()
            receipt.save(update_fields=['read_at'])

        # Update message read status if all participants have read it
        self.update_read_status()

    def update_read_status(self):
        """Update the is_read field based on read receipts"""
        participant_count = self.conversation.participants.count()
        read_count = self.read_by.count()

        # Message is considered read if all participants (except sender) have read it
        if read_count >= participant_count - 1:  # -1 to exclude sender
            self.is_read = True
            if not self.read_at:
                self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_delivered(self):
        """Mark message as delivered"""
        if not self.delivered_at:
            self.delivered_at = timezone.now()
            self.save(update_fields=['delivered_at'])

    def get_read_receipts(self):
        """Get all read receipts for this message"""
        return self.messagereadreceipt_set.select_related('user').order_by('read_at')

    def get_unread_users(self):
        """Get users who haven't read this message"""
        read_user_ids = self.read_by.values_list('id', flat=True)
        return self.conversation.participants.exclude(id__in=read_user_ids)

    def add_reaction(self, user, emoji):
        """Add a reaction to the message"""
        if 'reactions' not in self.reactions:
            self.reactions = {}

        user_id_str = str(user.id)
        if user_id_str in self.reactions:
            # Remove existing reaction if same emoji
            if self.reactions[user_id_str] == emoji:
                del self.reactions[user_id_str]
            else:
                self.reactions[user_id_str] = emoji
        else:
            self.reactions[user_id_str] = emoji

        self.save(update_fields=['reactions'])
        return self.reactions

    def get_reaction_count(self, emoji=None):
        """Get count of reactions, optionally filtered by emoji"""
        if not self.reactions:
            return 0

        if emoji:
            return sum(1 for r in self.reactions.values() if r == emoji)
        return len(self.reactions)

    def soft_delete(self, user):
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted message"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def edit(self, new_content):
        """Edit the message content"""
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['content', 'is_edited', 'edited_at', 'updated_at'])

    @property
    def file_url(self):
        """Get file URL if available"""
        if self.file:
            return self.file.url
        return None

    @property
    def image_url(self):
        """Get image URL if available"""
        if self.image:
            return self.image.url
        return None

    @property
    def video_url(self):
        """Get video URL if available"""
        if self.video:
            return self.video.url
        return None

    @property
    def audio_url(self):
        """Get audio URL if available"""
        if self.audio:
            return self.audio.url
        return None

    @property
    def is_media(self):
        """Check if message contains media"""
        return bool(self.image or self.video or self.audio or self.file)


class MessageReadReceipt(models.Model):
    """Tracks when messages are read by users"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(default=timezone.now)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['message', 'user']
        ordering = ['read_at']
        verbose_name = 'Message Read Receipt'
        verbose_name_plural = 'Message Read Receipts'

    def __str__(self):
        return f"{self.user.username} read message at {self.read_at}"


class TypingIndicator(models.Model):
    """Tracks when users are typing in conversations"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_indicators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['conversation', 'user']
        ordering = ['-last_updated']
        verbose_name = 'Typing Indicator'
        verbose_name_plural = 'Typing Indicators'

    def __str__(self):
        status = "typing" if self.is_typing else "not typing"
        return f"{self.user.username} is {status} in {self.conversation}"

    def update_typing(self, is_typing, device_id=None):
        """Update typing status"""
        self.is_typing = is_typing
        self.started_at = timezone.now() if is_typing else self.started_at
        if device_id:
            self.device_id = device_id
        self.save()


class OnlineStatus(models.Model):
    """Tracks user online status (redundant with CustomUser but for historical tracking)"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_online_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    device = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)  # web, mobile, desktop
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    connection_count = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Online statuses"
        ordering = ['-last_seen']

    def __str__(self):
        return f"{self.user.username}: {'Online' if self.is_online else 'Offline'}"

    def update_status(self, is_online, device=None, device_type=None, ip_address=None, user_agent=None,
                      session_id=None):
        """Update online status"""
        self.is_online = is_online
        self.last_seen = timezone.now()
        if device:
            self.device = device
        if device_type:
            self.device_type = device_type
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        if session_id:
            self.session_id = session_id

        if is_online:
            self.connection_count += 1

        self.save()

    def get_status_display(self):
        """Get display text for online status"""
        if self.is_online:
            return "Online"

        time_diff = timezone.now() - self.last_seen
        if time_diff.total_seconds() < 300:  # 5 minutes
            return "Just now"
        elif time_diff.total_seconds() < 3600:  # 1 hour
            minutes = int(time_diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif time_diff.total_seconds() < 86400:  # 24 hours
            hours = int(time_diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = time_diff.days
            return f"{days}d ago"


class ChatSettings(models.Model):
    """User-specific chat settings"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_settings')

    # Message preferences
    send_enter = models.BooleanField(default=True)  # Send message on Enter key
    show_preview = models.BooleanField(default=True)  # Show link previews
    auto_download_media = models.BooleanField(default=False)
    media_download_size_limit = models.IntegerField(default=10)  # MB

    # Notification preferences
    message_notifications = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    notification_sound = models.BooleanField(default=True)
    notification_vibrate = models.BooleanField(default=True)
    show_notification_content = models.BooleanField(default=True)

    # Privacy
    show_last_seen = models.BooleanField(default=True)
    show_read_receipts = models.BooleanField(default=True)
    show_typing_indicator = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=True)
    block_unknown_senders = models.BooleanField(default=False)

    # Theme
    theme = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto')
        ],
        default='auto'
    )

    # Chat background
    chat_background = models.ImageField(upload_to='chat_backgrounds/', blank=True, null=True)
    chat_background_color = models.CharField(max_length=7, default='#ffffff')  # Hex color

    # Font size
    font_size = models.CharField(
        max_length=10,
        choices=[
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large'),
            ('xlarge', 'Extra Large')
        ],
        default='medium'
    )

    # Auto-delete messages
    auto_delete_messages = models.BooleanField(default=False)
    auto_delete_after = models.IntegerField(default=7)  # Days

    # Data saving
    low_data_mode = models.BooleanField(default=False)
    compress_images = models.BooleanField(default=False)
    reduce_animation = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Chat Settings'
        verbose_name_plural = 'Chat Settings'

    def __str__(self):
        return f"Chat settings for {self.user.username}"


class ArchivedConversation(models.Model):
    """Archived conversations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='archived_conversations')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='archived_by')
    archived_at = models.DateTimeField(auto_now_add=True)
    muted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'conversation']
        ordering = ['-archived_at']
        verbose_name = 'Archived Conversation'
        verbose_name_plural = 'Archived Conversations'

    def __str__(self):
        return f"{self.user.username} archived {self.conversation}"


class PinnedConversation(models.Model):
    """Pinned conversations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pinned_conversations')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='pinned_by')
    pinned_at = models.DateTimeField(auto_now_add=True)
    position = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'conversation']
        ordering = ['position', '-pinned_at']
        verbose_name = 'Pinned Conversation'
        verbose_name_plural = 'Pinned Conversations'

    def __str__(self):
        return f"{self.user.username} pinned {self.conversation}"


class BlockedUser(models.Model):
    """Blocked users"""
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_by')
    blocked_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['blocker', 'blocked']
        ordering = ['-blocked_at']
        verbose_name = 'Blocked User'
        verbose_name_plural = 'Blocked Users'

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"


class ChatCall(models.Model):
    """Chat call history"""
    CALL_TYPES = [
        ('audio', 'Audio Call'),
        ('video', 'Video Call'),
    ]

    CALL_STATUS = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='calls')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='audio')
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')

    # Participants
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='made_calls')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_calls')

    # Call details
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # in seconds

    # Call quality metrics
    quality_score = models.FloatField(null=True, blank=True)
    has_video = models.BooleanField(default=False)
    has_audio = models.BooleanField(default=True)

    # Technical details
    call_sid = models.CharField(max_length=100, blank=True, null=True)  # For Twilio
    room_sid = models.CharField(max_length=100, blank=True, null=True)
    recording_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat Call'
        verbose_name_plural = 'Chat Calls'

    def __str__(self):
        return f"{self.caller.username} to {self.recipient.username} ({self.call_type})"

    def start_call(self):
        """Start the call"""
        self.started_at = timezone.now()
        self.status = 'ringing'
        self.save(update_fields=['started_at', 'status'])

    def answer_call(self):
        """Answer the call"""
        self.status = 'answered'
        self.save(update_fields=['status'])

    def end_call(self, duration=0):
        """End the call"""
        self.ended_at = timezone.now()
        self.duration = duration
        self.status = 'completed'
        self.save(update_fields=['ended_at', 'duration', 'status'])

    def miss_call(self):
        """Mark as missed"""
        self.status = 'missed'
        self.save(update_fields=['status'])

    def reject_call(self):
        """Reject the call"""
        self.status = 'rejected'
        self.save(update_fields=['status'])

    def fail_call(self, reason=""):
        """Mark as failed"""
        self.status = 'failed'
        self.save(update_fields=['status'])

    @property
    def is_ongoing(self):
        """Check if call is ongoing"""
        return self.status in ['ringing', 'answered']

    @property
    def formatted_duration(self):
        """Get formatted duration"""
        if not self.duration:
            return "0s"

        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class ChatCallParticipant(models.Model):
    """Call participants"""
    call = models.ForeignKey(ChatCall, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_video_on = models.BooleanField(default=False)
    connection_quality = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ['call', 'user']
        verbose_name = 'Call Participant'
        verbose_name_plural = 'Call Participants'

    def __str__(self):
        return f"{self.user.username} in call {self.call.id}"

    def join_call(self):
        """Join the call"""
        self.joined_at = timezone.now()
        self.save(update_fields=['joined_at'])

    def leave_call(self):
        """Leave the call"""
        self.left_at = timezone.now()
        self.save(update_fields=['left_at'])


class ChatNotification(models.Model):
    """Chat-specific notifications"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('call', 'Incoming Call'),
        ('group_invite', 'Group Invitation'),
        ('mention', 'Mention'),
        ('reaction', 'Message Reaction'),
        ('reply', 'Message Reply'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    related_message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    related_call = models.ForeignKey(ChatCall, on_delete=models.CASCADE, null=True, blank=True)

    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'is_archived']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Chat Notification'
        verbose_name_plural = 'Chat Notifications'

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])