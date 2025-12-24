# chat/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from django.db.models import Q
import os


class Conversation(models.Model):
    """Represents a conversation between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    group_description = models.TextField(blank=True, null=True)
    group_photo = models.ImageField(
        upload_to='group_photos/',
        blank=True,
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    typing_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='typing_in_conversations',
        blank=True
    )

    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='admin_of_groups',
        blank=True
    )

    is_archived = models.BooleanField(default=False)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_conversations'
    )
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['updated_at']),
            models.Index(fields=['is_group', 'is_archived']),
        ]

    def __str__(self):
        if self.is_group and self.group_name:
            return self.group_name
        participants = list(self.participants.all())
        if len(participants) == 2:
            names = [p.username for p in participants]
            return f"{names[0]} & {names[1]}"
        return f"Conversation: {self.id}"

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
        return self.messages.order_by('-timestamp').first()

    def get_unread_count(self, user):
        """Get unread message count for a user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def add_participant(self, user, added_by=None):
        """Add a participant to the conversation"""
        if user not in self.participants.all():
            self.participants.add(user)

            # If this is a group, create a notification
            if self.is_group and added_by:
                from accounts.models import Notification
                Notification.objects.create(
                    user=user,
                    notification_type='group_invite',
                    title="Group Invitation",
                    message=f"You were added to group '{self.group_name}' by {added_by.username}",
                    related_url=f"/chat/{self.id}/"
                )
            return True
        return False

    def remove_participant(self, user, removed_by=None):
        """Remove a participant from the conversation"""
        if user in self.participants.all():
            self.participants.remove(user)

            # Remove from admins if they were an admin
            if user in self.admins.all():
                self.admins.remove(user)

            # If this is a group and there's a system message needed
            if self.is_group and removed_by:
                Message.objects.create(
                    conversation=self,
                    sender=removed_by,
                    content=f"{user.username} was removed from the group by {removed_by.username}",
                    is_read=True
                )
            return True
        return False

    def get_participant_count(self):
        """Get number of participants"""
        return self.participants.count()


class Message(models.Model):
    """Represents a message in a conversation"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('emoji', 'Emoji'),
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

    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_unsent = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)

    reactions = models.JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    starred_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='starred_messages',
        blank=True
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['is_read', 'timestamp']),
        ]

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
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update conversation's updated_at
            self.conversation.updated_at = self.timestamp
            self.conversation.save(update_fields=['updated_at'])

    def add_reaction(self, user, emoji):
        """Add a reaction to the message"""
        if 'reactions' not in self.reactions:
            self.reactions = {}

        user_id_str = str(user.id)
        if user_id_str in self.reactions:
            if self.reactions[user_id_str] == emoji:
                # Remove reaction if same emoji
                del self.reactions[user_id_str]
            else:
                # Update reaction
                self.reactions[user_id_str] = emoji
        else:
            # Add new reaction
            self.reactions[user_id_str] = emoji

        self.save(update_fields=['reactions'])
        return self.reactions

    def get_reaction_summary(self):
        """Get summary of reactions"""
        if not self.reactions:
            return {}

        summary = {}
        for emoji in self.reactions.values():
            summary[emoji] = summary.get(emoji, 0) + 1

        return summary

    def get_user_reaction(self, user):
        """Get user's reaction to this message"""
        if not self.reactions:
            return None
        return self.reactions.get(str(user.id))

    def edit(self, new_content):
        """Edit the message content"""
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['content', 'is_edited', 'edited_at'])

    def mark_as_read(self, user):
        """Mark message as read by a user"""
        if not self.is_read and user != self.sender:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def is_image_file(self):
        """Check if the file is an image"""
        if not self.file:
            return False
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        return any(self.file.name.lower().endswith(ext) for ext in image_extensions)

    def is_video_file(self):
        """Check if the file is a video"""
        if not self.file:
            return False
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.3gp']
        return any(self.file.name.lower().endswith(ext) for ext in video_extensions)

    def is_audio_file(self):
        """Check if the file is an audio"""
        if not self.file:
            return False
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma']
        return any(self.file.name.lower().endswith(ext) for ext in audio_extensions)

    def get_file_size_display(self):
        """Get human-readable file size"""
        if not self.file_size:
            return "0 B"

        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_file_extension(self):
        """Get file extension"""
        if not self.file_name:
            return ''
        return os.path.splitext(self.file_name)[1].lower()

    def delete_file(self):
        """Delete the associated file"""
        if self.file:
            self.file.delete(save=False)
            self.file = None
            self.file_name = None
            self.file_size = None
            self.save(update_fields=['file', 'file_name', 'file_size'])


