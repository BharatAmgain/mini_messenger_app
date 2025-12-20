# messenger_app/accounts/views.py - COMPLETE FIXED VERSION
import json
import traceback
import base64
import requests
from datetime import timedelta
import urllib.parse

from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from social_core.backends.google import GoogleOAuth2

from .forms import (
    CustomUserCreationForm,
    OTPVerificationForm,
    PasswordResetRequestForm,
    OTPPasswordResetForm,
    OTPPasswordChangeForm,
    VerifyOTPForm,
    SendOTPForm
)
from .models import CustomUser, Notification, FriendRequest, Friendship, OTPVerification, PasswordResetOTP


def send_twilio_verification(phone_number):
    """Send verification code via Twilio Verify API - FIXED"""
    try:
        # Check if Twilio is configured
        if not all([settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN,
                    settings.TWILIO_VERIFY_SERVICE_SID]):
            print("ERROR: Twilio not configured in settings")
            return None, "Twilio verification service not configured"

        service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        url = f"https://verify.twilio.com/v2/Services/{service_sid}/Verifications"

        # Basic auth
        auth_string = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'To': phone_number,
            'Channel': 'sms',
        }

        print(f"DEBUG: Sending Twilio verification to {phone_number}")
        response = requests.post(url, headers=headers, data=data, timeout=30)

        if response.status_code == 201:
            result = response.json()
            verification_sid = result.get('sid')
            print(f"DEBUG: Verification sent successfully. SID: {verification_sid}")
            return verification_sid, "Verification code sent successfully"
        else:
            print(f"DEBUG: Twilio error: {response.status_code} - {response.text}")
            return None, f"Failed to send verification: {response.status_code}"

    except requests.exceptions.Timeout:
        print("ERROR: Twilio request timeout")
        return None, "Verification service timeout. Please try again."
    except Exception as e:
        print(f"ERROR: Twilio exception: {str(e)}")
        return None, f"Verification error: {str(e)}"


def verify_twilio_code(phone_number, code):
    """Verify code with Twilio Verify API - FIXED"""
    try:
        # Check if Twilio is configured
        if not all([settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN,
                    settings.TWILIO_VERIFY_SERVICE_SID]):
            return False, "Twilio verification service not configured"

        service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        url = f"https://verify.twilio.com/v2/Services/{service_sid}/VerificationCheck"

        # Basic auth
        auth_string = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'To': phone_number,
            'Code': code,
        }

        print(f"DEBUG: Verifying code {code} for {phone_number}")
        response = requests.post(url, headers=headers, data=data, timeout=30)

        if response.status_code == 201:
            result = response.json()
            if result.get('status') == 'approved' and result.get('valid') == True:
                print(f"DEBUG: Twilio verification SUCCESSFUL!")
                return True, "Verification successful"
            else:
                print(f"DEBUG: Verification failed: status={result.get('status')}, valid={result.get('valid')}")
                return False, "Invalid verification code"
        else:
            print(f"DEBUG: Verification failed: {response.status_code} - {response.text}")
            return False, f"Verification failed: {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Verification timeout. Please try again."
    except Exception as e:
        print(f"ERROR: Verification exception: {str(e)}")
        return False, f"Verification error: {str(e)}"


def register(request):
    if request.user.is_authenticated:
        return redirect('chat_home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                # Import ModelBackend correctly
                from django.contrib.auth.backends import ModelBackend

                # Use ModelBackend class, not string
                user.backend = f'{ModelBackend.__module__}.{ModelBackend.__name__}'

                # Log the user in
                from django.contrib.auth import login
                login(request, user)

                messages.success(request, 'Registration successful! Welcome to Messenger!')
                return redirect('chat_home')

            except Exception as e:
                messages.error(request, f'Registration error: {str(e)}')
                return render(request, 'accounts/register.html', {'form': form})
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_profile(request):
    """Update user profile"""
    try:
        user = request.user

        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        # Handle profile picture separately if it's base64 encoded
        if 'profile_picture_base64' in data and data['profile_picture_base64']:
            try:
                # Decode base64 image
                format, imgstr = data['profile_picture_base64'].split(';base64,')
                ext = format.split('/')[-1]
                image_data = base64.b64decode(imgstr)

                # Save to file
                filename = f"profile_{user.id}.{ext}"
                file_path = default_storage.save(
                    f"profile_pictures/{filename}",
                    ContentFile(image_data)
                )
                user.profile_picture = file_path
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid image data: {str(e)}'
                }, status=400)

        # Update other fields - EXCLUDE is_verified from user input
        # Only allow updating specific fields
        allowed_fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'bio', 'date_of_birth',
            'facebook_url', 'twitter_url', 'instagram_url'
        ]

        for field in allowed_fields:
            if field in data and data[field] is not None:
                # Special handling for boolean fields
                if field in ['email_notifications', 'push_notifications']:
                    setattr(user, field, bool(data[field]))
                else:
                    setattr(user, field, data[field])

        # Validate and save
        user.full_clean()
        user.save()

        # Return updated user data
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_picture_url': user.get_profile_picture_url(),
                'is_verified': user.is_verified,
                'phone_number': user.phone_number,
                'bio': user.bio
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def get_profile(request):
    """Get current user's profile"""
    user = request.user
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_picture_url': user.get_profile_picture_url(),
            'is_verified': user.is_verified,
            'phone_number': user.phone_number,
            'bio': user.bio,
            'date_of_birth': str(user.date_of_birth) if user.date_of_birth else None,
            'location': user.location,
            'website': user.website,
            'gender': user.gender
        }
    })


@login_required
def profile(request):
    """View user's own profile - FIXED: Always get fresh user data"""
    # CRITICAL FIX: Always get fresh user data from database, not cached request.user
    try:
        # Get fresh user instance from database
        user = CustomUser.objects.select_related().get(id=request.user.id)
        print(f"PROFILE VIEW: Loading fresh user data for {user.username}")
        print(f"  First Name: '{user.first_name}'")
        print(f"  Last Name: '{user.last_name}'")
        print(f"  Email: {user.email}")
        print(f"  Phone: {user.phone_number}")
        print(f"  Verified: {user.is_verified}")
    except CustomUser.DoesNotExist:
        user = request.user

    return render(request, 'accounts/profile.html', {'user': user})


