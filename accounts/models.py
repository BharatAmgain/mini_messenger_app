# accounts/models.py - COMPLETE FIXED VERSION WITH ALL VALIDATION
import secrets
import string
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from django.db.models import Q
import re


class CustomUser(AbstractUser):
    """Extended User model with additional fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Profile fields
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        default='profile_pictures/default.png'
    )
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], blank=True)

    # Social media links
    facebook_url = models.URLField(max_length=255, blank=True, null=True)
    twitter_url = models.URLField(max_length=200, blank=True)
    instagram_url = models.URLField(max_length=200, blank=True)
    linkedin_url = models.URLField(max_length=200, blank=True)

    # Online status
    online_status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('away', 'Away'),
            ('busy', 'Busy'),
            ('invisible', 'Invisible')
        ],
        default='offline'
    )
    last_seen = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)

    # Account verification
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)

    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)

    # Privacy settings
    show_online_status = models.BooleanField(default=True)
    allow_message_requests = models.BooleanField(default=True)
    allow_calls = models.BooleanField(default=True)
    allow_invitations = models.BooleanField(default=True)
    show_last_seen = models.BooleanField(default=True)
    show_profile_picture = models.BooleanField(default=True)

    # Notification preferences
    message_notifications = models.BooleanField(default=True)
    message_sound = models.BooleanField(default=True)
    message_preview = models.BooleanField(default=True)
    group_notifications = models.BooleanField(default=True)
    group_mentions_only = models.BooleanField(default=False)
    friend_request_notifications = models.BooleanField(default=True)
    friend_online_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=True)

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

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

    # Additional metadata
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    # Social auth fields
    google_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return full name if available, otherwise username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def get_profile_picture_url(self):
        """Get URL for profile picture"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-profile.png'

    def update_online_status(self, status='online'):
        """Update user's online status"""
        self.online_status = status
        self.is_online = (status == 'online')
        self.last_seen = timezone.now()
        self.save(update_fields=['online_status', 'is_online', 'last_seen'])

    def is_currently_online(self):
        """Check if user is currently online"""
        if self.online_status == 'online':
            return True
        elif self.show_last_seen:
            return (timezone.now() - self.last_seen) < timedelta(minutes=5)
        return False

    def get_friend_status(self, other_user):
        """Get friendship status with another user"""
        if self == other_user:
            return 'self'

        if Friendship.are_friends(self, other_user):
            return 'friends'

        sent_request = FriendRequest.objects.filter(
            from_user=self,
            to_user=other_user,
            status='pending'
        ).exists()

        if sent_request:
            return 'request_sent'

        received_request = FriendRequest.objects.filter(
            from_user=other_user,
            to_user=self,
            status='pending'
        ).exists()

        if received_request:
            return 'request_received'

        return 'not_friends'

    def get_mutual_friends(self, other_user):
        """Get mutual friends between two users"""
        user_friends = Friendship.get_friends(self)
        other_friends = Friendship.get_friends(other_user)

        mutual_friends = set(user_friends) & set(other_friends)
        return list(mutual_friends)

    def get_friend_count(self):
        """Get number of friends"""
        return Friendship.get_friend_count(self)

    def clean(self):
        """Custom validation with PostgreSQL UUID fix"""
        super().clean()  # Run parent validation first

        errors = {}

        # Email validation - case-insensitive check
        if self.email:
            self.email = self.email.strip().lower()

            # Email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                errors['email'] = 'Please enter a valid email address.'

            # Email uniqueness validation
            query = CustomUser.objects.filter(email__iexact=self.email)
            if self.pk:  # For existing users
                query = query.exclude(pk=self.pk)

            if query.exists():
                errors['email'] = 'This email is already registered.'

        # Phone number validation
        if self.phone_number:
            self.phone_number = self.phone_number.strip()

            # Basic phone validation
            if not self.phone_number.startswith('+'):
                errors['phone_number'] = 'Phone number must start with + for international format.'
            else:
                # Remove + and check if rest contains only digits and spaces
                cleaned = self.phone_number[1:].replace(' ', '').replace('-', '')
                if not cleaned.isdigit():
                    errors['phone_number'] = 'Phone number can only contain digits, spaces, and hyphens after +.'

            # Phone uniqueness validation (only if valid format)
            if 'phone_number' not in errors:
                query = CustomUser.objects.filter(phone_number=self.phone_number)
                if self.pk:  # For existing users
                    query = query.exclude(pk=self.pk)

                if query.exists():
                    errors['phone_number'] = 'This phone number is already registered.'

        # Username validation
        if self.username:
            self.username = self.username.strip()

            if len(self.username) < 3:
                errors['username'] = 'Username must be at least 3 characters long.'
            elif len(self.username) > 30:
                errors['username'] = 'Username cannot be longer than 30 characters.'
            elif not re.match(r'^[a-zA-Z0-9._]+$', self.username):
                errors['username'] = 'Username can only contain letters, numbers, underscores, and periods.'
            elif self.username.startswith('.') or self.username.endswith('.'):
                errors['username'] = 'Username cannot start or end with a period.'
            elif '..' in self.username:
                errors['username'] = 'Username cannot contain consecutive periods.'

        # Date of birth validation
        if self.date_of_birth:
            if self.date_of_birth > timezone.now().date():
                errors['date_of_birth'] = 'Date of birth cannot be in the future.'
            else:
                # Check if user is at least 13 years old
                age = (timezone.now().date() - self.date_of_birth).days / 365.25
                if age < 13:
                    errors['date_of_birth'] = 'You must be at least 13 years old to register.'
                elif age > 150:
                    errors['date_of_birth'] = 'Please enter a valid date of birth.'

        # Bio validation
        if self.bio and len(self.bio) > 500:
            errors['bio'] = 'Bio cannot be longer than 500 characters.'

        # Website validation
        if self.website:
            if not self.website.startswith(('http://', 'https://')):
                errors['website'] = 'Website must start with http:// or https://'
            elif len(self.website) > 200:
                errors['website'] = 'Website URL is too long.'

        # Quiet hours validation
        if self.quiet_hours_enabled:
            if not self.quiet_hours_start or not self.quiet_hours_end:
                errors['quiet_hours_enabled'] = 'Both start and end times are required for quiet hours.'
            elif self.quiet_hours_start >= self.quiet_hours_end:
                errors['quiet_hours_start'] = 'Start time must be before end time.'
                errors['quiet_hours_end'] = 'End time must be after start time.'

        # Social media URL validation
        social_fields = {
            'facebook_url': 'Facebook',
            'twitter_url': 'Twitter',
            'instagram_url': 'Instagram',
            'linkedin_url': 'LinkedIn'
        }

        for field, platform in social_fields.items():
            url = getattr(self, field, '')
            if url:
                if not url.startswith(('http://', 'https://')):
                    errors[field] = f'{platform} URL must start with http:// or https://'
                elif len(url) > 200:
                    errors[field] = f'{platform} URL is too long.'

        # Gender validation
        if self.gender and self.gender not in ['male', 'female', 'other', 'prefer_not_to_say']:
            errors['gender'] = 'Please select a valid gender option.'

        # Location validation
        if self.location and len(self.location) > 100:
            errors['location'] = 'Location cannot be longer than 100 characters.'

        # First name and last name validation
        if self.first_name and len(self.first_name) > 50:
            errors['first_name'] = 'First name cannot be longer than 50 characters.'

        if self.last_name and len(self.last_name) > 50:
            errors['last_name'] = 'Last name cannot be longer than 50 characters.'

        # Google ID validation (if provided)
        if self.google_id and len(self.google_id) > 100:
            errors['google_id'] = 'Google ID is too long.'

        # Raise validation errors if any
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to handle validation and updates"""
        # Run full validation before saving
        self.full_clean()

        # Set date_joined for new users
        if not self.pk:
            self.date_joined = timezone.now()

            # Set verification_date if user is verified on creation
            if self.is_verified and not self.verification_date:
                self.verification_date = timezone.now()
        else:
            # If is_verified changed from False to True, set verification_date
            try:
                old_user = CustomUser.objects.get(pk=self.pk)
                if not old_user.is_verified and self.is_verified and not self.verification_date:
                    self.verification_date = timezone.now()
            except CustomUser.DoesNotExist:
                pass

        # Ensure email is lowercase for consistency
        if self.email:
            self.email = self.email.lower().strip()

        # Remove whitespace from phone number
        if self.phone_number:
            self.phone_number = self.phone_number.strip()

        super().save(*args, **kwargs)


class Notification(models.Model):
    """Notification model for user notifications"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('friend_request', 'Friend Request'),
        ('friend_online', 'Friend Online'),
        ('group_invite', 'Group Invitation'),
        ('system', 'System Notification'),
        ('marketing', 'Marketing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='account_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def clean(self):
        """Validate notification data"""
        errors = {}

        if not self.title:
            errors['title'] = 'Title is required.'
        elif len(self.title) > 200:
            errors['title'] = 'Title cannot be longer than 200 characters.'

        if not self.message:
            errors['message'] = 'Message is required.'

        if self.related_url and len(self.related_url) > 500:
            errors['related_url'] = 'Related URL is too long.'

        if errors:
            raise ValidationError(errors)

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.save(update_fields=['is_read'])

    def archive(self):
        """Archive notification"""
        self.is_archived = True
        self.save(update_fields=['is_archived'])


class FriendRequest(models.Model):
    """Friend request model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests'
    )
    to_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_friend_requests'
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.status}"

    def clean(self):
        """Validate friend request"""
        errors = {}

        # Cannot send friend request to self
        if self.from_user == self.to_user:
            errors['to_user'] = 'You cannot send a friend request to yourself.'

        # Check if friendship already exists
        if self.pk is None:  # Only check for new requests
            if Friendship.are_friends(self.from_user, self.to_user):
                errors['to_user'] = 'You are already friends with this user.'

            # Check for existing pending request
            existing_request = FriendRequest.objects.filter(
                from_user=self.from_user,
                to_user=self.to_user,
                status='pending'
            ).exists()
            if existing_request:
                errors['to_user'] = 'A pending friend request already exists.'

        # Validate message length
        if self.message and len(self.message) > 1000:
            errors['message'] = 'Message cannot be longer than 1000 characters.'

        if errors:
            raise ValidationError(errors)

    def accept(self):
        """Accept friend request"""
        self.status = 'accepted'
        self.save(update_fields=['status', 'updated_at'])
        return True

    def reject(self):
        """Reject friend request"""
        self.status = 'rejected'
        self.save(update_fields=['status', 'updated_at'])
        return True

    def cancel(self):
        """Cancel friend request"""
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])
        return True

    def is_active(self):
        """Check if request is active (pending)"""
        return self.status == 'pending'


class Friendship(models.Model):
    """Friendship model to represent mutual friendships"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='friendships_as_user1'
    )
    user2 = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='friendships_as_user2'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user1} <-> {self.user2}"

    def clean(self):
        """Validate friendship"""
        # Cannot be friends with self
        if self.user1 == self.user2:
            raise ValidationError('A user cannot be friends with themselves.')

    @classmethod
    def create_friendship(cls, user1, user2):
        """Create a mutual friendship"""
        # Ensure consistent ordering
        if user1.id > user2.id:
            user1, user2 = user2, user1

        friendship, created = cls.objects.get_or_create(
            user1=user1,
            user2=user2
        )
        return friendship, created

    @classmethod
    def are_friends(cls, user1, user2):
        """Check if two users are friends"""
        return cls.objects.filter(
            (Q(user1=user1) & Q(user2=user2)) |
            (Q(user1=user2) & Q(user2=user1))
        ).exists()

    @classmethod
    def get_friends(cls, user):
        """Get all friends of a user"""
        friendships = cls.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).select_related('user1', 'user2')

        friends = []
        for friendship in friendships:
            if friendship.user1 == user:
                friends.append(friendship.user2)
            else:
                friends.append(friendship.user1)

        return friends

    @classmethod
    def get_friend_count(cls, user):
        """Get number of friends for a user"""
        return cls.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).count()

    @classmethod
    def remove_friendship(cls, user1, user2):
        """Remove friendship between two users"""
        cls.objects.filter(
            (Q(user1=user1) & Q(user2=user2)) |
            (Q(user1=user2) & Q(user2=user1))
        ).delete()