class UserStatus(models.Model):
    """User online/typing status for chat"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('typing', 'Typing...'),
        ('away', 'Away'),
        ('busy', 'Busy'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_status'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(auto_now=True)
    is_typing_in = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='typing_users_status'
    )
    custom_status = models.CharField(max_length=100, blank=True, null=True)
    status_emoji = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        verbose_name_plural = "User statuses"
        indexes = [
            models.Index(fields=['status', 'last_seen']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.status}"

    def update_status(self, status, custom_status=None, status_emoji=None):
        """Update user status"""
        self.status = status
        self.last_seen = timezone.now()

        if custom_status is not None:
            self.custom_status = custom_status

        if status_emoji is not None:
            self.status_emoji = status_emoji

        self.save()

    def set_typing(self, conversation=None):
        """Set user as typing in a conversation"""
        self.status = 'typing'
        self.is_typing_in = conversation
        self.last_seen = timezone.now()
        self.save()

    def clear_typing(self):
        """Clear typing status"""
        if self.status == 'typing':
            self.status = 'online'
            self.is_typing_in = None
            self.save()


class ChatNotification(models.Model):
    """Chat-specific notifications"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('call', 'Incoming Call'),
        ('group_invite', 'Group Invitation'),
        ('mention', 'Mention'),
        ('reaction', 'Message Reaction'),
        ('reply', 'Message Reply'),
        ('system', 'System Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def archive(self):
        """Archive notification"""
        self.is_archived = True
        self.save(update_fields=['is_archived'])


class GroupInvitation(models.Model):
    """Group invitations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    # Track if notification was sent
    notification_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ['conversation', 'invited_user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invited_user', 'status', 'created_at']),
            models.Index(fields=['conversation', 'status']),
        ]

    def __str__(self):
        return f"{self.invited_by.username} invited {self.invited_user.username} to {self.conversation}"

    def accept(self):
        """Accept the invitation"""
        if self.status == 'pending':
            self.status = 'accepted'
            self.responded_at = timezone.now()
            self.save()

            # Add user to conversation
            self.conversation.participants.add(self.invited_user)

            # Create system message
            Message.objects.create(
                conversation=self.conversation,
                sender=self.invited_user,
                content=f"{self.invited_user.username} joined the group",
                is_read=True
            )

            # Create notification for inviter
            ChatNotification.objects.create(
                user=self.invited_by,
                notification_type='group_invite',
                title="Group Invitation Accepted",
                message=f"{self.invited_user.username} accepted your invitation to join {self.conversation.group_name}",
                related_conversation=self.conversation
            )

            return True
        return False

    def reject(self):
        """Reject the invitation"""
        if self.status == 'pending':
            self.status = 'rejected'
            self.responded_at = timezone.now()
            self.save()

            # Create notification for inviter
            ChatNotification.objects.create(
                user=self.invited_by,
                notification_type='group_invite',
                title="Group Invitation Rejected",
                message=f"{self.invited_user.username} declined your invitation to join {self.conversation.group_name}",
                related_conversation=self.conversation
            )

            return True
        return False

    def cancel(self):
        """Cancel the invitation"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.responded_at = timezone.now()
            self.save()

            # Create notification for invited user
            ChatNotification.objects.create(
                user=self.invited_user,
                notification_type='group_invite',
                title="Group Invitation Cancelled",
                message=f"Invitation to join {self.conversation.group_name} was cancelled",
                related_conversation=self.conversation
            )

            return True
        return False

    def send_notification(self):
        """Send notification for this invitation"""
        if not self.notification_sent:
            ChatNotification.objects.create(
                user=self.invited_user,
                notification_type='group_invite',
                title="Group Invitation",
                message=f"You are invited to join {self.conversation.group_name} by {self.invited_by.username}",
                related_conversation=self.conversation
            )
            self.notification_sent = True
            self.save(update_fields=['notification_sent'])
            return True
        return False

    def is_expired(self):
        """Check if invitation is expired (7 days)"""
        if self.status != 'pending':
            return False
        return timezone.now() > self.created_at + timedelta(days=7)


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
        ('busy', 'Busy'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='calls'
    )
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='audio')
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')

    caller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='made_calls'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_calls'
    )

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # in seconds

    # Call quality metrics
    call_quality = models.CharField(max_length=20, blank=True, null=True)
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True, null=True)

    # Additional metadata
    caller_ip = models.GenericIPAddressField(blank=True, null=True)
    recipient_ip = models.GenericIPAddressField(blank=True, null=True)
    call_direction = models.CharField(
        max_length=10,
        choices=[('incoming', 'Incoming'), ('outgoing', 'Outgoing')],
        default='outgoing'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['caller', 'created_at']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.caller.username} to {self.recipient.username} ({self.call_type}) - {self.status}"

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

    def start_call(self):
        """Mark call as started"""
        if self.status in ['initiated', 'ringing']:
            self.status = 'answered'
            self.started_at = timezone.now()
            self.save(update_fields=['status', 'started_at'])
            return True
        return False

    def end_call(self, status='completed'):
        """End the call"""
        if self.status == 'answered':
            self.status = status
            self.ended_at = timezone.now()

            # Calculate duration if call was answered
            if self.started_at:
                self.duration = int((self.ended_at - self.started_at).total_seconds())

            self.save(update_fields=['status', 'ended_at', 'duration'])

            # Create call ended message
            if status == 'completed':
                duration_display = self.formatted_duration
                call_type_display = "Video call" if self.call_type == 'video' else "Voice call"
                Message.objects.create(
                    conversation=self.conversation,
                    sender=self.caller,
                    content=f"{call_type_display} ended ({duration_display})",
                    is_read=True
                )

            return True
        return False

    def mark_as_missed(self):
        """Mark call as missed"""
        if self.status in ['initiated', 'ringing']:
            self.status = 'missed'
            self.ended_at = timezone.now()
            self.save(update_fields=['status', 'ended_at'])
            return True
        return False

    def mark_as_rejected(self):
        """Mark call as rejected"""
        if self.status in ['initiated', 'ringing']:
            self.status = 'rejected'
            self.ended_at = timezone.now()
            self.save(update_fields=['status', 'ended_at'])
            return True
        return False

    def get_call_summary(self):
        """Get summary of the call"""
        summary = {
            'id': str(self.id),
            'call_type': self.call_type,
            'status': self.status,
            'caller': self.caller.username,
            'recipient': self.recipient.username,
            'duration': self.formatted_duration,
            'created_at': self.created_at,
        }

        if self.started_at:
            summary['started_at'] = self.started_at
        if self.ended_at:
            summary['ended_at'] = self.ended_at

        return summary