@login_required
def profile_edit(request):
    """Edit user's own profile - FIXED VERSION"""
    user = request.user

    if request.method == 'POST':
        try:
            # Handle profile picture separately
            if 'profile_picture' in request.FILES and request.FILES['profile_picture']:
                profile_picture = request.FILES['profile_picture']
                if profile_picture.content_type.startswith('image/'):
                    if profile_picture.size <= 5 * 1024 * 1024:  # 5MB
                        user.profile_picture = profile_picture
                    else:
                        messages.error(request, 'Image too large. Max 5MB.')
                else:
                    messages.error(request, 'Please select a valid image file.')

            # Track which fields were updated
            updated_fields = []

            # Update ONLY safe fields - whitelist approach
            safe_fields = ['first_name', 'last_name', 'email', 'phone_number',
                           'bio', 'location', 'website', 'gender']

            for field in safe_fields:
                if field in request.POST:
                    value = request.POST.get(field, '').strip()
                    old_value = getattr(user, field)

                    if field == 'email':
                        # Special handling for email - must be unique
                        if value and value != user.email:
                            # Check if email already exists
                            if CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
                                messages.error(request, 'This email is already in use.')
                                continue
                            else:
                                user.email = value
                                updated_fields.append(field)
                    elif field == 'phone_number':
                        # Special handling for phone number
                        if value != str(old_value):
                            user.phone_number = value
                            updated_fields.append(field)
                    else:
                        # For other fields
                        if value != str(old_value):
                            setattr(user, field, value)
                            updated_fields.append(field)

            # Handle date_of_birth separately
            if 'date_of_birth' in request.POST and request.POST['date_of_birth']:
                try:
                    from datetime import datetime
                    dob_str = request.POST['date_of_birth']
                    new_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    if new_dob != user.date_of_birth:
                        user.date_of_birth = new_dob
                        updated_fields.append('date_of_birth')
                except ValueError:
                    messages.error(request, 'Invalid date format. Use YYYY-MM-DD')

            # CRITICAL FIX: Ensure is_verified is always a boolean and not touched by form
            # Remove is_verified if it exists in POST data
            if 'is_verified' in request.POST:
                del request.POST['is_verified']

            # Ensure is_verified is explicitly set to current value (boolean)
            user.is_verified = bool(user.is_verified)

            # Only save if there are changes
            if updated_fields:
                # Force save with specific fields to ensure database update
                user.save(update_fields=updated_fields)

                # CRITICAL: Get fresh user instance from database to ensure data is updated
                fresh_user = CustomUser.objects.get(id=user.id)

                # Debug output
                print(f"PROFILE EDIT: Updated fields: {updated_fields}")
                print(f"  New First Name: '{fresh_user.first_name}'")
                print(f"  New Last Name: '{fresh_user.last_name}'")
                print(f"  New Email: {fresh_user.email}")
                print(f"  New Phone: {fresh_user.phone_number}")

                messages.success(request, 'Profile updated successfully!')
            else:
                messages.info(request, 'No changes were made to your profile.')

            return redirect('profile')

        except ValidationError as e:
            # Handle validation errors properly
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
            else:
                error_messages = e.messages if hasattr(e, 'messages') else [str(e)]

            for error_msg in error_messages:
                messages.error(request, error_msg)

        except Exception as e:
            print(f"ERROR in profile_edit: {str(e)}")
            messages.error(request, f'Error updating profile: {str(e)}')

    # Get context for template
    context = {
        'user': user,
        'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else '',
    }

    return render(request, 'accounts/profile_edit.html', context)


@login_required
def settings_main(request):
    return render(request, 'accounts/settings.html', {'user': request.user})


@login_required
def privacy_settings(request):
    """Privacy settings page"""
    return render(request, 'accounts/privacy_settings.html', {'user': request.user})


@login_required
def update_privacy_settings(request):
    """Update privacy settings"""
    if request.method == 'POST':
        user = request.user
        user.show_online_status = request.POST.get('show_online_status') == 'on'
        user.allow_message_requests = request.POST.get('allow_message_requests') == 'on'
        user.allow_calls = request.POST.get('allow_calls') == 'on'
        user.allow_invitations = request.POST.get('allow_invitations') == 'on'
        user.show_last_seen = request.POST.get('show_last_seen') == 'on'
        user.show_profile_picture = request.POST.get('show_profile_picture') == 'on'
        user.save()
        messages.success(request, 'Privacy settings updated successfully!')

    return redirect('privacy_settings')


@login_required
def notifications(request):
    """Enhanced notifications page with filtering and management"""
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', 'newest')

    # Base queryset
    notifications = request.user.account_notifications.filter(is_archived=False)

    # Apply filters
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    elif filter_type != 'all':
        notifications = notifications.filter(notification_type=filter_type)

    # Apply sorting
    if sort_by == 'oldest':
        notifications = notifications.order_by('created_at')
    else:  # newest
        notifications = notifications.order_by('-created_at')

    # Get notification counts for filters
    notification_counts = {
        'all': request.user.account_notifications.filter(is_archived=False).count(),
        'unread': request.user.account_notifications.filter(is_read=False, is_archived=False).count(),
        'read': request.user.account_notifications.filter(is_read=True, is_archived=False).count(),
    }

    # Count by type
    for notification_type, _ in Notification.NOTIFICATION_TYPES:
        notification_counts[notification_type] = request.user.account_notifications.filter(
            notification_type=notification_type,
            is_archived=False
        ).count()

    context = {
        'notifications': notifications,
        'filter_type': filter_type,
        'sort_by': sort_by,
        'notification_counts': notification_counts,
        'notification_types': Notification.NOTIFICATION_TYPES,
    }
    return render(request, 'accounts/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark single notification as read"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, 'Notification marked as read.')
        except Notification.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Notification not found'})
            messages.error(request, 'Notification not found.')

    return redirect('notifications')


@login_required
def mark_notification_unread(request, notification_id):
    """Mark single notification as unread"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = False
            notification.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, 'Notification marked as unread.')
        except Notification.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Notification not found'})
            messages.error(request, 'Notification not found.')

    return redirect('notifications')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if request.method == 'POST':
        updated_count = request.user.account_notifications.filter(
            is_read=False,
            is_archived=False
        ).update(is_read=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'updated_count': updated_count
            })

        messages.success(request, f'Marked {updated_count} notifications as read.')

    return redirect('notifications')


@login_required
def mark_all_notifications_unread(request):
    """Mark all notifications as unread"""
    if request.method == 'POST':
        updated_count = request.user.account_notifications.filter(
            is_read=True,
            is_archived=False
        ).update(is_read=False)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'updated_count': updated_count
            })

        messages.success(request, f'Marked {updated_count} notifications as unread.')

    return redirect('notifications')


@login_required
def archive_notification(request, notification_id):
    """Archive a single notification"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_archived = True
            notification.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, 'Notification archived.')
        except Notification.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Notification not found'})
            messages.error(request, 'Notification not found.')

    return redirect('notifications')


