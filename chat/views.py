# messenger_app/chat/views.py - COMPLETE WITH MOBILE SUPPORT
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Subquery, OuterRef
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db import transaction
from django.conf import settings
import json
import uuid
import emoji
import os
import logging

from .models import Conversation, Message, UserStatus, GroupInvitation, BlockedUser
from accounts.models import CustomUser, Notification, Friendship, FriendRequest
from .utils import EmojiManager

logger = logging.getLogger(__name__)


@login_required
def chat_home(request):
    """Chat home page with conversations and search"""
    # Get conversations where user is a participant, ordered by last activity
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Subquery(
            Message.objects.filter(
                conversation=OuterRef('pk')
            ).order_by('-timestamp').values('timestamp')[:1]
        )
    ).order_by('-last_message_time', '-updated_at')

    # Prepare conversation data
    conversation_data = []
    for conversation in conversations:
        if conversation.is_group:
            display_name = conversation.group_name or "Group Chat"
            display_photo = conversation.group_photo.url if conversation.group_photo else None
            is_online = False
            unread_count = Message.objects.filter(
                conversation=conversation,
                is_read=False
            ).exclude(sender=request.user).count()
        else:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            if other_user:
                display_name = other_user.username
                display_photo = other_user.profile_picture.url if other_user.profile_picture else None
                is_online = other_user.status.online if hasattr(other_user, 'status') else False
                unread_count = Message.objects.filter(
                    conversation=conversation,
                    sender=other_user,
                    is_read=False
                ).count()
            else:
                display_name = "Unknown User"
                display_photo = None
                is_online = False
                unread_count = 0

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

    # Get notifications
    unread_notifications_count = request.user.account_notifications.filter(is_read=False).count()

    context = {
        'conversation_data': conversation_data,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'chat/chat_home.html', context)


@login_required
def start_chat(request):
    """Start a new chat with email or phone number"""
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip()

        if not email_or_phone:
            messages.error(request, 'Please enter an email or phone number.')
            return redirect('start_chat')

        try:
            if '@' in email_or_phone:
                user = CustomUser.objects.get(email=email_or_phone)
            else:
                user = CustomUser.objects.get(phone_number=email_or_phone)
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('start_chat')

        if user == request.user:
            messages.error(request, 'You cannot chat with yourself.')
            return redirect('start_chat')

        # Check if already friends
        if not Friendship.are_friends(request.user, user):
            messages.error(request, 'You need to be friends to chat with this user.')
            return redirect('start_chat')

        # Check for existing conversation
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
        conversation.save()

        messages.success(request, f'Started chat with {user.username}')
        return redirect('conversation', conversation_id=conversation.id)

    return render(request, 'chat/start_chat.html')


