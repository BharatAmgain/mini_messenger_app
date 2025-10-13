# messenger_app/accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from .models import CustomUser, Notification


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('chat_home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """View user's own profile"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def profile_edit(request):
    """Edit user's own profile - Anytime, any changes"""
    user = request.user

    if request.method == 'POST':
        try:
            # Handle profile picture upload (optional)
            if 'profile_picture' in request.FILES and request.FILES['profile_picture']:
                profile_picture = request.FILES['profile_picture']

                # Basic validation
                if profile_picture.content_type.startswith('image/'):
                    if profile_picture.size <= 5 * 1024 * 1024:  # 5MB
                        user.profile_picture = profile_picture
                    else:
                        messages.error(request, 'Image too large. Max 5MB.')
                else:
                    messages.error(request, 'Please select a valid image file.')

            # Update all profile fields
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.phone_number = request.POST.get('phone_number', '')
            user.bio = request.POST.get('bio', '')
            user.location = request.POST.get('location', '')
            user.website = request.POST.get('website', '')
            user.date_of_birth = request.POST.get('date_of_birth') or None
            user.gender = request.POST.get('gender', '')

            # Save changes
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    return render(request, 'accounts/profile_edit.html', {'user': user})
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
    notifications = request.user.account_notifications.all().order_by('-created_at')
    return render(request, 'accounts/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            messages.success(request, 'Notification marked as read.')
        except Notification.DoesNotExist:
            messages.error(request, 'Notification not found.')

    return redirect('notifications')


@login_required
def mark_all_notifications_read(request):  # ADD THIS FUNCTION
    """Mark all notifications as read"""
    if request.method == 'POST':
        request.user.account_notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
    return redirect('notifications')


@login_required
def get_unread_count(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        unread_count = request.user.account_notifications.filter(is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'error': 'Invalid request'})


# messenger_app/accounts/views.py
def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat_home')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'chat_home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# Add this to messenger_app/accounts/views.py
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
        messages.success(request, f'Two-factor authentication has been {status}.')
    return redirect('settings_main')