@login_required
def archive_all_notifications(request):
    """Archive all notifications"""
    if request.method == 'POST':
        updated_count = request.user.account_notifications.filter(
            is_archived=False
        ).update(is_archived=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'updated_count': updated_count
            })

        messages.success(request, f'Archived {updated_count} notifications.')

    return redirect('notifications')


@login_required
def delete_notification(request, notification_id):
    """Delete a single notification"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            messages.success(request, 'Notification deleted.')
        except Notification.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Notification not found'})
            messages.error(request, 'Notification not found.')

    return redirect('notifications')


@login_required
def clear_all_notifications(request):
    """Clear all notifications"""
    if request.method == 'POST':
        deleted_count = request.user.account_notifications.all().count()
        request.user.account_notifications.all().delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count
            })

        messages.success(request, f'Cleared {deleted_count} notifications.')

    return redirect('notifications')


@login_required
def notification_settings(request):
    """Notification settings page"""
    return render(request, 'accounts/notification_settings.html', {'user': request.user})


@login_required
def update_notification_preferences(request):
    """Update notification preferences - FIXED: Handle quiet hours properly"""
    if request.method == 'POST':
        user = request.user

        # Message notifications
        user.message_notifications = request.POST.get('message_notifications') == 'on'
        user.message_sound = request.POST.get('message_sound') == 'on'
        user.message_preview = request.POST.get('message_preview') == 'on'

        # Group notifications
        user.group_notifications = request.POST.get('group_notifications') == 'on'
        user.group_mentions_only = request.POST.get('group_mentions_only') == 'on'

        # Friend notifications
        user.friend_request_notifications = request.POST.get('friend_request_notifications') == 'on'
        user.friend_online_notifications = request.POST.get('friend_online_notifications') == 'on'

        # System notifications
        user.system_notifications = request.POST.get('system_notifications') == 'on'
        user.marketing_notifications = request.POST.get('marketing_notifications') == 'on'

        # Delivery methods
        user.push_notifications = request.POST.get('push_notifications') == 'on'
        user.email_notifications = request.POST.get('email_notifications') == 'on'
        user.desktop_notifications = request.POST.get('desktop_notifications') == 'on'

        # Quiet hours - FIXED: Only update time fields if quiet hours are enabled
        user.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'

        if user.quiet_hours_enabled:
            # Only set time values if quiet hours are enabled
            quiet_hours_start = request.POST.get('quiet_hours_start')
            quiet_hours_end = request.POST.get('quiet_hours_end')

            if quiet_hours_start:
                user.quiet_hours_start = quiet_hours_start
            if quiet_hours_end:
                user.quiet_hours_end = quiet_hours_end
        else:
            # If quiet hours are disabled, set times to None
            user.quiet_hours_start = None
            user.quiet_hours_end = None

        user.save()
        messages.success(request, 'Notification preferences updated successfully!')

    return redirect('notification_settings')


@login_required
def get_unread_count(request):
    """Get unread notification count for badge"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        unread_count = request.user.account_notifications.filter(is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'error': 'Invalid request'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat_home')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate with all available backends
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # User authenticated successfully
            login(request, user)
            next_url = request.GET.get('next', 'chat_home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    # Check for social auth errors
    social_errors = []
    if 'social-auth' in request.GET:
        messages.error(request, 'There was an error with social authentication. Please try again.')

    return render(request, 'accounts/login.html', {
        'social_errors': social_errors
    })


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def update_notification_settings(request):
    """Update notification settings"""
    if request.method == 'POST':
        user = request.user
        user.email_notifications = request.POST.get('email_notifications') == 'on'
        user.push_notifications = request.POST.get('push_notifications') == 'on'
        user.message_notifications = request.POST.get('message_notifications') == 'on'
        user.marketing_emails = request.POST.get('marketing_emails') == 'on'
        user.save()
        messages.success(request, 'Notification settings updated successfully!')
    return redirect('settings_main')


@login_required
def deactivate_account(request):
    """Deactivate user account"""
    if request.method == 'POST':
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, 'Your account has been deactivated. You can reactivate by logging in.')
        return redirect('login')
    return redirect('settings_main')


@login_required
def delete_account(request):
    """Permanently delete user account"""
    if request.method == 'POST':
        user = request.user
        # Perform cleanup (you might want to add more cleanup logic)
        user.delete()
        logout(request)
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('login')
    return redirect('settings_main')


@login_required
def clear_chat_history(request):
    """Clear user's chat history"""
    if request.method == 'POST':
        # Add logic to clear chat history
        # This would typically involve deleting messages or chat records
        messages.success(request, 'Your chat history has been cleared.')
    return redirect('settings_main')


@login_required
def export_data(request):
    """Export user data"""
    if request.method == 'POST':
        # Add logic to prepare data export
        # This would typically generate a file with user data
        messages.success(request, 'Your data export has been requested. You will receive an email when it\'s ready.')
    return redirect('settings_main')


@login_required
def update_theme(request):
    """Update user theme preference"""
    if request.method == 'POST':
        user = request.user
        user.theme = request.POST.get('theme', 'auto')
        user.save()
        messages.success(request, f'Theme updated to {user.theme} mode.')
    return redirect('settings_main')


@login_required
def toggle_two_factor(request):
    """Toggle two-factor authentication"""
    if request.method == 'POST':
        user = request.user
        user.two_factor_enabled = not user.two_factor_enabled
        user.save()
        status = "enabled" if user.two_factor_enabled else "disabled"

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': status,
                'message': f'Two-factor authentication has been {status}.'
            })

        messages.success(request, f'Two-factor authentication has been {status}.')
    return redirect('settings_main')