@login_required
def start_chat_with_user(request, user_id):
    """Start chat directly with user ID"""
    try:
        user = CustomUser.objects.get(id=user_id)

        if user == request.user:
            messages.error(request, 'You cannot chat with yourself.')
            return redirect('chat_home')

        # Check if friends
        if not Friendship.are_friends(request.user, user):
            messages.error(request, 'You need to be friends to chat with this user.')
            return redirect('discover_users')

        # Check for existing conversation
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
        conversation.save()

        return redirect('conversation', conversation_id=conversation.id)

    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('chat_home')


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
                    # Send notification
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
        ).exclude(id=request.user.id).distinct()[:20]
    else:
        users = CustomUser.objects.none()

    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'chat/search_users.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def conversation(request, conversation_id):
    """View conversation and messages - handles both GET and POST"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('created_by').prefetch_related('participants', 'admins'),
        id=conversation_id,
        participants=request.user
    )

    if request.method == 'POST':
        return send_message(request, conversation_id)

    # For direct chats, check if friends
    if not conversation.is_group:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            # Check if blocked
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

    # Mark messages as read
    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user)

    for message in unread_messages:
        message.is_read = True
        message.save()

    # Mark notifications as read
    Notification.objects.filter(
        user=request.user,
        notification_type='message',
        related_url=f"/chat/{conversation.id}/",
        is_read=False
    ).update(is_read=True)

    # Get messages with related data
    messages_list = conversation.messages.select_related('sender').all().order_by('timestamp')

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
def send_message(request, conversation_id):
    """Send message (both regular POST and AJAX)"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # For direct chats, check if friends
    if not conversation.is_group:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            # Check if blocked
            is_blocked = BlockedUser.objects.filter(
                Q(user=request.user, blocked_user=other_user) |
                Q(user=other_user, blocked_user=request.user)
            ).exists()

            if is_blocked:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot send message. User is blocked.'
                    })
                messages.error(request, 'Cannot send message. User is blocked.')
                return redirect('conversation', conversation_id=conversation_id)

            # Check if friends
            if not Friendship.are_friends(request.user, other_user):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'You need to be friends to chat with this user.'
                    })
                messages.error(request, 'You need to be friends to chat with this user.')
                return redirect('conversation', conversation_id=conversation_id)

    content = request.POST.get('content', '').strip()
    file = request.FILES.get('file')

    # Validate file size
    if file and file.size > 50 * 1024 * 1024:  # 50MB
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'File too large. Maximum size is 50MB.'
            })
        messages.error(request, 'File too large. Maximum size is 50MB.')
        return redirect('conversation', conversation_id=conversation_id)

    if content or file:
        # Determine message type
        message_type = 'text'
        file_name = None
        file_size = None

        if file:
            file_name = file.name
            file_size = file.size

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

        # Update conversation timestamp
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
                # Create notification message
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

        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
            if message.message_type not in ['text', 'emoji'] and message.file:
                response_data['file_url'] = message.file.url
                response_data['file_name'] = message.file_name
                response_data['file_size'] = message.get_file_size_display()
                response_data['is_image'] = message.is_image_file()
                response_data['is_video'] = message.is_video_file()
                response_data['is_audio'] = message.is_audio_file()

            return JsonResponse(response_data)
        else:
            # Regular form submission
            return redirect('conversation', conversation_id=conversation_id)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Message content or file is required'})
        else:
            messages.error(request, 'Message content or file is required')
            return redirect('conversation', conversation_id=conversation_id)


@login_required
@csrf_exempt
@require_POST
def send_message_ajax(request, conversation_id):
    """Send message via AJAX"""
    return send_message(request, conversation_id)


@login_required
def group_settings(request, conversation_id):
    """Group settings and management"""
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants', 'admins'),
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
                if group_photo.content_type.startswith('image/'):
                    if group_photo.size <= 5 * 1024 * 1024:  # 5MB
                        conversation.group_photo = group_photo
                    else:
                        messages.error(request, 'Image too large. Max 5MB.')
                else:
                    messages.error(request, 'Please select a valid image file.')

            conversation.save()
            messages.success(request, 'Group updated successfully.')
            return redirect('group_settings', conversation_id=conversation_id)

        elif 'remove_group_photo' in request.POST:
            if conversation.group_photo:
                conversation.group_photo.delete(save=True)
                messages.success(request, 'Group photo removed successfully.')
            else:
                messages.warning(request, 'No group photo to remove.')

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
@require_POST
def leave_group(request, conversation_id):
    """Leave a group"""
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

    return redirect('chat_home')


@login_required
@csrf_exempt
@require_POST
def invite_to_group(request, conversation_id):
    """Invite users to group via AJAX"""
    conversation = get_object_or_404(Conversation, id=conversation_id, is_group=True)
    user_ids = request.POST.getlist('user_ids[]')

    invited_users = []
    for user_id in user_ids:
        try:
            user = CustomUser.objects.get(id=user_id)
            if user not in conversation.participants.all():
                conversation.participants.add(user)
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


