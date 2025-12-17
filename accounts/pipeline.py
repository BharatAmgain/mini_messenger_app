# messenger_app/accounts/pipeline.py
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth import get_user_model
from .models import SocialAccount, CustomUser
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def handle_duplicate_email(backend, uid, user=None, *args, **kwargs):
    """
    Custom pipeline function to handle existing users with the same email.
    This prevents 'UNIQUE constraint failed: accounts_customuser.email' errors.
    """
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)

    if social:
        # Social account already exists, use it
        return {'social': social, 'user': social.user}

    if user:
        # User is already authenticated
        return None

    # Get email from OAuth response
    response = kwargs.get('response', {})
    email = response.get('email')

    if email:
        try:
            # Try to find an existing user by email
            existing_user = CustomUser.objects.get(email=email)

            # Create social auth for this existing user
            social = backend.strategy.storage.user.create_social_auth(
                existing_user, uid, provider
            )
            return {'social': social, 'user': existing_user}

        except CustomUser.DoesNotExist:
            # No user with this email exists, continue with normal flow
            pass
        except CustomUser.MultipleObjectsReturned:
            # Multiple users with same email (shouldn't happen due to unique constraint)
            # Use the first one
            existing_user = CustomUser.objects.filter(email=email).first()
            if existing_user:
                social = backend.strategy.storage.user.create_social_auth(
                    existing_user, uid, provider
                )
                return {'social': social, 'user': existing_user}

    return None


def save_profile_picture(backend, user, response, *args, **kwargs):
    """Download and save profile picture from social providers."""
    img_url = None

    if backend.name == 'google-oauth2':
        # Google provides picture URL directly
        img_url = response.get('picture')
    elif backend.name == 'facebook':
        # Facebook needs the ID to construct URL
        facebook_id = response.get('id')
        if facebook_id:
            img_url = f"https://graph.facebook.com/{facebook_id}/picture?type=large&width=400&height=400"

    if img_url and not user.profile_picture:
        try:
            # Download the image
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(img_url).read())
            img_temp.flush()

            # Save to user profile
            user.profile_picture.save(f"{user.username}_social.jpg", File(img_temp))
            user.social_provider = backend.name
            user.save()

        except Exception as e:
            # Just log the error, don't break the login
            logger.warning(f"Could not download profile picture: {e}")