@login_required
def send_friend_request(request, user_id):
    """Send a friend request to another user"""
    if request.method == 'POST':
        try:
            to_user = CustomUser.objects.get(id=user_id)

            # Can't send request to yourself
            if to_user == request.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'You cannot send a friend request to yourself.'})
                messages.error(request, 'You cannot send a friend request to yourself.')
                return redirect('discover_users')

            # Check if users are already friends
            if Friendship.are_friends(request.user, to_user):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'You are already friends with this user.'})
                messages.warning(request, 'You are already friends with this user.')
                return redirect('discover_users')

            # Check if there's any existing friend request (regardless of status)
            existing_request = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=to_user
            ).first()

            if existing_request:
                # If there's an existing request, handle based on its status
                if existing_request.status == 'pending':
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Friend request already sent.'})
                    messages.warning(request, 'Friend request already sent.')
                    return redirect('discover_users')
                elif existing_request.status == 'accepted':
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'You are already friends with this user.'})
                    messages.warning(request, 'You are already friends with this user.')
                    return redirect('discover_users')
                else:  # cancelled or rejected - update the existing request
                    existing_request.status = 'pending'
                    existing_request.message = request.POST.get('message', '')
                    existing_request.save()

                    # Create notification
                    Notification.objects.create(
                        user=to_user,
                        notification_type='friend_request',
                        title="New Friend Request",
                        message=f"{request.user.username} sent you a friend request",
                        related_url="/accounts/friend-requests/"
                    )

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': f'Friend request sent to {to_user.username}!'})
                    messages.success(request, f'Friend request sent to {to_user.username}!')
                    return redirect('discover_users')

            # Check if reverse request exists
            reverse_request = FriendRequest.objects.filter(
                from_user=to_user,
                to_user=request.user,
                status='pending'
            ).first()

            if reverse_request:
                # Auto-accept if there's a pending reverse request
                reverse_request.accept()
                Friendship.create_friendship(request.user, to_user)

                # Create notification for both users
                Notification.objects.create(
                    user=to_user,
                    notification_type='friend_request',
                    title="Friend Request Accepted",
                    message=f"{request.user.username} accepted your friend request",
                    related_url=f"/accounts/profile/{request.user.id}/"
                )

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f'You are now friends with {to_user.username}!'})
                messages.success(request, f'You are now friends with {to_user.username}!')
            else:
                # Create new friend request using get_or_create to avoid unique constraint issues
                friend_request, created = FriendRequest.objects.get_or_create(
                    from_user=request.user,
                    to_user=to_user,
                    defaults={
                        'message': request.POST.get('message', ''),
                        'status': 'pending'
                    }
                )

                if not created:
                    # If it already exists but wasn't caught above, update it
                    friend_request.status = 'pending'
                    friend_request.message = request.POST.get('message', '')
                    friend_request.save()

                # Create notification
                Notification.objects.create(
                    user=to_user,
                    notification_type='friend_request',
                    title="New Friend Request",
                    message=f"{request.user.username} sent you a friend request",
                    related_url="/accounts/friend-requests/"
                )

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f'Friend request sent to {to_user.username}!'})
                messages.success(request, f'Friend request sent to {to_user.username}!')

        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found.'})
            messages.error(request, 'User not found.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    return redirect('discover_users')


@login_required
def cancel_friend_request(request, user_id):
    """Cancel a sent friend request"""
    if request.method == 'POST':
        try:
            to_user = CustomUser.objects.get(id=user_id)

            # Find any pending friend request
            friend_request = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=to_user,
                status='pending'
            ).first()

            if friend_request:
                friend_request.status = 'cancelled'
                friend_request.save()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'success': True, 'message': f'Friend request to {to_user.username} cancelled.'})
                messages.success(request, f'Friend request to {to_user.username} cancelled.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'No pending friend request found.'})
                messages.error(request, 'No pending friend request found.')

        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found.'})
            messages.error(request, 'User not found.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    return redirect('discover_users')


@login_required
def accept_friend_request(request, request_id):
    """Accept a friend request"""
    if request.method == 'POST':
        try:
            friend_request = FriendRequest.objects.get(
                id=request_id,
                to_user=request.user,
                status='pending'
            )

            friend_request.accept()
            Friendship.create_friendship(friend_request.from_user, friend_request.to_user)

            # Create notification for the requester
            Notification.objects.create(
                user=friend_request.from_user,
                notification_type='friend_request',
                title="Friend Request Accepted",
                message=f"{request.user.username} accepted your friend request",
                related_url=f"/accounts/profile/{request.user.id}/"
            )

            messages.success(request, f'You are now friends with {friend_request.from_user.username}!')

        except FriendRequest.DoesNotExist:
            messages.error(request, 'Friend request not found.')

    return redirect('friend_requests')


@login_required
def reject_friend_request(request, request_id):
    """Reject a friend request"""
    if request.method == 'POST':
        try:
            friend_request = FriendRequest.objects.get(
                id=request_id,
                to_user=request.user,
                status='pending'
            )

            friend_request.reject()
            messages.success(request, f'Friend request from {friend_request.from_user.username} rejected.')

        except FriendRequest.DoesNotExist:
            messages.error(request, 'Friend request not found.')

    return redirect('friend_requests')


@login_required
def friend_requests(request):
    """View friend requests"""
    received_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')

    sent_requests = FriendRequest.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user')

    friends = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2')

    # Extract friend users
    friend_users = []
    for friendship in friends:
        if friendship.user1 == request.user:
            friend_users.append(friendship.user2)
        else:
            friend_users.append(friendship.user1)

    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'friends': friend_users,
    }
    return render(request, 'accounts/friend_requests.html', context)


@login_required
def remove_friend(request, user_id):
    """Remove a friend"""
    if request.method == 'POST':
        try:
            friend = CustomUser.objects.get(id=user_id)

            # Delete friendship
            Friendship.objects.filter(
                (Q(user1=request.user) & Q(user2=friend)) |
                (Q(user1=friend) & Q(user2=request.user))
            ).delete()

            # Update friend request status
            FriendRequest.objects.filter(
                (Q(from_user=request.user) & Q(to_user=friend)) |
                (Q(from_user=friend) & Q(to_user=request.user))
            ).update(status='cancelled')

            messages.success(request, f'{friend.username} removed from friends.')

        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')

    return redirect('friend_requests')


def password_reset_request(request):
    """Request password reset with OTP - FIXED VERSION"""
    if request.user.is_authenticated:
        return redirect('chat_home')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email_or_phone = form.cleaned_data['email_or_phone']

            if email_or_phone['type'] == 'email':
                email = email_or_phone['value']
                try:
                    user = CustomUser.objects.get(email__iexact=email, is_active=True)

                    # CREATE OTP RECORD
                    otp = PasswordResetOTP.create_password_reset_otp(
                        user=user,
                        email=email
                    )

                    # Store in session
                    request.session['password_reset_user_id'] = str(user.id)
                    request.session['password_reset_otp_id'] = str(otp.id)
                    request.session['password_reset_method'] = 'email'

                    messages.success(request, f'OTP has been sent to {email}. Please check your email.')
                    return redirect('password_reset_verify_otp')

                except CustomUser.DoesNotExist:
                    # Still show success message for security (don't reveal if user exists)
                    messages.success(request, 'If an account exists with this email, OTP has been sent.')
                    return redirect('password_reset_verify_otp')

            else:  # phone - USE TWILIO
                phone = email_or_phone['value']
                try:
                    user = CustomUser.objects.get(phone_number=phone, is_active=True)

                    # ✅ SEND VIA TWILIO VERIFY API
                    verification_sid, message = send_twilio_verification(phone)

                    if verification_sid:
                        # Create OTP record with Twilio SID
                        otp = PasswordResetOTP.objects.create(
                            user=user,
                            otp_code='000000',  # Placeholder - Twilio handles the code
                            phone_number=phone,
                            expires_at=timezone.now() + timedelta(minutes=10),
                            verification_sid=verification_sid  # Store Twilio verification SID
                        )

                        # Store in session
                        request.session['password_reset_user_id'] = str(user.id)
                        request.session['password_reset_otp_id'] = str(otp.id)
                        request.session['password_reset_method'] = 'phone'
                        request.session['twilio_verification_sid'] = verification_sid
                        request.session['twilio_phone_number'] = phone  # Store phone number

                        messages.success(request, f'Verification code has been sent to {phone}.')
                        return redirect('password_reset_verify_otp')
                    else:
                        messages.error(request, f'Failed to send verification: {message}')

                except CustomUser.DoesNotExist:
                    # Still show success message for security
                    messages.success(request, 'If an account exists with this phone, verification code has been sent.')
                    return redirect('password_reset_verify_otp')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
        else:
            # DEBUG: Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_verify_otp(request):
    """Verify OTP for password reset - FIXED VERSION"""
    if request.user.is_authenticated:
        return redirect('chat_home')

    # ✅ FIX: Initialize form at the beginning to prevent UnboundLocalError
    form = OTPVerificationForm()

    # Get session data
    user_id = request.session.get('password_reset_user_id')
    otp_id = request.session.get('password_reset_otp_id')
    reset_method = request.session.get('password_reset_method')
    phone_number = request.session.get('twilio_phone_number')

    if not user_id or not otp_id:
        messages.error(request, 'Invalid password reset request. Please start over.')
        return redirect('password_reset_request')

    try:
        user = CustomUser.objects.get(id=user_id, is_active=True)
        otp = PasswordResetOTP.objects.get(id=otp_id, user=user, is_used=False)
    except (CustomUser.DoesNotExist, PasswordResetOTP.DoesNotExist):
        messages.error(request, 'Invalid password reset request. Please start over.')
        # Clear session
        session_keys = ['password_reset_user_id', 'password_reset_otp_id',
                        'password_reset_method', 'twilio_verification_sid', 'twilio_phone_number']
        for key in session_keys:
            if key in request.session:
                del request.session[key]
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)  # Re-initialize with POST data
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            # VERIFY VIA TWILIO FOR PHONE
            if reset_method == 'phone' and phone_number:
                print(f"DEBUG: Verifying phone OTP {otp_code} for {phone_number}")

                success, message = verify_twilio_code(phone_number, otp_code)

                if success:
                    # Mark OTP as used
                    otp.is_used = True
                    otp.save()

                    # Store verification in session
                    request.session['password_reset_verified'] = True
                    request.session['verified_user_id'] = str(user.id)

                    messages.success(request, 'Verification successful! You can now set your new password.')
                    return redirect('password_reset_confirm')
                else:
                    messages.error(request, message)
            else:
                # Email verification
                success, message = otp.verify_and_use(otp_code)

                if success:
                    request.session['password_reset_verified'] = True
                    request.session['verified_user_id'] = str(user.id)
                    messages.success(request, 'OTP verified successfully. You can now set your new password.')
                    return redirect('password_reset_confirm')
                else:
                    messages.error(request, message)
        else:
            messages.error(request, 'Please enter a valid 6-digit verification code.')

    # Get contact info for display
    contact_info = None
    if reset_method == 'email' and otp.email:
        # Mask email
        email = otp.email
        if '@' in email:
            username, domain = email.split('@')
            masked_email = username[0] + '*' * max(0, len(username) - 2) + username[-1] + '@' + domain
            contact_info = masked_email
    elif reset_method == 'phone' and phone_number:
        # Mask phone number
        phone = phone_number
        if len(phone) > 4:
            masked_phone = '*' * (len(phone) - 4) + phone[-4:]
        else:
            masked_phone = '*' * len(phone)
        contact_info = masked_phone

    context = {
        'form': form,  # This variable is now guaranteed to be defined
        'contact_info': contact_info,
        'reset_method': reset_method,
        'can_resend': True,
    }
    return render(request, 'accounts/password_reset_verify_otp.html', context)


