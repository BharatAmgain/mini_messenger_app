# accounts/models.py - COMPLETE FIXED VERSION
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid
import os
from datetime import timedelta


class CustomUser(AbstractUser):
    """Custom User Model with additional fields"""

    # Additional fields
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say')
        ],
        blank=True
    )

    # Verification fields
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Online status fields - CRITICAL FIX
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    # Privacy settings
    show_online_status = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    allow_invitations = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)
    show_profile_picture = models.BooleanField(default=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    message_sound = models.BooleanField(default=True)
    message_preview = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    group_mentions_only = models.BooleanField(default=False)
    friend_request_notifications = models.BooleanField(default=True)
    friend_online_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    desktop_notifications = models.BooleanField(default=True)

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=10,
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('app', 'Authenticator App')
        ],
        default='email'
    )

    # Social media links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Theme preferences
    theme = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto')
        ],
        default='auto'
    )

    # Account settings
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=False)
    account_locked = models.BooleanField(default=False)
    login_attempts = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Update last_seen when user goes online
        if self.is_online and not self.pk:
            self.last_seen = timezone.now()

        # Ensure username is lowercase
        if self.username:
            self.username = self.username.lower()

        # Ensure email is lowercase
        if self.email:
            self.email = self.email.lower()

        super().save(*args, **kwargs)

    def get_full_name(self):
        """Return the full name of the user."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.username

    def get_profile_picture_url(self):
        """Return the URL of the profile picture or a default."""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-avatar.png'

    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        now = timezone.now().time()
        return self.quiet_hours_start <= now <= self.quiet_hours_end

    def send_verification_email(self):
        """Send verification email to user."""
        if not self.email:
            return False

        subject = 'Verify Your Account'
        verification_url = f"{settings.SITE_DOMAIN}/accounts/verify-email/{self.verification_token}/"
        message = f"""
        Hello {self.username},

        Please verify your email address by clicking the link below:
        {verification_url}

        If you didn't create an account, you can ignore this email.

        Best regards,
        {settings.SITE_NAME} Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False

    def verify_account(self):
        """Mark account as verified."""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])

    def update_online_status(self, is_online):
        """Update user's online status."""
        self.is_online = is_online
        self.last_seen = timezone.now()
        update_fields = ['last_seen']

        if hasattr(self, 'is_online'):
            update_fields.append('is_online')

        self.save(update_fields=update_fields)

    def get_online_status_display(self):
        """Get display text for online status."""
        if self.is_online:
            return "Online"

        if not self.show_online_status:
            return "Hidden"

        time_diff = timezone.now() - self.last_seen
        if time_diff < timedelta(minutes=5):
            return "Just now"
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif time_diff < timedelta(days=1):
            hours = int(time_diff.seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = time_diff.days
            return f"{days} day{'s' if days > 1 else ''} ago"

    @property
    def display_name(self):
        """Display name for the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


# OTP Verification Model
class OTPVerification(models.Model):
    VERIFICATION_TYPES = [
        ('account_verification', 'Account Verification'),
        ('password_reset', 'Password Reset'),
        ('two_factor', 'Two-Factor Authentication'),
        ('phone_verification', 'Phone Verification'),
        ('email_verification', 'Email Verification'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_verifications')
    verification_type = models.CharField(max_length=30, choices=VERIFICATION_TYPES)
    otp_code = models.CharField(max_length=6)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    verification_sid = models.CharField(max_length=100, blank=True, null=True)  # For Twilio
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'verification_type', 'is_verified']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.verification_type} - {self.otp_code}"

    def is_expired(self):
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at

    def verify_otp(self, otp_code):
        """Verify OTP code."""
        if self.is_expired():
            return False, "OTP has expired"

        if self.is_verified:
            return False, "OTP already verified"

        if self.otp_code == otp_code:
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save()
            return True, "OTP verified successfully"

        return False, "Invalid OTP code"

    @classmethod
    def create_otp(cls, user, verification_type, email=None, phone_number=None):
        """Create a new OTP."""
        import random
        import secrets

        # Generate secure OTP
        otp_code = str(random.randint(100000, 999999))

        # Delete any existing OTPs for this user and verification type
        cls.objects.filter(
            user=user,
            verification_type=verification_type,
            is_verified=False
        ).delete()

        # Create new OTP
        otp = cls.objects.create(
            user=user,
            verification_type=verification_type,
            otp_code=otp_code,
            email=email,
            phone_number=phone_number,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        return otp


# Password Reset OTP Model
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    verification_sid = models.CharField(max_length=100, blank=True, null=True)  # For Twilio
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - Password Reset OTP"

    def is_expired(self):
        """Check if OTP has expired."""
        return timezone.now() > self.expires_at

    def verify_and_use(self, otp_code):
        """Verify OTP code and mark as used."""
        if self.is_expired():
            return False, "OTP has expired"

        if self.is_used:
            return False, "OTP already used"

        if self.otp_code == otp_code:
            self.is_used = True
            self.used_at = timezone.now()
            self.save()
            return True, "OTP verified successfully"

        return False, "Invalid OTP code"

    @classmethod
    def create_password_reset_otp(cls, user, email=None):
        """Create a new password reset OTP."""
        import random

        # Generate OTP
        otp_code = str(random.randint(100000, 999999))

        # Delete any existing unused OTPs for this user
        cls.objects.filter(user=user, is_used=False).delete()

        # Create new OTP
        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            email=email,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Send OTP via email
        if email:
            try:
                subject = f'Password Reset OTP - {settings.SITE_NAME}'
                message = f"""
                Hello {user.username},

                Your password reset OTP is: {otp_code}

                This OTP will expire in 10 minutes.

                If you didn't request a password reset, please ignore this email.

                Best regards,
                {settings.SITE_NAME} Team
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending password reset email: {e}")

        return otp


# Notification Model
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('friend_request', 'Friend Request'),
        ('message', 'New Message'),
        ('group_invite', 'Group Invitation'),
        ('system', 'System Notification'),
        ('security', 'Security Alert'),
        ('marketing', 'Marketing'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='account_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_url = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'is_archived']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])


# Friend Request Model
class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_friend_requests')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

    def accept(self):
        """Accept friend request."""
        self.status = 'accepted'
        self.save()

    def reject(self):
        """Reject friend request."""
        self.status = 'rejected'
        self.save()

    def cancel(self):
        """Cancel friend request."""
        self.status = 'cancelled'
        self.save()


# Friendship Model
class Friendship(models.Model):
    user1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships_as_user1')
    user2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friendships_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user1.username} & {self.user2.username}"

    @classmethod
    def are_friends(cls, user1, user2):
        """Check if two users are friends."""
        return cls.objects.filter(
            (models.Q(user1=user1) & models.Q(user2=user2)) |
            (models.Q(user1=user2) & models.Q(user2=user1))
        ).exists()

    @classmethod
    def create_friendship(cls, user1, user2):
        """Create a friendship between two users."""
        # Ensure user1.id < user2.id to maintain consistency
        if user1.id > user2.id:
            user1, user2 = user2, user1

        friendship, created = cls.objects.get_or_create(
            user1=user1,
            user2=user2,
            defaults={'notes': 'Friends'}
        )
        return friendship, created

    @classmethod
    def get_friends(cls, user):
        """Get all friends of a user."""
        friendships = cls.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).select_related('user1', 'user2')

        friends = []
        for friendship in friendships:
            if friendship.user1 == user:
                friends.append(friendship.user2)
            else:
                friends.append(friendship.user1)

        return friends