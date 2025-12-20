# accounts/management/commands/fix_verification.py
from django.core.management.base import BaseCommand
from accounts.models import CustomUser, OTPVerification
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fix user verification status based on OTP verification'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to fix')
        parser.add_argument('--all', action='store_true', help='Fix all users')

    def handle(self, *args, **options):
        username = options.get('username')
        fix_all = options.get('all')

        if username:
            users = CustomUser.objects.filter(username=username)
        elif fix_all:
            users = CustomUser.objects.all()
        else:
            self.stdout.write(self.style.ERROR('Specify --username or --all'))
            return

        fixed_count = 0
        for user in users:
            # Check if user has verified OTP for account verification
            has_verified_otp = OTPVerification.objects.filter(
                user=user,
                verification_type='account_verification',
                is_verified=True
            ).exists()

            if has_verified_otp and not user.is_verified:
                user.is_verified = True
                user.save(update_fields=['is_verified'])
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Fixed {user.username}: is_verified=True')
                )
                fixed_count += 1
            elif not has_verified_otp and user.is_verified:
                user.is_verified = False
                user.save(update_fields=['is_verified'])
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Fixed {user.username}: is_verified=False (no verified OTP)')
                )
                fixed_count += 1
            else:
                self.stdout.write(
                    self.style.NOTICE(f'✓ {user.username}: Already correct (is_verified={user.is_verified})')
                )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Fixed {fixed_count} users'))