def password_reset_confirm(request):
    """Set new password after OTP verification"""
    if request.user.is_authenticated:
        return redirect('chat_home')

    # Check if verification is complete
    if not request.session.get('password_reset_verified'):
        messages.error(request, 'Please verify OTP first.')
        return redirect('password_reset_request')

    user_id = request.session.get('verified_user_id')
    if not user_id:
        messages.error(request, 'Invalid session. Please start over.')
        return redirect('password_reset_request')

    try:
        user = CustomUser.objects.get(id=user_id, is_active=True)
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
        # Clear session
        if 'password_reset_verified' in request.session:
            del request.session['password_reset_verified']
        if 'verified_user_id' in request.session:
            del request.session['verified_user_id']
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = OTPPasswordResetForm(user, request.POST)
        if form.is_valid():
            # Clear all session data
            session_keys = [
                'password_reset_user_id',
                'password_reset_otp_id',
                'password_reset_method',
                'password_reset_verified',
                'verified_user_id',
                'twilio_verification_sid',
                'twilio_phone_number'
            ]
            for key in session_keys:
                if key in request.session:
                    del request.session[key]

            # Save new password
            form.save()

            # Create notification
            Notification.objects.create(
                user=user,
                notification_type='system',
                title="Password Reset",
                message="Your password has been reset successfully.",
                related_url="/accounts/settings/"
            )

            messages.success(request, 'Your password has been reset successfully. You can now log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = OTPPasswordResetForm(user)

    context = {
        'form': form,
        'user': user
    }
    return render(request, 'accounts/password_reset_confirm.html', context)


@login_required
def password_change_with_otp(request):
    """Change password with OTP verification"""
    if request.method == 'POST':
        form = OTPPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            # Send OTP before changing password
            user = request.user

            # Determine contact method based on user's preference
            contact_method = 'email'  # Default to email
            contact_value = user.email

            # If user has phone and prefers SMS, use phone
            if user.phone_number:
                # In a real app, you might have a user preference field
                # For now, we'll check both
                contact_method = 'phone'
                contact_value = user.phone_number

            # Create OTP for password change
            if contact_method == 'email':
                otp = PasswordResetOTP.create_password_reset_otp(
                    user=user,
                    email=contact_value
                )
            else:
                # For phone, use Twilio
                verification_sid, message = send_twilio_verification(contact_value)
                if verification_sid:
                    otp = PasswordResetOTP.objects.create(
                        user=user,
                        otp_code='000000',  # Placeholder
                        phone_number=contact_value,
                        expires_at=timezone.now() + timedelta(minutes=10),
                        verification_sid=verification_sid
                    )
                else:
                    messages.error(request, f'Failed to send OTP: {message}')
                    return render(request, 'accounts/password_change_with_otp.html', {'form': form})

            # Store OTP ID and form data in session
            request.session['password_change_otp_id'] = str(otp.id)
            request.session['password_change_form_data'] = {
                'old_password': form.cleaned_data['old_password'],
                'new_password1': form.cleaned_data['new_password1'],
                'new_password2': form.cleaned_data['new_password2'],
            }
            request.session['password_change_method'] = contact_method
            if contact_method == 'phone':
                request.session['password_change_twilio_sid'] = verification_sid

            messages.success(request, f'OTP has been sent to your {contact_method}. Please verify to continue.')
            return redirect('verify_password_change_otp')
    else:
        form = OTPPasswordChangeForm(request.user)

    context = {
        'form': form,
    }
    return render(request, 'accounts/password_change_with_otp.html', context)


@login_required
def verify_password_change_otp(request):
    """Verify OTP for password change"""
    otp_id = request.session.get('password_change_otp_id')
    form_data = request.session.get('password_change_form_data')
    contact_method = request.session.get('password_change_method')
    twilio_sid = request.session.get('password_change_twilio_sid')

    if not otp_id or not form_data:
        messages.error(request, 'Invalid request. Please start over.')
        return redirect('password_change_with_otp')

    try:
        otp = PasswordResetOTP.objects.get(
            id=otp_id,
            user=request.user,
            is_used=False
        )
    except PasswordResetOTP.DoesNotExist:
        messages.error(request, 'Invalid OTP request. Please start over.')
        # Clear session
        session_keys = ['password_change_otp_id', 'password_change_form_data',
                        'password_change_method', 'password_change_twilio_sid']
        for key in session_keys:
            if key in request.session:
                del request.session[key]
        return redirect('password_change_with_otp')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            # VERIFY VIA TWILIO FOR PHONE
            if contact_method == 'phone' and twilio_sid:
                success, message = verify_twilio_code(otp.phone_number, otp_code)
            else:
                # Email verification
                success, message = otp.verify_and_use(otp_code)

            if success:
                # Verify old password first
                user = request.user
                old_password = form_data['old_password']

                if not user.check_password(old_password):
                    messages.error(request, 'Your old password was entered incorrectly.')
                    # Clear session
                    session_keys = ['password_change_otp_id', 'password_change_form_data',
                                    'password_change_method', 'password_change_twilio_sid']
                    for key in session_keys:
                        if key in request.session:
                            del request.session[key]
                    return redirect('password_change_with_otp')

                # Set new password
                user.set_password(form_data['new_password1'])
                user.save()

                # Update session
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

                # Create notification
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title="Password Changed",
                    message="Your password has been changed successfully.",
                    related_url="/accounts/settings/"
                )

                # Clear session
                session_keys = ['password_change_otp_id', 'password_change_form_data',
                                'password_change_method', 'password_change_twilio_sid']
                for key in session_keys:
                    if key in request.session:
                        del request.session[key]

                messages.success(request, 'Your password has been changed successfully!')
                return redirect('settings_main')
            else:
                messages.error(request, message)
        else:
            messages.error(request, 'Please enter a valid 6-digit OTP.')
    else:
        form = VerifyOTPForm()

    # Get contact info for display
    contact_info = None
    if contact_method == 'email' and otp.email:
        # Mask email for display
        email = otp.email
        if '@' in email:
            username, domain = email.split('@')
            if len(username) > 2:
                masked_email = username[0] + '*' * (len(username) - 2) + username[-1] + '@' + domain
            else:
                masked_email = '*' * len(username) + '@' + domain
            contact_info = masked_email
    elif contact_method == 'phone' and otp.phone_number:
        # Mask phone number for display
        phone = otp.phone_number
        if len(phone) > 4:
            masked_phone = '*' * (len(phone) - 4) + phone[-4:]
        else:
            masked_phone = '*' * len(phone)
        contact_info = masked_phone

    context = {
        'form': form,
        'contact_info': contact_info,
        'contact_method': contact_method,
        'can_resend': True,
    }
    return render(request, 'accounts/verify_password_change_otp.html', context)


