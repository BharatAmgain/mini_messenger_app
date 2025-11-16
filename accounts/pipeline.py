# messenger_app/accounts/pipeline.py
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from .models import SocialAccount


def save_profile_picture(backend, user, response, *args, **kwargs):
    if backend.name == 'facebook':
        img_url = f"https://graph.facebook.com/{response['id']}/picture?type=large&width=400&height=400"
    elif backend.name == 'google-oauth2':
        img_url = response.get('picture')
    else:
        return

    if img_url and not user.profile_picture:
        try:
            # Download the image
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(img_url).read())
            img_temp.flush()

            # Save to user profile
            user.profile_picture.save(f"{user.username}_social.jpg", File(img_temp))

            # Save social provider info
            user.social_provider = backend.name
            if backend.name == 'facebook':
                user.social_avatar = img_url
            elif backend.name == 'google-oauth2':
                user.social_avatar = response.get('picture')

            user.save()

            # Create SocialAccount record
            SocialAccount.objects.get_or_create(
                user=user,
                provider=backend.name,
                provider_id=response['id'],
                email=response.get('email', '')
            )

        except Exception as e:
            print(f"Error downloading profile picture: {e}")