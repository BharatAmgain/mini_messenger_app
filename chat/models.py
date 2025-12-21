# messenger_app/chat/models.py
from django.db import models
from django.conf import settings  # Use settings.AUTH_USER_MODEL instead
import uuid
import emoji
from django.utils import timezone
import json
from django.db.models import Q
import os


def get_user_model_class():
    """Lazy loading of user model to avoid import issues"""
    from django.contrib.auth import get_user_model
    return get_user_model()


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=255, blank=True, null=True)
    group_description = models.TextField(blank=True, null=True)
    group_photo = models.ImageField(upload_to='group_photos/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='created_groups', null=True, blank=True)
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='admin_groups', blank=True)

    # Typing indicators
    typing_users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          related_name='typing_in_conversations', blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.is_group:
            return f"Group: {self.group_name}"
        else:
            User = get_user_model_class()
            participants = self.participants.all()
            return f"Chat between {', '.join([user.username for user in participants])}"

    def get_display_name(self, current_user):
        if self.is_group:
            return self.group_name
        else:
            other_user = self.participants.exclude(id=current_user.id).first()
            return other_user.username if other_user else "Unknown User"

    def get_display_photo(self, current_user):
        if self.is_group:
            if self.group_photo:
                return self.group_photo.url
            return None
        else:
            other_user = self.participants.exclude(id=current_user.id).first()
            if other_user and hasattr(other_user, 'profile_picture') and other_user.profile_picture:
                return other_user.profile_picture.url
            return None

    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('emoji', 'Emoji'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='message_thumbnails/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)

    # New fields for editing, deleting, and reactions
    is_edited = models.BooleanField(default=False)
    is_unsent = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    reactions = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        if self.is_unsent:
            return f"{self.sender.username}: [Message unsent]"
        return f"{self.sender.username}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        # Auto-detect if content is primarily emoji
        if self.message_type == 'text' and self._is_emoji_message():
            self.message_type = 'emoji'
        super().save(*args, **kwargs)

    def _is_emoji_message(self):
        """Check if message is primarily emoji"""
        if not self.content:
            return False

        # Count emoji characters vs regular characters
        emoji_count = sum(1 for char in self.content if emoji.is_emoji(char))
        total_chars = len(self.content.strip())

        # If more than 70% of characters are emoji or it's a single emoji
        return (emoji_count > 0 and total_chars <= 3) or (total_chars > 0 and emoji_count / total_chars > 0.7)

    def mark_as_read(self, user):
        if not self.is_read and user != self.sender:
            self.is_read = True
            self.read_by.add(user)
            self.save()

    def add_reaction(self, user, reaction):
        if self.is_unsent:
            return False

        reactions = self.reactions.copy()
        user_id = str(user.id)

        if user_id in reactions:
            if reactions[user_id] == reaction:
                del reactions[user_id]
            else:
                reactions[user_id] = reaction
        else:
            reactions[user_id] = reaction

        self.reactions = reactions
        self.save()
        return True

    def get_reaction_summary(self):
        if not self.reactions:
            return {}

        summary = {}
        for reaction in self.reactions.values():
            summary[reaction] = summary.get(reaction, 0) + 1

        return summary

    def get_user_reaction(self, user):
        return self.reactions.get(str(user.id))

    def get_file_extension(self):
        if self.file and self.file.name:
            return os.path.splitext(self.file.name)[1].lower()
        return ''

    def is_image_file(self):
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.get_file_extension() in image_extensions

    def is_video_file(self):
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        return self.get_file_extension() in video_extensions

    def is_audio_file(self):
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        return self.get_file_extension() in audio_extensions

    def get_file_type_display(self):
        if self.message_type != 'text' and self.message_type != 'emoji':
            return self.get_message_type_display()
        return 'Text'

    def get_file_size_display(self):
        if self.file_size:
            bytes = self.file_size
            # Convert bytes to human readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes < 1024.0:
                    return f"{bytes:.1f} {unit}"
                bytes /= 1024.0
        return ''


class UserStatus(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='status')
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.online else 'Offline'}"


class ChatNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('typing', 'Typing Indicator'),
        ('online', 'Online Status'),
        ('group_invite', 'Group Invitation'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='chat_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='chat_notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='chat_notifications')
    content = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"

    def mark_as_read(self):
        self.is_read = True
        self.save()


class GroupInvitation(models.Model):
    group = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='group_sent_invitations')
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='received_invitations')
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ), default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['group', 'invited_user']

    def __str__(self):
        return f"{self.invited_by.username} invited {self.invited_user.username} to {self.group.group_name}"


class BlockedUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='blocked_users')
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'blocked_user']
        verbose_name = 'Blocked User'
        verbose_name_plural = 'Blocked Users'

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"