@login_required
def resend_otp(request, otp_type):
    """Resend OTP"""
    if otp_type == 'password_change':
        otp_id = request.session.get('password_change_otp_id')
        contact_method = request.session.get('password_change_method')

        if otp_id:
            try:
                otp = PasswordResetOTP.objects.get(id=otp_id, user=request.user)
                # Delete old OTP
                otp.delete()

                # Create new OTP
                if contact_method == 'email':
                    new_otp = PasswordResetOTP.create_password_reset_otp(
                        user=request.user,
                        email=request.user.email
                    )
                else:
                    # For phone, use Twilio
                    verification_sid, message = send_twilio_verification(request.user.phone_number)
                    if verification_sid:
                        new_otp = PasswordResetOTP.objects.create(
                            user=request.user,
                            otp_code='000000',
                            phone_number=request.user.phone_number,
                            expires_at=timezone.now() + timedelta(minutes=10),
                            verification_sid=verification_sid
                        )
                        request.session['password_change_twilio_sid'] = verification_sid
                    else:
                        messages.error(request, f'Failed to resend OTP: {message}')
                        return redirect('verify_password_change_otp')

                # Update session with new OTP ID
                request.session['password_change_otp_id'] = str(new_otp.id)

                messages.success(request, f'New OTP has been sent to your {contact_method}.')
                return redirect('verify_password_change_otp')

            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'Unable to resend OTP. Please start over.')
                return redirect('password_change_with_otp')

    elif otp_type == 'password_reset':
        user_id = request.session.get('password_reset_user_id')
        reset_method = request.session.get('password_reset_method')

        if user_id and reset_method:
            try:
                user = CustomUser.objects.get(id=user_id)

                # Get old OTP ID from session
                old_otp_id = request.session.get('password_reset_otp_id')
                if old_otp_id:
                    try:
                        old_otp = PasswordResetOTP.objects.get(id=old_otp_id, user=user)
                        old_otp.delete()
                    except PasswordResetOTP.DoesNotExist:
                        pass

                # Create new OTP
                if reset_method == 'email':
                    new_otp = PasswordResetOTP.create_password_reset_otp(
                        user=user,
                        email=user.email
                    )
                else:
                    # For phone, use Twilio
                    phone = request.session.get('twilio_phone_number', user.phone_number)
                    verification_sid, message = send_twilio_verification(phone)
                    if verification_sid:
                        new_otp = PasswordResetOTP.objects.create(
                            user=user,
                            otp_code='000000',
                            phone_number=phone,
                            expires_at=timezone.now() + timedelta(minutes=10),
                            verification_sid=verification_sid
                        )
                        request.session['twilio_verification_sid'] = verification_sid
                    else:
                        messages.error(request, f'Failed to resend OTP: {message}')
                        return redirect('password_reset_verify_otp')

                # Update session with new OTP ID
                request.session['password_reset_otp_id'] = str(new_otp.id)

                messages.success(request, f'New OTP has been sent.')
                return redirect('password_reset_verify_otp')

            except CustomUser.DoesNotExist:
                messages.error(request, 'Unable to resend OTP. Please start over.')

    messages.error(request, 'Invalid request.')
    return redirect('settings_main' if request.user.is_authenticated else 'password_reset_request')