@login_required
@csrf_exempt
@require_POST
def typing_indicator(request, conversation_id):
    """Handle typing indicators"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    try:
        data = json.loads(request.body)
        is_typing = data.get('is_typing', False)

        if is_typing:
            conversation.typing_users.add(request.user)
        else:
            conversation.typing_users.remove(request.user)

        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})


@login_required
@require_GET
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
@require_GET
def get_new_messages(request, conversation_id):
    """Get new messages for real-time updates"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    # Get messages that are not from current user and not read
    new_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).select_related('sender')

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
        if message.message_type not in ['text', 'emoji'] and message.file:
            message_data['file_url'] = message.file.url
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


@login_required
@require_GET
def get_notifications(request):
    """Get user notifications for dropdown"""
    notifications = request.user.account_notifications.filter(
        is_read=False,
        is_archived=False
    ).order_by('-created_at')[:10]

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


@login_required
@csrf_exempt
@require_GET
def get_messages_ajax(request, conversation_id):
    """Get messages via AJAX"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    messages_list = conversation.messages.select_related('sender').all().order_by('timestamp')

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
        if message.message_type not in ['text', 'emoji'] and message.file:
            message_data['file_url'] = message.file.url
            message_data['file_name'] = message.file_name
            message_data['file_size'] = message.get_file_size_display()
            message_data['is_image'] = message.is_image_file()
            message_data['is_video'] = message.is_video_file()
            message_data['is_audio'] = message.is_audio_file()

        messages_data.append(message_data)

    return JsonResponse({'messages': messages_data})


@login_required
@csrf_exempt
@require_POST
def edit_message(request, message_id):
    """Edit a message"""
    try:
        message = Message.objects.select_related('sender', 'conversation').get(id=message_id, sender=request.user)

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
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})


@login_required
@csrf_exempt
@require_POST
def unsend_message(request, message_id):
    """Unsend (delete) a message"""
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


@login_required
@csrf_exempt
@require_POST
def react_to_message(request, message_id):
    """Add reaction to a message"""
    try:
        message = Message.objects.get(id=message_id)

        if message.is_unsent:
            return JsonResponse({'success': False, 'error': 'Cannot react to unsent message'})

        data = json.loads(request.body)
        reaction = data.get('reaction', '')

        # Validate reaction
        if reaction and len(reaction) <= 10:
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
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})


@login_required
def discover_users(request):
    """Discover and search users"""
    query = request.GET.get('q', '').strip()

    # Get users blocked by current user
    blocked_users_ids = BlockedUser.objects.filter(user=request.user).values_list('blocked_user_id', flat=True)

    # Get users who blocked current user
    blocked_by_ids = BlockedUser.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)

    # Combine both sets of blocked users
    all_blocked_ids = set(blocked_users_ids) | set(blocked_by_ids)

    # Get users based on search query or show all
    if query:
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
        users = CustomUser.objects.exclude(
            Q(id=request.user.id) | Q(id__in=all_blocked_ids)
        ).order_by('-date_joined')
        is_search = False
        total_users = users.count()

    # Add friend status
    users_with_status = []
    for user in users:
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

        user_info = {
            'user': user,
            'friend_status': friend_status,
            'received_request_id': received_request_id,
            'is_online': hasattr(user, 'status') and user.status.online
        }
        users_with_status.append(user_info)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users_with_status, 20)

    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    context = {
        'users_page': users_page,
        'total_users': total_users,
        'query': query,
        'is_search': is_search,
    }
    return render(request, 'chat/discover_users.html', context)


@login_required
@require_POST
def block_user(request, user_id):
    """Block a user"""
    try:
        user_to_block = CustomUser.objects.get(id=user_id)

        # Can't block yourself
        if user_to_block == request.user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'You cannot block yourself.'})
            messages.error(request, 'You cannot block yourself.')
            return redirect('discover_users')

        # Check if already blocked
        if BlockedUser.objects.filter(user=request.user, blocked_user=user_to_block).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': f'You have already blocked {user_to_block.username}.'})
            messages.warning(request, f'You have already blocked {user_to_block.username}.')
            return redirect('discover_users')

        # Create block
        BlockedUser.objects.create(
            user=request.user,
            blocked_user=user_to_block,
            reason=request.POST.get('reason', '')
        )

        # Cancel any pending friend requests
        FriendRequest.objects.filter(
            from_user=request.user,
            to_user=user_to_block,
            status='pending'
        ).update(status='cancelled')

        FriendRequest.objects.filter(
            from_user=user_to_block,
            to_user=request.user,
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

    except CustomUser.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'User not found.'})
        messages.error(request, 'User not found.')

    return redirect('discover_users')


@login_required
@require_POST
def unblock_user(request, user_id):
    """Unblock a user"""
    try:
        user_to_unblock = CustomUser.objects.get(id=user_id)

        # Remove block
        blocked_entry = BlockedUser.objects.filter(
            user=request.user,
            blocked_user=user_to_unblock
        )

        if blocked_entry.exists():
            blocked_entry.delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'You have unblocked {user_to_unblock.username}.'
                })

            messages.success(request, f'You have unblocked {user_to_unblock.username}.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User is not blocked.'})
            messages.error(request, 'User is not blocked.')

    except CustomUser.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'User not found.'})
        messages.error(request, 'User not found.')

    return redirect('blocked_users')


@login_required
def blocked_users(request):
    """Show list of blocked users"""
    blocked_users = BlockedUser.objects.filter(
        user=request.user
    ).select_related('blocked_user').order_by('-blocked_at')

    context = {
        'blocked_users': blocked_users,
    }
    return render(request, 'chat/blocked_users.html', context)


@login_required
def quick_chat(request, user_id):
    """Start a quick chat with any user"""
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
        conversation.save()

        messages.success(request, f'Started chat with {target_user.username}')
        return redirect('conversation', conversation_id=conversation.id)

    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('discover_users')


@login_required
@csrf_exempt
@require_POST
def update_online_status(request):
    """Update user's online status"""
    try:
        data = json.loads(request.body)
        is_online = data.get('online', True)

        # Update user's online status
        request.user.is_online = is_online
        request.user.last_seen = timezone.now()
        request.user.save()

        # Update UserStatus if it exists
        try:
            status = request.user.status
            status.online = is_online
            status.last_seen = timezone.now()
            status.save()
        except UserStatus.DoesNotExist:
            UserStatus.objects.create(
                user=request.user,
                online=is_online,
                last_seen=timezone.now()
            )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating online status: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_GET
