# accounts/models.py - COMPLETE FIXED VERSION
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid
from django.utils import timezone
from django.db.models import Q
import os
import random
import string
from django.core.mail import send_mail
from django.conf import settings
import phonenumbers
from phonenumbers import NumberParseException
import requests
import base64


def user_profile_picture_path(instance, filename):
    """File upload path for user profile pictures"""
    ext = filename.split('.')[-1]
    if instance.id:
        filename = f"profile_picture_{instance.id}.{ext}"
    else:
        filename = f"profile_picture_{instance.username}.{ext}"
    return os.path.join('profile_pictures', f'user_{instance.id if instance.id else instance.username}', filename)


class CustomUser(AbstractUser):
    # BASIC FIELDS
    online_status = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        blank=True,
        null=True,
        default=None
    )
    last_seen = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)

    # ✅ FIXED: is_verified as BooleanField ONLY
    is_verified = models.BooleanField(default=False, verbose_name="Email Verified")

    # PROFILE FIELDS
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not', 'Prefer not to say')
    ], blank=True)

    # PRIVACY SETTINGS
    show_online_status = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    allow_invitations = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)
    show_profile_picture = models.BooleanField(default=True)

    # NOTIFICATION SETTINGS
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    message_sound = models.BooleanField(default=True)
    message_preview = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    group_mentions_only = models.BooleanField(default=False)
    friend_request_notifications = models.BooleanField(default=True)
    friend_online_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    desktop_notifications = models.BooleanField(default=True)

    # QUIET HOURS
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)

    # SECURITY & APPEARANCE
    two_factor_enabled = models.BooleanField(default=False)
    theme = models.CharField(max_length=10, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ], default='auto')

    # SOCIAL AUTH
    social_avatar = models.URLField(blank=True, null=True)
    social_provider = models.CharField(max_length=20, blank=True, null=True)

    # GROUPS AND PERMISSIONS - FIXED
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_profile_picture_url(self):
        """Get profile picture URL with fallback"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        elif self.social_avatar:
            return self.social_avatar
        else:
            return '/static/images/default-avatar.png'

    def get_age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                    (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def get_friend_status(self, other_user):
        """Get friendship status between this user and another user"""
        if self == other_user:
            return 'self'

        if Friendship.are_friends(self, other_user):
            return 'friends'

        sent_request = FriendRequest.objects.filter(
            from_user=self,
            to_user=other_user,
            status='pending'
        ).first()
        if sent_request:
            return 'request_sent'

        received_request = FriendRequest.objects.filter(
            from_user=other_user,
            to_user=self,
            status='pending'
        ).first()
        if received_request:
            return 'request_received'

        return 'not_friends'

    def save(self, *args, **kwargs):
        """Override save to ensure is_verified is always a boolean"""
        # Ensure is_verified is a boolean
        if not isinstance(self.is_verified, bool):
            self.is_verified = bool(self.is_verified)

        # Save the model
        super().save(*args, **kwargs)


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
            user1, user2 = user2, user1
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


class OTPVerification(models.Model):
    VERIFICATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('password_reset', 'Password Reset'),
        ('account_verification', 'Account Verification'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_verifications')
    verification_type = models.CharField(max_length=50, choices=VERIFICATION_TYPES)
    otp_code = models.CharField(max_length=6)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_sid = models.CharField(max_length=100, blank=True, null=True)  # ADDED FOR TWILIO SUPPORT

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.verification_type} - {self.otp_code}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def generate_otp(cls, length=6):
        """Generate random OTP code"""
        return ''.join(random.choices(string.digits, k=length))

    @classmethod
    def send_otp_email(cls, email, otp_code, verification_type='account_verification'):
        """Send OTP via email"""
        subject = f"Your Verification Code - {verification_type.replace('_', ' ').title()}"
        message = f"""
        Hello,

        Your verification code is: {otp_code}

        This code will expire in 5 minutes.

        If you didn't request this, please ignore this email.

        Best regards,
        Connect.io Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True

    @classmethod
    def create_otp(cls, user, verification_type='account_verification', email=None, phone_number=None):
        """Create and send OTP"""
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timezone.timedelta(minutes=5)

        otp = cls.objects.create(
            user=user,
            verification_type=verification_type,
            otp_code=otp_code,
            email=email,
            phone_number=phone_number,
            expires_at=expires_at
        )

        if email:
            cls.send_otp_email(email, otp_code, verification_type)

        return otp

    # In accounts/models.py - OTPVerification model
    def verify_otp(self, otp_code):
        """Verify OTP code - FIXED: Properly update user's is_verified"""
        if self.is_expired():
            return False, "OTP has expired"

        if self.is_verified:
            return False, "OTP already used"

        if self.otp_code == otp_code:
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save()

            # CRITICAL FIX: Update user's is_verified status for account verification
            if self.verification_type == 'account_verification':
                # Refresh user object from database to ensure we have latest
                user = CustomUser.objects.get(id=self.user.id)
                user.is_verified = True
                user.save(update_fields=['is_verified'])
                print(f"DEBUG: User {user.username} is_verified updated to True")

            return True, "OTP verified successfully"

        return False, "Invalid OTP code"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verification_sid = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - Password Reset OTP"

    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def create_password_reset_otp(cls, user, email=None, phone_number=None):
        """Create password reset OTP"""
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            email=email,
            phone_number=phone_number,
            expires_at=expires_at
        )

        if email:
            cls.send_password_reset_email(email, otp_code)

        return otp

    @classmethod
    def generate_otp(cls, length=6):
        """Generate random OTP code"""
        return ''.join(random.choices(string.digits, k=length))

    @classmethod
    def send_password_reset_email(cls, email, otp_code):
        """Send password reset OTP via email"""
        subject = "Password Reset Verification Code"
        message = f"""
        Hello,

        You requested to reset your password. Your verification code is:

        {otp_code}

        This code will expire in 10 minutes.

        If you didn't request a password reset, please ignore this email.

        Best regards,
        Connect.io Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

    def verify_and_use(self, otp_code):
        """Verify and mark OTP as used"""
        if self.is_expired():
            return False, "OTP has expired"

        if self.is_used:
            return False, "OTP already used"

        if self.otp_code == otp_code:
            self.is_used = True
            self.save()
            return True, "OTP verified successfully"

        return False, "Invalid OTP code"