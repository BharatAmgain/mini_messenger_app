
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

from .models import (
    Conversation,
    Message,
    UserStatus,
    ChatNotification,
    GroupInvitation,
    BlockedUser,
)

from accounts.models import (
    CustomUser,
    Notification,
    Friendship,
    FriendRequest,
)

from .utils import EmojiManager
import emoji
import uuid
import json
import os


@login_required
def chat_home(request):
    """Chat home page with conversations and search"""
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')

    # Prepare conversation data with other user info
    conversation_data = []
    for conversation in conversations:
        # Get display info based on conversation type
        if conversation.is_group:
            display_name = conversation.group_name
            display_photo = conversation.group_photo.url if conversation.group_photo else None
            is_online = False  # Groups don't have online status
        else:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            display_name = other_user.username if other_user else "Unknown User"
            display_photo = other_user.profile_picture.url if other_user and other_user.profile_picture else None
            is_online = other_user.status.online if other_user and hasattr(other_user, 'status') else False

        # Get unread count
        unread_count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).count()

        # Get last message
        last_message = conversation.messages.last()

        conversation_data.append({
            'conversation': conversation,
            'display_name': display_name,
            'display_photo': display_photo,
            'is_online': is_online,
            'unread_count': unread_count,
            'last_message': last_message,
            'is_group': conversation.is_group
        })

    # Get unread notifications count - FIXED: Use account_notifications
    unread_notifications_count = request.user.account_notifications.filter(is_read=False).count()

    # Get pending group invitations
    pending_invitations = GroupInvitation.objects.filter(
        invited_user=request.user,
        status='pending'
    ).count()

    context = {
        'conversation_data': conversation_data,
        'unread_notifications_count': unread_notifications_count,
        'pending_invitations_count': pending_invitations,
    }
    return render(request, 'chat/chat_home.html', context)


@login_required
def start_chat(request):
    """Start a new chat with email or phone number - Updated with friendship check"""
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip()

        if not email_or_phone:
            messages.error(request, 'Please enter an email or phone number.')
            return redirect('start_chat')

        # Search for user by email or phone number
        try:
            if '@' in email_or_phone:
                # Search by email
                user = CustomUser.objects.get(email=email_or_phone)
            else:
                # Search by phone number
                user = CustomUser.objects.get(phone_number=email_or_phone)
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found. Please check the email or phone number.')
            return redirect('start_chat')

        if user == request.user:
            messages.error(request, 'You cannot start a chat with yourself.')
            return redirect('start_chat')

        # Check if friends
        if not Friendship.are_friends(request.user, user):
            messages.error(request, 'You need to be friends to chat with this user.')
            return redirect('start_chat')

        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=user
        ).filter(
            is_group=False
        ).first()

        if existing_conversation:
            return redirect('conversation', conversation_id=existing_conversation.id)

        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, user)

        messages.success(request, f'Started chat with {user.username}')
        return redirect('conversation', conversation_id=conversation.id)

    return render(request, 'chat/start_chat.html')


@login_required
def create_group(request):
    """Create a new group chat"""
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip()
        group_description = request.POST.get('group_description', '').strip()
        participant_ids = request.POST.getlist('participants')

        if not group_name:
            messages.error(request, 'Group name is required.')
            return redirect('create_group')

        # Create group conversation
        conversation = Conversation.objects.create(
            is_group=True,
            group_name=group_name,
            group_description=group_description,
            created_by=request.user
        )

        # Add creator as participant and admin
        conversation.participants.add(request.user)
        conversation.admins.add(request.user)

        # Add other participants
        for user_id in participant_ids:
            try:
                user = CustomUser.objects.get(id=user_id)
                if user != request.user:
                    conversation.participants.add(user)
                    # Create account notification - FIXED: Use Notification model
                    Notification.objects.create(
                        user=user,
                        notification_type='group_invite',
                        title="Group Invitation",
                        message=f"You were added to group '{group_name}' by {request.user.username}",
                        related_url=f"/chat/{conversation.id}/"
                    )
            except CustomUser.DoesNotExist:
                continue

        # Create welcome message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"Welcome to {group_name}! This group was created by {request.user.username}.",
            is_read=True
        )

        messages.success(request, f'Group "{group_name}" created successfully!')
        return redirect('conversation', conversation_id=conversation.id)

    # Get users to invite (exclude current user)
    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'chat/create_group.html', {'users': users})


