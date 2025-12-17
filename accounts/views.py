# messenger_app/accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .forms import CustomUserCreationForm
from .models import CustomUser, Notification
from .models import FriendRequest, Friendship


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # FIX: Specify the authentication backend
            from django.contrib.auth import authenticate, login

            # Authenticate with the ModelBackend
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                backend='django.contrib.auth.backends.ModelBackend'
            )

            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('chat_home')
            else:
                # If authentication fails, still log in using the user object
                # This is a fallback
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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

            # Update all profile fields - FIXED: Use get() method with proper fallback
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.bio = request.POST.get('bio', user.bio)
            user.location = request.POST.get('location', user.location)
            user.website = request.POST.get('website', user.website)

            # Handle date_of_birth properly
            date_of_birth = request.POST.get('date_of_birth')
            if date_of_birth:
                user.date_of_birth = date_of_birth
            elif date_of_birth == '':  # If empty string, set to None
                user.date_of_birth = None

            user.gender = request.POST.get('gender', user.gender)

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