def search_emojis(request):
    """Search emojis via AJAX"""
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


@login_required
@require_GET
def get_emoji_categories(request):
    """Get emoji categories via AJAX"""
    categories = EmojiManager.get_emoji_categories()
    return JsonResponse({
        'success': True,
        'categories': categories
    })


@login_required
@csrf_exempt
@require_POST
def device_info(request):
    """Store device information for mobile users"""
    try:
        data = json.loads(request.body)
        device_type = data.get('device_type', 'unknown')
        screen_width = data.get('screen_width', 0)
        screen_height = data.get('screen_height', 0)

        # Store in session
        request.session['device_type'] = device_type
        request.session['screen_width'] = screen_width
        request.session['screen_height'] = screen_height
        request.session['is_mobile'] = device_type in ['phone', 'tablet']

        return JsonResponse({
            'success': True,
            'message': 'Device info stored'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if request.method == 'POST':
        request.user.account_notifications.filter(is_read=False).update(is_read=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'All notifications marked as read'})

        messages.success(request, 'All notifications marked as read')
        return redirect('chat_home')

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    if request.method == 'POST':
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        # For groups, only admins can delete
        if conversation.is_group and request.user not in conversation.admins.all():
            messages.error(request, 'Only group admins can delete the conversation.')
            return redirect('conversation', conversation_id=conversation_id)

        conversation_name = conversation.group_name if conversation.is_group else "Conversation"
        conversation.delete()

        messages.success(request, f'{conversation_name} deleted successfully.')
        return redirect('chat_home')

    return JsonResponse({'success': False, 'error': 'Invalid request method'})