@login_required
def search_users(request):
    """Search users by username, email, or phone number"""
    query = request.GET.get('q', '').strip()

    if query:
        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id).distinct()[:10]
    else:
        users = CustomUser.objects.none()

    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'chat/search_users.html', context)


@login_required
def conversation(request, conversation_id):
    """View conversation and messages - Updated with friendship check"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # For direct chats, check if friends
    if not conversation.is_group:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            # Check if blocked in either direction
            is_blocked = BlockedUser.objects.filter(
                Q(user=request.user, blocked_user=other_user) |
                Q(user=other_user, blocked_user=request.user)
            ).exists()

            if is_blocked:
                messages.error(request, 'This conversation is not available due to blocking.')
                return redirect('chat_home')

            # Check if friends
            if not Friendship.are_friends(request.user, other_user):
                messages.error(request, 'You need to be friends to chat with this user.')
                return redirect('chat_home')

    # Mark messages as read when viewing conversation
    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user)

    for message in unread_messages:
        message.is_read = True
        message.save()

    # Mark notifications as read when viewing conversation - FIXED: Use account_notifications
    request.user.account_notifications.filter(
        notification_type='message',
        related_url=f"/chat/{conversation.id}/"
    ).update(is_read=True)

    # Get messages
    messages_list = conversation.messages.all().order_by('timestamp')

    # Get context based on conversation type
    if conversation.is_group:
        context = {
            'conversation': conversation,
            'messages': messages_list,
            'is_group': True,
            'group_members': conversation.participants.all(),
            'group_admins': conversation.admins.all(),
        }
    else:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        context = {
            'conversation': conversation,
            'messages': messages_list,
            'other_user': other_user,
            'is_group': False,
        }

    return render(request, 'chat/conversation.html', context)


@login_required
def group_settings(request, conversation_id):
    """Group settings and management"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        is_group=True
    )

    # Check if user is a participant
    if not conversation.participants.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this group.')
        return redirect('chat_home')

    if request.method == 'POST':
        if 'add_member' in request.POST:
            email_or_phone = request.POST.get('new_member', '').strip()
            try:
                if '@' in email_or_phone:
                    user = CustomUser.objects.get(email=email_or_phone)
                else:
                    user = CustomUser.objects.get(phone_number=email_or_phone)

                if user not in conversation.participants.all():
                    conversation.participants.add(user)
                    # FIXED: Use Notification model
                    Notification.objects.create(
                        user=user,
                        notification_type='group_invite',
                        title="Group Invitation",
                        message=f"You were added to group '{conversation.group_name}' by {request.user.username}",
                        related_url=f"/chat/{conversation.id}/"
                    )
                    messages.success(request, f'{user.username} added to group.')
                else:
                    messages.warning(request, 'User is already in the group.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')

            # Redirect to avoid resubmission
            return redirect('group_settings', conversation_id=conversation_id)

        elif 'remove_member' in request.POST:
            user_id = request.POST.get('user_id')
            try:
                user = CustomUser.objects.get(id=user_id)
                if user != request.user and user in conversation.participants.all():
                    conversation.participants.remove(user)

                    # Create system message
                    Message.objects.create(
                        conversation=conversation,
                        sender=request.user,
                        content=f"{user.username} was removed from the group by {request.user.username}",
                        is_read=True
                    )

                    messages.success(request, f'{user.username} removed from group.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')

            # Redirect to avoid resubmission
            return redirect('group_settings', conversation_id=conversation_id)

        elif 'update_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            group_description = request.POST.get('group_description', '').strip()

            if group_name:
                conversation.group_name = group_name
            if group_description:
                conversation.group_description = group_description

            # Handle group photo upload
            if 'group_photo' in request.FILES and request.FILES['group_photo']:
                group_photo = request.FILES['group_photo']

                # Basic validation
                if group_photo.content_type.startswith('image/'):
                    if group_photo.size <= 5 * 1024 * 1024:  # 5MB
                        conversation.group_photo = group_photo
                    else:
                        messages.error(request, 'Image too large. Max 5MB.')
                else:
                    messages.error(request, 'Please select a valid image file.')

            conversation.save()
            messages.success(request, 'Group updated successfully.')

            # Redirect to avoid resubmission
            return redirect('group_settings', conversation_id=conversation_id)

        elif 'remove_group_photo' in request.POST:
            # Remove group photo
            if conversation.group_photo:
                conversation.group_photo.delete(save=True)
                messages.success(request, 'Group photo removed successfully.')
            else:
                messages.warning(request, 'No group photo to remove.')

            # Redirect to avoid resubmission
            return redirect('group_settings', conversation_id=conversation_id)

        elif 'leave_group' in request.POST:
            # User wants to leave the group
            conversation.participants.remove(request.user)

            # Remove from admins if they were an admin
            if request.user in conversation.admins.all():
                conversation.admins.remove(request.user)

            # Create system message
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=f"{request.user.username} left the group",
                is_read=True
            )

            messages.success(request, f'You have left the group "{conversation.group_name}".')
            return redirect('chat_home')

        elif 'delete_group' in request.POST:
            # Only admins can delete group
            if request.user in conversation.admins.all():
                group_name = conversation.group_name
                conversation.delete()
                messages.success(request, f'Group "{group_name}" has been deleted.')
                return redirect('chat_home')
            else:
                messages.error(request, 'Only group admins can delete the group.')
                return redirect('group_settings', conversation_id=conversation_id)

    # Get all users for adding new members
    all_users = CustomUser.objects.exclude(
        Q(id=request.user.id) | Q(conversations=conversation)
    )

    context = {
        'conversation': conversation,
        'group_members': conversation.participants.all(),
        'group_admins': conversation.admins.all(),
        'all_users': all_users,
    }
    return render(request, 'chat/group_settings.html', context)