class OTPVerification(models.Model):
    """OTP verification for various purposes"""
    VERIFICATION_TYPES = [
        ('account_verification', 'Account Verification'),
        ('phone_verification', 'Phone Verification'),
        ('email_verification', 'Email Verification'),
        ('two_factor', 'Two-Factor Authentication'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_verifications')
    verification_type = models.CharField(max_length=30, choices=VERIFICATION_TYPES)
    otp_code = models.CharField(max_length=6)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    verification_sid = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.verification_type} - {self.otp_code}"

    def clean(self):
        """Validate OTP data"""
        if not self.otp_code or len(self.otp_code) != 6:
            raise ValidationError({'otp_code': 'OTP code must be exactly 6 digits.'})

        if not self.otp_code.isdigit():
            raise ValidationError({'otp_code': 'OTP code must contain only digits.'})

    @classmethod
    def create_otp(cls, user, verification_type, email=None, phone_number=None):
        """Create a new OTP"""
        otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        expires_at = timezone.now() + timedelta(minutes=10)

        otp = cls.objects.create(
            user=user,
            verification_type=verification_type,
            otp_code=otp_code,
            email=email,
            phone_number=phone_number,
            expires_at=expires_at
        )

        return otp

    def verify_otp(self, otp_code):
        """Verify OTP code"""
        if self.is_expired():
            return False, "OTP has expired. Please request a new one."

        if self.otp_code == otp_code:
            self.is_verified = True
            self.verified_at = timezone.now()
            self.save(update_fields=['is_verified', 'verified_at'])
            return True, "OTP verified successfully."

        return False, "Invalid OTP code."

    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at


class PasswordResetOTP(models.Model):
    """OTP for password reset"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    verification_sid = models.CharField(max_length=100, blank=True, null=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - Password Reset OTP"

    def clean(self):
        """Validate password reset OTP"""
        if not self.otp_code or len(self.otp_code) != 6:
            raise ValidationError({'otp_code': 'OTP code must be exactly 6 digits.'})

        if not self.otp_code.isdigit():
            raise ValidationError({'otp_code': 'OTP code must contain only digits.'})

    @classmethod
    def create_password_reset_otp(cls, user, email=None, phone_number=None):
        """Create password reset OTP"""
        otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        expires_at = timezone.now() + timedelta(minutes=10)

        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            email=email,
            phone_number=phone_number,
            expires_at=expires_at
        )

        return otp

    def verify_and_use(self, otp_code):
        """Verify and mark OTP as used"""
        if self.is_expired():
            return False, "OTP has expired. Please request a new one."

        if self.is_used:
            return False, "OTP has already been used."

        if self.otp_code == otp_code:
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True, "OTP verified successfully."

        return False, "Invalid OTP code."

    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at

    def can_resend(self):
        """Check if OTP can be resent"""
        return self.is_expired() or (not self.is_used and timezone.now() > self.created_at + timedelta(minutes=1))


class BlockedUser(models.Model):
    """Model for blocked users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='blocked_users'
    )
    blocked = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='blocked_by'
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['blocker', 'blocked']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

    def clean(self):
        """Validate blocked user"""
        # Cannot block self
        if self.blocker == self.blocked:
            raise ValidationError('You cannot block yourself.')

        # Validate reason length
        if self.reason and len(self.reason) > 500:
            raise ValidationError({'reason': 'Reason cannot be longer than 500 characters.'})

    @classmethod
    def is_blocked(cls, user1, user2):
        """Check if user1 has blocked user2 or vice versa"""
        return cls.objects.filter(
            (Q(blocker=user1) & Q(blocked=user2)) |
            (Q(blocker=user2) & Q(blocked=user1))
        ).exists()


