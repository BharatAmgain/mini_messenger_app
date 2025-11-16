# messenger_app/accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    online_status = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True,
                                        default='profile_pics/default.png')
    last_seen = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    is_verified = models.BooleanField(default=False)

    # Additional profile fields
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not', 'Prefer not to say')
    ], blank=True)

    # Privacy settings
    show_online_status = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    allow_invitations = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)
    show_profile_picture = models.BooleanField(default=True)

    # Notification settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)

    # New notification preference fields
    message_sound = models.BooleanField(default=True)
    message_preview = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    group_mentions_only = models.BooleanField(default=False)
    friend_request_notifications = models.BooleanField(default=True)
    friend_online_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    desktop_notifications = models.BooleanField(default=True)

    # Quiet hours - make null=True to handle disabled state
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00', blank=True, null=True)
    quiet_hours_end = models.TimeField(default='08:00', blank=True, null=True)

    # Security settings
    two_factor_enabled = models.BooleanField(default=False)

    # Appearance settings
    theme = models.CharField(max_length=10, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ], default='auto')

    # Social auth fields
    social_avatar = models.URLField(blank=True, null=True)
    social_provider = models.CharField(max_length=20, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )

    def __str__(self):
        return self.username

    def get_age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                    (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_friend_status(self, other_user):
        """Get friendship status between this user and another user"""
        if self == other_user:
            return 'self'

        # Check if friends
        if Friendship.are_friends(self, other_user):
            return 'friends'

        # Check if friend request sent
        sent_request = FriendRequest.objects.filter(
            from_user=self,
            to_user=other_user,
            status='pending'
        ).first()
        if sent_request:
            return 'request_sent'

        # Check if friend request received
        received_request = FriendRequest.objects.filter(
            from_user=other_user,
            to_user=self,
            status='pending'
        ).first()
        if received_request:
            return 'request_received'

        return 'not_friends'


class SocialAccount(models.Model):
    PROVIDER_CHOICES = [
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='social_accounts')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_id = models.CharField(max_length=255)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['provider', 'provider_id']

    def __str__(self):
        return f"{self.user.username} - {self.provider}"


class Contact(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contacts')
    contact_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='added_by')
    created_at = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['user', 'contact_user']

    def __str__(self):
        return f"{self.user} -> {self.contact_user}"


class Invitation(models.Model):
    INVITATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='account_sent_invitations')
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    invitation_type = models.CharField(max_length=10, choices=INVITATION_TYPES)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['email', 'inviter']
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['phone_number', 'status']),
        ]

    def __str__(self):
        return f"{self.inviter} -> {self.email or self.phone_number} ({self.status})"

    def is_expired(self):
        return timezone.now() > self.expires_at


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

    def accept(self):
        self.status = 'accepted'
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.save()

    @property
    def is_accepted(self):
        return self.status == 'accepted'

    @property
    def is_pending(self):
        return self.status == 'pending'


class Friendship(models.Model):
    user1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships1')
    user2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']

    def __str__(self):
        return f"{self.user1.username} - {self.user2.username}"

    @classmethod
    def are_friends(cls, user1, user2):
        return cls.objects.filter(
            (Q(user1=user1) & Q(user2=user2)) |
            (Q(user1=user2) & Q(user2=user1))
        ).exists()

    @classmethod
    def create_friendship(cls, user1, user2):
        """Create a friendship between two users"""
        if user1.id > user2.id:
            user1, user2 = user2, user1  # Ensure consistent ordering
        return cls.objects.get_or_create(user1=user1, user2=user2)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('friend_request', 'Friend Request'),
        ('invitation', 'Invitation'),
        ('system', 'System'),
        ('group', 'Group Message'),
        ('message_reaction', 'Message Reaction'),
        ('message_edit', 'Message Edited'),
        ('online_status', 'Online Status'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='account_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal')
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField(blank=True, null=True)
    action_buttons = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'notification_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def mark_as_unread(self):
        self.is_read = False
        self.save()

    def archive(self):
        self.is_archived = True
        self.save()

    def unarchive(self):
        self.is_archived = False
        self.save()