@login_required
def leave_group(request, conversation_id):
    """Leave a group"""
    if request.method == 'POST':
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user,
            is_group=True
        )

        # Remove user from group
        conversation.participants.remove(request.user)

        # Remove from admins if they were an admin
        if request.user in conversation.admins.all():
            conversation.admins.remove(request.user)

        # Create system message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"{request.user.username} left the group",
            is_read=True
        )

        messages.success(request, f'You have left the group "{conversation.group_name}".')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'You have left the group "{conversation.group_name}".'
            })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})

    return redirect('chat_home')


@login_required
def invite_to_group(request, conversation_id):
    """Invite users to group via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, is_group=True)
        user_ids = request.POST.getlist('user_ids[]')

        invited_users = []
        for user_id in user_ids:
            try:
                user = CustomUser.objects.get(id=user_id)
                if user not in conversation.participants.all():
                    conversation.participants.add(user)
                    # FIXED: Use Notification model
                    Notification.objects.create(
                        user=user,
                        notification_type='group_invite',
                        title="Group Invitation",
                        message=f"You were invited to group '{conversation.group_name}' by {request.user.username}",
                        related_url=f"/chat/{conversation.id}/"
                    )
                    invited_users.append(user.username)
            except CustomUser.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'message': f'Invited {len(invited_users)} users to the group',
            'invited_users': invited_users
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@csrf_exempt
def typing_indicator(request, conversation_id):
    """Handle typing indicators"""
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        data = json.loads(request.body)
        is_typing = data.get('is_typing', False)

        if is_typing:
            conversation.typing_users.add(request.user)
        else:
            conversation.typing_users.remove(request.user)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_typing_status(request, conversation_id):
    """Get typing status for a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    # Get typing users (excluding current user)
    typing_users = conversation.typing_users.exclude(id=request.user.id)
    typing_usernames = [user.username for user in typing_users]

    return JsonResponse({
        'typing_users': typing_usernames,
        'is_typing': len(typing_usernames) > 0
    })