@login_required
def send_verification_otp(request):
    """Send verification OTP for account verification"""
    if request.method == 'POST':
        form = SendOTPForm(request.POST)
        if form.is_valid():
            verification_method = form.cleaned_data['verification_method']
            email = form.cleaned_data.get('email')
            phone_number = form.cleaned_data.get('phone_number')

            user = request.user

            if verification_method == 'email':
                # Update email if different
                if email and email != user.email:
                    # Check if email is already taken
                    if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                        messages.error(request, 'This email is already registered.')
                        return redirect('send_verification_otp')
                    user.email = email
                    user.save()

                # Create OTP
                otp = OTPVerification.create_otp(
                    user=user,
                    verification_type='account_verification',
                    email=user.email
                )

                # Store OTP ID in session
                request.session['verification_otp_id'] = str(otp.id)
                request.session['verification_method'] = 'email'

                messages.success(request, f'Verification OTP has been sent to {user.email}')
                return redirect('verify_account_otp')

            else:  # phone
                # Update phone if different
                if phone_number and phone_number != user.phone_number:
                    # Check if phone is already taken
                    if CustomUser.objects.filter(phone_number=phone_number).exclude(id=user.id).exists():
                        messages.error(request, 'This phone number is already registered.')
                        return redirect('send_verification_otp')
                    user.phone_number = phone_number
                    user.save()

                # Send OTP via Twilio
                verification_sid, message = send_twilio_verification(user.phone_number)
                if verification_sid:
                    # Create OTP record
                    otp = OTPVerification.objects.create(
                        user=user,
                        verification_type='account_verification',
                        otp_code='000000',  # Placeholder
                        phone_number=user.phone_number,
                        expires_at=timezone.now() + timedelta(minutes=10),
                        verification_sid=verification_sid
                    )

                    # Store OTP ID in session
                    request.session['verification_otp_id'] = str(otp.id)
                    request.session['verification_method'] = 'phone'
                    request.session['verification_twilio_sid'] = verification_sid

                    messages.success(request, f'Verification OTP has been sent to {user.phone_number}')
                    return redirect('verify_account_otp')
                else:
                    messages.error(request, f'Failed to send OTP: {message}')
    else:
        form = SendOTPForm(initial={
            'email': request.user.email,
            'phone_number': request.user.phone_number
        })

    context = {
        'form': form,
    }
    return render(request, 'accounts/send_verification_otp.html', context)


@login_required
def verify_account_otp(request):
    """Verify account with OTP - FIXED: Ensure is_verified is properly updated"""
    otp_id = request.session.get('verification_otp_id')
    verification_method = request.session.get('verification_method')
    twilio_sid = request.session.get('verification_twilio_sid')

    if not otp_id:
        messages.error(request, 'Please request OTP first.')
        return redirect('send_verification_otp')

    try:
        otp = OTPVerification.objects.get(
            id=otp_id,
            user=request.user,
            is_verified=False
        )
    except OTPVerification.DoesNotExist:
        messages.error(request, 'Invalid OTP request. Please start over.')
        session_keys = ['verification_otp_id', 'verification_method', 'verification_twilio_sid']
        for key in session_keys:
            if key in request.session:
                del request.session[key]
        return redirect('send_verification_otp')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            # VERIFY VIA TWILIO FOR PHONE
            if verification_method == 'phone' and twilio_sid:
                success, message = verify_twilio_code(otp.phone_number, otp_code)
            else:
                # Email verification
                success, message = otp.verify_otp(otp_code)

            if success:
                # CRITICAL FIX: Mark user as verified
                user = request.user
                user.is_verified = True  # Set to True
                user.save(update_fields=['is_verified'])  # Force update only is_verified field

                print(f"DEBUG: User {user.username} is_verified set to: {user.is_verified}")

                # Mark OTP as verified
                otp.is_verified = True
                otp.verified_at = timezone.now()
                otp.save()

                # Create notification
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title="Account Verified",
                    message="Your account has been verified successfully.",
                    related_url="/accounts/profile/"
                )

                # Clear session
                session_keys = ['verification_otp_id', 'verification_method', 'verification_twilio_sid']
                for key in session_keys:
                    if key in request.session:
                        del request.session[key]

                messages.success(request, 'Your account has been verified successfully!')
                return redirect('profile')
            else:
                messages.error(request, message)
        else:
            messages.error(request, 'Please enter a valid 6-digit OTP.')
    else:
        form = VerifyOTPForm()

    # Get contact info for display
    contact_info = None
    if verification_method == 'email' and otp.email:
        # Mask email for display
        email = otp.email
        if '@' in email:
            username, domain = email.split('@')
            if len(username) > 2:
                masked_email = username[0] + '*' * (len(username) - 2) + username[-1] + '@' + domain
            else:
                masked_email = '*' * len(username) + '@' + domain
            contact_info = masked_email
    elif verification_method == 'phone' and otp.phone_number:
        # Mask phone number for display
        phone = otp.phone_number
        if len(phone) > 4:
            masked_phone = '*' * (len(phone) - 4) + phone[-4:]
        else:
            masked_phone = '*' * len(phone)
        contact_info = masked_phone

    context = {
        'form': form,
        'contact_info': contact_info,
        'verification_method': verification_method,
        'can_resend': True,
    }
    return render(request, 'accounts/verify_account_otp.html', context)