# Signal handlers at the bottom to avoid circular imports
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=CustomUser)
def update_last_seen_on_save(sender, instance, **kwargs):
    """Update last_seen when user saves their profile"""
    if instance.online_status == 'online':
        instance.last_seen = timezone.now()
        # Avoid infinite recursion
        if 'update_fields' not in kwargs:
            instance.save(update_fields=['last_seen'])


@receiver(post_save, sender=FriendRequest)
def create_friend_request_notification(sender, instance, created, **kwargs):
    """Create notification for friend request"""
    if created and instance.status == 'pending':
        Notification.objects.create(
            user=instance.to_user,
            notification_type='friend_request',
            title="New Friend Request",
            message=f"{instance.from_user.username} sent you a friend request",
            related_url="/accounts/friend-requests/"
        )


@receiver(post_save, sender=FriendRequest)
def update_friend_request_notification(sender, instance, **kwargs):
    """Update notification when friend request status changes"""
    if instance.status == 'accepted':
        # Create notification for the requester
        Notification.objects.create(
            user=instance.from_user,
            notification_type='friend_request',
            title="Friend Request Accepted",
            message=f"{instance.to_user.username} accepted your friend request",
            related_url=f"/accounts/profile/{instance.to_user.id}/"
        )

        # Archive the original notification for the receiver
        Notification.objects.filter(
            user=instance.to_user,
            notification_type='friend_request',
            message__contains=f"{instance.from_user.username} sent you a friend request"
        ).update(is_archived=True)


@receiver(post_save, sender=BlockedUser)
def create_block_notification(sender, instance, created, **kwargs):
    """Create notification when user is blocked"""
    if created:
        # Notification for blocked user
        Notification.objects.create(
            user=instance.blocked,
            notification_type='system',
            title="User Blocked You",
            message=f"{instance.blocker.username} has blocked you",
            related_url="/accounts/settings/"
        )

        # Notification for blocker
        Notification.objects.create(
            user=instance.blocker,
            notification_type='system',
            title="User Blocked",
            message=f"You have blocked {instance.blocked.username}",
            related_url="/chat/blocked-users/"
        )