@login_required
def get_new_messages(request, conversation_id):
    """Get new messages for real-time updates"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

        # Get messages that are not from current user and not read
        new_messages = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user)

        messages_data = []
        for message in new_messages:
            message_data = {
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'is_own': False,
                'is_read': message.is_read,
                'message_type': message.message_type,
                'is_edited': message.is_edited,
                'is_unsent': message.is_unsent,
                'reactions': message.get_reaction_summary(),
                'user_reaction': message.get_user_reaction(request.user)
            }

            # Add file information if it's a media message
            if message.message_type != 'text':
                message_data['file_url'] = message.file.url if message.file else None
                message_data['file_name'] = message.file_name
                message_data['file_size'] = message.get_file_size_display()
                message_data['is_image'] = message.is_image_file()
                message_data['is_video'] = message.is_video_file()
                message_data['is_audio'] = message.is_audio_file()

            messages_data.append(message_data)

            # Mark as read
            message.is_read = True
            message.save()

        return JsonResponse({
            'success': True,
            'new_messages': messages_data,
            'has_new_messages': len(messages_data) > 0
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_notifications(request):
    """Get user notifications for dropdown - FIXED: Use account_notifications"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        notifications = request.user.account_notifications.filter(
            is_read=False,
            is_archived=False
        ).order_by('-created_at')[:10]  # Show 10 latest unread notifications

        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'content': notification.message,
                'title': notification.title,
                'related_url': notification.related_url,
                'created_at': notification.created_at.strftime('%H:%M'),
                'is_read': notification.is_read
            })

        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': notifications.count()
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def send_message_ajax(request, conversation_id):
    """Send message via AJAX - Now supports emojis"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

        # Check for blocks in direct chats
        if not conversation.is_group:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            if other_user:
                is_blocked = BlockedUser.objects.filter(
                    Q(user=request.user, blocked_user=other_user) |
                    Q(user=other_user, blocked_user=request.user)
                ).exists()

                if is_blocked:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot send message. User is blocked.'
                    })

        content = request.POST.get('content', '').strip()
        file = request.FILES.get('file')

        # Validate file size (50MB limit)
        if file and file.size > 50 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File too large. Maximum size is 50MB.'
            })

        if content or file:
            # Determine message type
            message_type = 'text'
            file_name = None
            file_size = None

            if file:
                file_name = file.name
                file_size = file.size

                # Determine message type based on file content type
                if file.content_type.startswith('image/'):
                    message_type = 'image'
                elif file.content_type.startswith('video/'):
                    message_type = 'video'
                elif file.content_type.startswith('audio/'):
                    message_type = 'audio'
                else:
                    message_type = 'file'
            else:
                # Check if it's an emoji message
                emoji_count = sum(1 for char in content if emoji.is_emoji(char))
                total_chars = len(content.strip())

                if (emoji_count > 0 and total_chars <= 3) or (total_chars > 0 and emoji_count / total_chars > 0.7):
                    message_type = 'emoji'

            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
                message_type=message_type,
                file=file if file else None,
                file_name=file_name,
                file_size=file_size
            )
            conversation.updated_at = timezone.now()
            conversation.save()

            # Create notifications for other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                # Check if participant blocked the sender
                is_blocked = BlockedUser.objects.filter(
                    user=participant,
                    blocked_user=request.user
                ).exists()

                if not is_blocked:
                    # Create appropriate notification message
                    if message_type == 'text':
                        notification_message = content[:100] + "..." if len(content) > 100 else content
                    elif message_type == 'emoji':
                        notification_message = "Sent an emoji"
                    else:
                        notification_message = f"Sent a {message_type}"

                    Notification.objects.create(
                        user=participant,
                        notification_type='message',
                        title=f"New message from {request.user.username}",
                        message=notification_message,
                        related_url=f"/chat/{conversation.id}/"
                    )

            # Prepare response data
            response_data = {
                'success': True,
                'message_id': str(message.id),
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'sender': message.sender.username,
                'is_own': True,
                'is_edited': False,
                'is_unsent': False,
                'reactions': {},
                'user_reaction': None,
                'message_type': message.message_type
            }

            # Add file information if it's a media message
            if message.message_type != 'text' and message.message_type != 'emoji':
                response_data['file_url'] = message.file.url if message.file else None
                response_data['file_name'] = message.file_name
                response_data['file_size'] = message.get_file_size_display()
                response_data['is_image'] = message.is_image_file()
                response_data['is_video'] = message.is_video_file()
                response_data['is_audio'] = message.is_audio_file()

            return JsonResponse(response_data)
        else:
            return JsonResponse({'success': False, 'error': 'Message content or file is required'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def search_emojis(request):
    """Search emojis via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()

        if query:
            results = EmojiManager.search_emojis(query)
        else:
            # Return popular emojis if no query
            results = EmojiManager.get_all_emojis()[:30]

        return JsonResponse({
            'success': True,
            'emojis': results,
            'query': query
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_emoji_categories(request):
    """Get emoji categories via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        categories = EmojiManager.get_emoji_categories()
        return JsonResponse({
            'success': True,
            'categories': categories
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_messages_ajax(request, conversation_id):
    """Get messages via AJAX"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        messages_list = conversation.messages.all().order_by('timestamp')

        messages_data = []
        for message in messages_list:
            message_data = {
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'is_own': message.sender.id == request.user.id,
                'is_read': message.is_read,
                'is_edited': message.is_edited,
                'is_unsent': message.is_unsent,
                'reactions': message.get_reaction_summary(),
                'user_reaction': message.get_user_reaction(request.user),
                'message_type': message.message_type
            }

            # Add file information if it's a media message
            if message.message_type != 'text':
                message_data['file_url'] = message.file.url if message.file else None
                message_data['file_name'] = message.file_name
                message_data['file_size'] = message.get_file_size_display()
                message_data['is_image'] = message.is_image_file()
                message_data['is_video'] = message.is_video_file()
                message_data['is_audio'] = message.is_audio_file()

            messages_data.append(message_data)

        return JsonResponse({'messages': messages_data})

    return JsonResponse({'error': 'Invalid request'})


@csrf_exempt
@login_required
def update_online_status(request):
    """Update user's online status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_online = data.get('online', True)

            # Update user's online status
            user = request.user
            user.is_online = is_online
            user.last_seen = timezone.now()
            user.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def edit_message(request, message_id):
    """Edit a message"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            message = Message.objects.get(id=message_id, sender=request.user)

            if message.is_unsent:
                return JsonResponse({'success': False, 'error': 'Cannot edit unsent message'})

            data = json.loads(request.body)
            new_content = data.get('content', '').strip()

            if new_content and new_content != message.content:
                message.content = new_content
                message.is_edited = True
                message.edited_at = timezone.now()
                message.save()

                return JsonResponse({
                    'success': True,
                    'message_id': str(message.id),
                    'new_content': message.content,
                    'is_edited': True
                })

            return JsonResponse({'success': False, 'error': 'Invalid content'})

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@csrf_exempt
def unsend_message(request, message_id):
    """Unsend (delete) a message"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            message = Message.objects.get(id=message_id, sender=request.user)
            message.is_unsent = True
            message.content = "This message was unsent"
            message.save()

            return JsonResponse({
                'success': True,
                'message_id': str(message.id)
            })

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@csrf_exempt
def react_to_message(request, message_id):
    """Add reaction to a message"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            message = Message.objects.get(id=message_id)

            if message.is_unsent:
                return JsonResponse({'success': False, 'error': 'Cannot react to unsent message'})

            data = json.loads(request.body)
            reaction = data.get('reaction', '')

            # Validate reaction (basic emoji validation)
            if reaction and len(reaction) <= 10:  # Basic length check for emojis
                success = message.add_reaction(request.user, reaction)

                if success:
                    return JsonResponse({
                        'success': True,
                        'message_id': str(message.id),
                        'reactions': message.get_reaction_summary(),
                        'user_reaction': message.reactions.get(str(request.user.id))
                    })

            return JsonResponse({'success': False, 'error': 'Invalid reaction'})

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def discover_users(request):
    """Merged page for discovering all users and searching users"""
    query = request.GET.get('q', '').strip()

    # Get users blocked by current user
    blocked_users_ids = BlockedUser.objects.filter(user=request.user).values_list('blocked_user_id', flat=True)

    # Get users who blocked current user
    blocked_by_ids = BlockedUser.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)

    # Combine both sets of blocked users
    all_blocked_ids = set(blocked_users_ids) | set(blocked_by_ids)

    # Get users based on search query or show all
    if query:
        # Search mode
        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(
            Q(id=request.user.id) | Q(id__in=all_blocked_ids)
        ).distinct().order_by('username')
        is_search = True
        total_users = users.count()
    else:
        # Discovery mode - show all users
        users = CustomUser.objects.exclude(
            Q(id=request.user.id) | Q(id__in=all_blocked_ids)
        ).order_by('-date_joined')
        is_search = False
        total_users = users.count()

    # Check which users are online and add friend status
    online_users = []
    users_with_status = []

    for user in users:
        if hasattr(user, 'status') and user.status.online:
            online_users.append(user.id)

        # Get friend status
        friend_status = user.get_friend_status(request.user)

        # Get received request ID if applicable
        received_request_id = None
        if friend_status == 'request_received':
            received_request = FriendRequest.objects.filter(
                from_user=user,
                to_user=request.user,
                status='pending'
            ).first()
            if received_request:
                received_request_id = received_request.id

        # Create a dictionary with user info and status
        user_info = {
            'user': user,
            'friend_status': friend_status,
            'received_request_id': received_request_id,
            'is_online': user.id in online_users
        }
        users_with_status.append(user_info)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users_with_status, 20)  # 20 users per page

    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    context = {
        'users_page': users_page,
        'online_users': online_users,
        'total_users': total_users,
        'query': query,
        'is_search': is_search,
    }
    return render(request, 'chat/discover_users.html', context)


