# messenger_app/accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone


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

    # Notification settings (NEW FIELDS)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)

    # Security settings (NEW FIELDS)
    two_factor_enabled = models.BooleanField(default=False)

    # Appearance settings (NEW FIELDS)
    theme = models.CharField(max_length=10, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ], default='auto')

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


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('friend_request', 'Friend Request'),
        ('invitation', 'Invitation'),
        ('system', 'System'),
        ('group', 'Group Message'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='account_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def get_profile_picture_url(self):
        """Get profile picture URL or return a default"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-avatar.png'