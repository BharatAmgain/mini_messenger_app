# messenger_app/chat/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone
import json

User = get_user_model()


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=255, blank=True, null=True)
    group_description = models.TextField(blank=True, null=True)
    group_photo = models.ImageField(upload_to='group_photos/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups', null=True, blank=True)
    admins = models.ManyToManyField(User, related_name='admin_groups', blank=True)

    # Typing indicators
    typing_users = models.ManyToManyField(User, related_name='typing_in_conversations', blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.is_group:
            return f"Group: {self.group_name}"
        else:
            participants = self.participants.all()
            return f"Chat between {', '.join([user.username for user in participants])}"

    def get_display_name(self, current_user):
        """Get display name for conversation"""
        if self.is_group:
            return self.group_name
        else:
            other_user = self.participants.exclude(id=current_user.id).first()
            return other_user.username if other_user else "Unknown User"

    def get_display_photo(self, current_user):
        """Get display photo for conversation"""
        if self.is_group:
            if self.group_photo:
                return self.group_photo.url
            return None
        else:
            other_user = self.participants.exclude(id=current_user.id).first()
            if other_user and other_user.profile_picture:
                return other_user.profile_picture.url
            return None

    def add_participant(self, user, added_by=None):
        """Add a participant to group conversation"""
        if not self.is_group:
            return False

        if user not in self.participants.all():
            self.participants.add(user)
            return True
        return False

    def remove_participant(self, user, removed_by=None):
        """Remove participant from group conversation"""
        if not self.is_group:
            return False

        if user in self.participants.all():
            self.participants.remove(user)
            return True
        return False

    def make_admin(self, user):
        """Make user a group admin"""
        if not self.is_group:
            return False

        if user in self.participants.all() and user not in self.admins.all():
            self.admins.add(user)
            return True
        return False


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)

    # New fields for editing, deleting, and reactions
    is_edited = models.BooleanField(default=False)
    is_unsent = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    reactions = models.JSONField(default=dict, blank=True)  # Store reactions as JSON

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        if self.is_unsent:
            return f"{self.sender.username}: [Message unsent]"
        return f"{self.sender.username}: {self.content[:50]}"

    def add_reaction(self, user, reaction):
        """Add or update reaction from a user"""
        if self.is_unsent:
            return False

        reactions = self.reactions.copy()
        user_id = str(user.id)

        if user_id in reactions:
            # User already reacted, remove reaction if same emoji
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
        """Get summary of reactions (emoji: count)"""
        if not self.reactions:
            return {}

        summary = {}
        for reaction in self.reactions.values():
            summary[reaction] = summary.get(reaction, 0) + 1

        return summary

    def get_user_reaction(self, user):
        """Get user's reaction to this message"""
        return self.reactions.get(str(user.id))


class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='status')
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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_notifications')
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


class GroupInvitation(models.Model):
    group = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_sent_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ), default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['group', 'invited_user']