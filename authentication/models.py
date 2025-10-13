from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import string

User = get_user_model()

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

class TwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=10, choices=[('email', 'Email'), ('phone', 'Phone')], default='email')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    secret_key = models.CharField(max_length=100, default='')

    def generate_otp(self):
        # Generate a random 6-digit OTP
        return ''.join(random.choices(string.digits, k=6))

    def verify_otp(self, otp):
        # Simple verification - check if it's 6 digits
        # In a real app, you'd implement proper TOTP verification
        return len(otp) == 6 and otp.isdigit()

    def generate_secret_key(self):
        # Generate a random secret key
        chars = string.ascii_uppercase + string.digits
        self.secret_key = ''.join(random.choices(chars, k=16))
        return self.secret_key

class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)