# --------------------------------------------------
@login_required
def block_user(request, user_id):
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid request'})
        return redirect('discover_users')

    try:
        user_to_block = CustomUser.objects.get(id=user_id)

        if user_to_block == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot block yourself.'})

        # Create block (avoid duplicates)
        BlockedUser.objects.get_or_create(
            user=request.user,
            blocked_user=user_to_block
        )

        # Cancel pending friend requests (both directions)
        FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=user_to_block) |
            Q(from_user=user_to_block, to_user=request.user),
            status='pending'
        ).update(status='cancelled')

        # Remove friendship if exists
        Friendship.objects.filter(
            (Q(user1=request.user) & Q(user2=user_to_block)) |
            (Q(user1=user_to_block) & Q(user2=request.user))
        ).delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'You have blocked {user_to_block.username}.'
            })

        messages.success(request, f'You have blocked {user_to_block.username}.')
        return redirect('discover_users')

    except CustomUser.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'User not found.'})
        messages.error(request, 'User not found.')
        return redirect('discover_users')

        @login_required
        def unblock_user(request, user_id):
            if request.method != 'POST':
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Invalid request'})
                return redirect('blocked_users')

            try:
                user_to_unblock = CustomUser.objects.get(id=user_id)

                blocked = BlockedUser.objects.filter(
                    user=request.user,
                    blocked_user=user_to_unblock
                )

                if not blocked.exists():
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'User is not blocked.'})
                    messages.error(request, 'User is not blocked.')
                    return redirect('blocked_users')

                blocked.delete()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'You have unblocked {user_to_unblock.username}.'
                    })

                messages.success(request, f'You have unblocked {user_to_unblock.username}.')
                return redirect('blocked_users')

            except CustomUser.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'User not found.'})
                messages.error(request, 'User not found.')
                return redirect('blocked_users')

        @login_required
        def blocked_users(request):
            blocked_users = BlockedUser.objects.filter(
                user=request.user
            ).select_related('blocked_user')

            return render(request, 'chat/blocked_users.html', {
                'blocked_users': blocked_users
            })

        # Add this function to your existing chat/views.py file
        # Make sure to add it at the end of the file, before any imports

        @login_required
        def quick_chat(request, user_id):
            """Start a quick chat with any user - Updated with friendship check"""
            try:
                target_user = CustomUser.objects.get(id=user_id)

                # Check if user is blocked in either direction
                is_blocked = BlockedUser.objects.filter(
                    Q(user=request.user, blocked_user=target_user) |
                    Q(user=target_user, blocked_user=request.user)
                ).exists()

                if is_blocked:
                    messages.error(request, 'You cannot start a chat with this user due to blocking.')
                    return redirect('discover_users')

                # Check if friends
                if not Friendship.are_friends(request.user, target_user):
                    messages.error(request, 'You need to be friends to chat with this user.')
                    return redirect('discover_users')

                # Check if conversation already exists
                existing_conversation = Conversation.objects.filter(
                    participants=request.user
                ).filter(
                    participants=target_user
                ).filter(
                    is_group=False
                ).first()

                if existing_conversation:
                    return redirect('conversation', conversation_id=existing_conversation.id)

                # Create new conversation
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, target_user)

                messages.success(request, f'Started chat with {target_user.username}')
                return redirect('conversation', conversation_id=conversation.id)

            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('discover_users')

