# accounts/management/commands/create_default_profile.py
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from accounts.models import CustomUser
from PIL import Image, ImageDraw
import io
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Create default profile picture for users without one'

    def handle(self, *args, **options):
        # Create default profile picture file if it doesn't exist
        default_pic_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures', 'default.png')
        os.makedirs(os.path.dirname(default_pic_path), exist_ok=True)

        if not os.path.exists(default_pic_path):
            # Create a simple default profile picture
            img = Image.new('RGB', (200, 200), color=(100, 100, 100))
            d = ImageDraw.Draw(img)
            d.text((70, 90), "User", fill=(255, 255, 255))

            img_io = io.BytesIO()
            img.save(img_io, format='PNG')

            with open(default_pic_path, 'wb') as f:
                f.write(img_io.getvalue())

            self.stdout.write(self.style.SUCCESS(f'Created default profile picture at {default_pic_path}'))
        else:
            self.stdout.write(self.style.SUCCESS('Default profile picture already exists'))

        # Update users without profile pictures
        users = CustomUser.objects.filter(profile_picture='')
        count = users.count()

        for user in users:
            user.profile_picture = 'profile_pictures/default.png'
            user.save()

        self.stdout.write(self.style.SUCCESS(f'Updated {count} users with default profile picture'))