class MessageReaction(models.Model):
    """Detailed message reactions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='detailed_reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reactions'
    )
    reaction = models.CharField(max_length=10)  # Emoji character
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['message', 'user']
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['message', 'user']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted with {self.reaction} to message {self.message.id}"


class PinnedMessage(models.Model):
    """Pinned messages in conversations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='pinned_messages'
    )
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='pinned_message'
    )
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pinned_messages'
    )
    pinned_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)  # Optional note about why it's pinned

    class Meta:
        ordering = ['-pinned_at']
        indexes = [
            models.Index(fields=['conversation', 'pinned_at']),
        ]

    def __str__(self):
        return f"Pinned message in {self.conversation} by {self.pinned_by.username}"


class ConversationSettings(models.Model):
    """User-specific settings for conversations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_settings'
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='user_settings'
    )

    # Notification settings
    mute_notifications = models.BooleanField(default=False)
    custom_notification_sound = models.CharField(max_length=100, blank=True, null=True)
    hide_preview = models.BooleanField(default=False)

    # Display settings
    custom_nickname = models.CharField(max_length=50, blank=True, null=True)
    custom_color = models.CharField(max_length=7, blank=True, null=True)  # Hex color

    # Privacy settings
    archive_conversation = models.BooleanField(default=False)
    hide_conversation = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'conversation']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'conversation']),
            models.Index(fields=['user', 'archive_conversation']),
        ]

    def __str__(self):
        return f"Settings for {self.user.username} in {self.conversation}"


class ChatMedia(models.Model):
    """Media files in chat"""
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('sticker', 'Sticker'),
        ('gif', 'GIF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='media_files',
        null=True,
        blank=True
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='chat_media/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    mime_type = models.CharField(max_length=100)

    # Image/Video specific fields
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # in seconds for video/audio

    # Thumbnail for videos and large images
    thumbnail = models.ImageField(upload_to='chat_media/thumbnails/', null=True, blank=True)

    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_media'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Privacy/Deletion
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_media'
    )

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['conversation', 'media_type', 'uploaded_at']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
        ]

    def __str__(self):
        return f"{self.media_type}: {self.file_name}"

    def get_file_size_display(self):
        """Get human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def delete_file(self):
        """Delete the actual file from storage"""
        if self.file:
            self.file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)

    def mark_as_deleted(self, user):
        """Mark media as deleted"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


# Signal handlers
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """Create chat notification for new messages"""
    if created and not instance.is_unsent:
        # Create notifications for other participants
        for participant in instance.conversation.participants.exclude(id=instance.sender.id):
            # Check if participant has muted this conversation
            settings = ConversationSettings.objects.filter(
                user=participant,
                conversation=instance.conversation,
                mute_notifications=True
            ).exists()

            if not settings:
                ChatNotification.objects.create(
                    user=participant,
                    notification_type='message',
                    title=f"New message from {instance.sender.username}",
                    message=instance.content[:100] if instance.content else f"Sent a {instance.message_type}",
                    related_conversation=instance.conversation,
                    related_message=instance
                )


@receiver(post_save, sender=GroupInvitation)
def send_group_invitation_notification(sender, instance, created, **kwargs):
    """Send notification for new group invitations"""
    if created and instance.status == 'pending':
        instance.send_notification()


@receiver(m2m_changed, sender=Conversation.participants.through)
def conversation_participants_changed(sender, instance, action, pk_set, **kwargs):
    """Handle conversation participants changes"""
    if action == "post_add":
        # New participants added
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                # Create conversation settings for new participant
                ConversationSettings.objects.get_or_create(
                    user=user,
                    conversation=instance
                )
            except User.DoesNotExist:
                pass


@receiver(post_save, sender=ChatCall)
def create_call_notification(sender, instance, created, **kwargs):
    """Create notification for new calls"""
    if created:
        call_type = "Video" if instance.call_type == 'video' else "Voice"
        ChatNotification.objects.create(
            user=instance.recipient,
            notification_type='call',
            title=f"Incoming {call_type} Call",
            message=f"{instance.caller.username} is calling you",
            related_conversation=instance.conversation
        )


@receiver(post_delete, sender=ChatMedia)
def delete_media_file(sender, instance, **kwargs):
    """Delete actual media files when record is deleted"""
    instance.delete_file()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_status(sender, instance, created, **kwargs):
    """Create UserStatus when a new user is created"""
    if created:
        UserStatus.objects.create(user=instance)


@receiver(post_save, sender=Conversation)
def create_default_conversation_settings(sender, instance, created, **kwargs):
    """Create default conversation settings for all participants when conversation is created"""
    if created:
        for participant in instance.participants.all():
            ConversationSettings.objects.get_or_create(
                user=participant,
                conversation=instance
            )