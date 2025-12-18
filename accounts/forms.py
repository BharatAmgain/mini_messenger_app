# messenger_app/accounts/forms.py
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordChangeForm,
    SetPasswordForm,
    PasswordResetForm as AuthPasswordResetForm
)
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import CustomUser
import phonenumbers
from phonenumbers import NumberParseException
import re


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Enter your email'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Choose a username'
    }))
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter password (min 8 characters)'
        }),
        help_text="Password must be at least 8 characters long."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        }),
        error_messages={
            'required': 'Please enter the OTP code',
            'min_length': 'OTP must be 6 digits',
            'max_length': 'OTP must be 6 digits'
        }
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        if not otp_code.isdigit():
            raise forms.ValidationError('OTP must contain only numbers')
        return otp_code


class PasswordResetRequestForm(AuthPasswordResetForm):
    email_or_phone = forms.CharField(
        label="Email or Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter your email or phone number'
        }),
        help_text="Example: user@example.com or +9779800000000"
    )

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone', '').strip()

        if not email_or_phone:
            raise forms.ValidationError('Please enter an email or phone number')

        # Check if it's an email
        if '@' in email_or_phone:
            # Validate email format
            try:
                validate_email(email_or_phone)
                return {'type': 'email', 'value': email_or_phone}
            except ValidationError:
                raise forms.ValidationError('Please enter a valid email address (e.g., user@example.com)')
        else:
            # Try to parse as phone number
            # Remove any spaces, dashes, parentheses
            phone = email_or_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

            # Add country code if not present (assume Nepal +977)
            if not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+977' + phone[1:]  # Remove leading 0 and add +977
                else:
                    phone = '+977' + phone

            try:
                parsed = phonenumbers.parse(phone, None)  # Auto-detect country
                if phonenumbers.is_valid_number(parsed):
                    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                    return {'type': 'phone', 'value': formatted}
                else:
                    raise forms.ValidationError('Please enter a valid phone number (e.g., +9779800000000)')
            except NumberParseException:
                # Try one more time with just the number
                try:
                    # Try with Nepal as default
                    parsed = phonenumbers.parse(phone, "NP")
                    if phonenumbers.is_valid_number(parsed):
                        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                        return {'type': 'phone', 'value': formatted}
                    else:
                        raise forms.ValidationError('Please enter a valid phone number')
                except:
                    raise forms.ValidationError('Please enter a valid email or phone number')

    def get_users(self, email_or_phone):
        """Get users by email or phone number"""
        if not hasattr(self, 'cleaned_data'):
            return []

        data = self.cleaned_data.get('email_or_phone')
        if not data:
            return []

        if data['type'] == 'email':
            email = data['value']
            return CustomUser.objects.filter(email__iexact=email, is_active=True)
        else:  # phone
            phone = data['value']
            return CustomUser.objects.filter(phone_number=phone, is_active=True)


class OTPPasswordResetForm(SetPasswordForm):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter OTP',
            'autocomplete': 'off'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        # Remove the new_password2 help text
        self.fields['new_password2'].help_text = None


class OTPPasswordChangeForm(PasswordChangeForm):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter OTP sent to your email/phone',
            'autocomplete': 'off'
        }),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the new_password2 help text
        self.fields['new_password2'].help_text = None


class VerifyOTPForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'off'
        })
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        if not otp_code.isdigit():
            raise forms.ValidationError('OTP must contain only numbers')
        return otp_code


class SendOTPForm(forms.Form):
    verification_method = forms.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone')
        ],
        widget=forms.RadioSelect(attrs={'class': 'mr-2'})
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter your email'
        })
    )

    phone_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter your phone number (e.g., +9779800000000)'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        verification_method = cleaned_data.get('verification_method')
        email = cleaned_data.get('email')
        phone_number = cleaned_data.get('phone_number')

        if verification_method == 'email' and not email:
            raise forms.ValidationError('Email is required for email verification')

        if verification_method == 'phone' and not phone_number:
            raise forms.ValidationError('Phone number is required for phone verification')

        # Validate phone number if provided
        if phone_number:
            try:
                # Add + if not present
                if not phone_number.startswith('+'):
                    phone_number = '+977' + phone_number.lstrip('0')

                parsed = phonenumbers.parse(phone_number, None)
                if not phonenumbers.is_valid_number(parsed):
                    raise forms.ValidationError('Please enter a valid phone number (e.g., +9779800000000)')
            except NumberParseException:
                raise forms.ValidationError('Please enter a valid phone number (e.g., +9779800000000)')

        return cleaned_data