def debug_verification_status(request):
    """Debug endpoint to check verification status"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    user = request.user

    data = {
        'username': user.username,
        'email': user.email,
        'is_verified': user.is_verified,
        'phone_number': user.phone_number,
        'user_id': user.id,
    }

    # Check OTP verifications
    from accounts.models import OTPVerification
    otps = OTPVerification.objects.filter(user=user, verification_type='account_verification')
    data['otp_count'] = otps.count()
    data['verified_otps'] = otps.filter(is_verified=True).count()

    # List OTPs
    otp_list = []
    for otp in otps:
        otp_list.append({
            'id': otp.id,
            'otp_code': otp.otp_code,
            'is_verified': otp.is_verified,
            'verified_at': otp.verified_at,
            'created_at': otp.created_at,
            'expired': otp.is_expired()
        })
    data['otps'] = otp_list

    return JsonResponse(data)


# Add this temporary function to manually fix verification - REMOVE AFTER USE
@login_required
def force_verify_user(request):
    """Force verify current user - TEMPORARY - REMOVE AFTER USE"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Admin only'}, status=403)

    user = request.user
    user.is_verified = True
    user.save()

    return JsonResponse({
        'success': True,
        'username': user.username,
        'is_verified': user.is_verified,
        'message': 'User manually verified'
    })


# Add this to debug session
@login_required
def debug_session(request):
    """Debug session data"""
    session_data = dict(request.session.items())
    return JsonResponse({
        'session': session_data,
        'user_is_verified': request.user.is_verified,
        'username': request.user.username
    })


# Add this function to test profile update
@login_required
def test_profile_update(request):
    """Test profile update - TEMPORARY"""
    user = request.user

    # Test update
    user.first_name = "TestFirstName"
    user.last_name = "TestLastName"
    user.save(update_fields=['first_name', 'last_name'])

    # Refresh from database
    user.refresh_from_db()

    return JsonResponse({
        'success': True,
        'message': 'Test update applied',
        'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_verified': user.is_verified
        }
    })


# Add this function to force refresh profile
@login_required
def refresh_profile(request):
    """Force refresh profile data"""
    # Get fresh user instance
    fresh_user = CustomUser.objects.get(id=request.user.id)

    return JsonResponse({
        'success': True,
        'user': {
            'id': fresh_user.id,
            'username': fresh_user.username,
            'first_name': fresh_user.first_name,
            'last_name': fresh_user.last_name,
            'email': fresh_user.email,
            'phone': fresh_user.phone_number,
            'verified': fresh_user.is_verified
        }
    })


def debug_google_oauth(request):
    """Debug view to see the exact Google OAuth redirect URI"""
    try:
        # Create Google OAuth2 backend
        backend = GoogleOAuth2()

        # Force use the correct redirect URI
        backend.redirect_uri = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI

        # Get the auth URL with all parameters
        auth_url = backend.auth_url()

        # Parse the URL to see the redirect_uri parameter
        parsed = urllib.parse.urlparse(auth_url)
        query_params = urllib.parse.parse_qs(parsed.query)

        # Get the redirect_uri from the URL
        redirect_uri_from_url = query_params.get('redirect_uri', ['NOT FOUND'])[0]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google OAuth Debug</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .match {{ color: green; font-weight: bold; }}
                .mismatch {{ color: red; font-weight: bold; }}
                .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .success {{ background: #e8f5e8; border-color: #4CAF50; }}
                .error {{ background: #ffebee; border-color: #f44336; }}
            </style>
        </head>
        <body>
            <h1>🔍 Google OAuth Debug Information</h1>

            <div class="box {'success' if redirect_uri_from_url == settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI else 'error'}">
                <h2>Redirect URI Status</h2>
                <p>
                    URL Match: 
                    <span class="{'match' if redirect_uri_from_url == settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI else 'mismatch'}">
                        {redirect_uri_from_url == settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}
                    </span>
                </p>
            </div>

            <div class="box">
                <h2>🔗 Full Auth URL Generated:</h2>
                <pre>{auth_url}</pre>
            </div>

            <div class="box">
                <h2>🔄 Redirect URI from Generated URL:</h2>
                <pre>{redirect_uri_from_url}</pre>
            </div>

            <div class="box">
                <h2>⚙️ Settings.py Redirect URI:</h2>
                <pre>{settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}</pre>
            </div>

            <div class="box">
                <h2>📋 What to add to Google Cloud Console:</h2>
                <pre>{settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}</pre>
                <p>Copy this EXACT URL and add it to Google Cloud Console > Credentials > OAuth 2.0 Client IDs > Authorized redirect URIs</p>
            </div>

            <div class="box">
                <h2>🔑 Current Configuration:</h2>
                <ul>
                    <li>Client ID: {'✅ SET' if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY else '❌ MISSING'}</li>
                    <li>Client Secret: {'✅ SET' if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET else '❌ MISSING'}</li>
                    <li>Environment: {'Production (Render)' if 'RENDER' in os.environ else 'Development (Local)'}</li>
                    <li>DEBUG Mode: {settings.DEBUG}</li>
                </ul>
            </div>

            <div class="box">
                <h2>🚨 Action Required:</h2>
                <ol>
                    <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a></li>
                    <li>Select your project</li>
                    <li>Go to APIs & Services → Credentials</li>
                    <li>Click on your OAuth 2.0 Client ID</li>
                    <li>In "Authorized redirect URIs", add:</li>
                    <pre>{settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI}</pre>
                    <li>Remove any other redirect URIs</li>
                    <li>Click SAVE</li>
                </ol>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>")


def test_google_login(request):
    """Test Google login button"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Google Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .button { 
                background: #4285F4; 
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 4px; 
                font-size: 16px; 
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 20px;
            }
            .button:hover { background: #357ae8; }
        </style>
    </head>
    <body>
        <h1>Test Google Login</h1>
        <p>Click the button below to test Google OAuth:</p>
        <a href="/accounts/login/google-oauth2/" class="button">Sign in with Google</a>
        <p><a href="/accounts/debug-google-oauth/">View Debug Information</a></p>
    </body>
    </html>
    """
    return HttpResponse(html)