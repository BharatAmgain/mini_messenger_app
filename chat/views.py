# messenger_app/chat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Conversation, Message, UserStatus, ChatNotification, GroupInvitation
from accounts.models import CustomUser  # ✅ Correct import
import uuid
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


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

    # Get unread notifications count
    unread_notifications_count = ChatNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

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
    """Start a new chat with email or phone number"""
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip()

        if not email_or_phone:
            messages.error(request, 'Please enter an email or phone number.')
            return redirect('start_chat')  # Remove 'chat:' namespace

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
            return redirect('start_chat')  # Remove 'chat:' namespace

        if user == request.user:
            messages.error(request, 'You cannot start a chat with yourself.')
            return redirect('start_chat')  # Remove 'chat:' namespace

        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=user
        ).filter(
            is_group=False
        ).first()

        if existing_conversation:
            return redirect('conversation', conversation_id=existing_conversation.id)  # Remove 'chat:' namespace

        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, user)

        messages.success(request, f'Started chat with {user.username}')
        return redirect('conversation', conversation_id=conversation.id)  # Remove 'chat:' namespace

    return render(request, 'chat/start_chat.html')

# In messenger_app/chat/views.py - update the create_group view
@login_required
def create_group(request):
    """Create a new group chat"""
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip()
        group_description = request.POST.get('group_description', '').strip()
        participant_ids = request.POST.getlist('participants')

        if not group_name:
            messages.error(request, 'Group name is required.')
            return redirect('create_group')  # Remove 'chat:' namespace

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
                    # Create invitation notification
                    ChatNotification.objects.create(
                        user=user,
                        notification_type='group_invite',
                        conversation=conversation,
                        content=f"You were added to group '{group_name}' by {request.user.username}"
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
        return redirect('conversation', conversation_id=conversation.id)  # Remove 'chat:' namespace

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
    """View conversation and messages"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # Mark messages as read
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    # Mark notifications as read
    ChatNotification.objects.filter(
        user=request.user,
        conversation=conversation,
        notification_type='message',
        is_read=False
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

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )
                conversation.save()

                # Create notifications for other participants
                for participant in conversation.participants.exclude(id=request.user.id):
                    ChatNotification.objects.create(
                        user=participant,
                        notification_type='message',
                        conversation=conversation,
                        message=message,
                        content=f"New message from {request.user.username}"
                    )

                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': str(message.id),
                        'content': message.content,
                        'sender': message.sender.username,
                        'sender_id': message.sender.id,
                        'timestamp': message.timestamp.strftime('%H:%M'),
                        'is_own': True,
                        'is_read': message.is_read
                    }
                })

        return JsonResponse({'success': False, 'error': 'Invalid request'})

    return render(request, 'chat/conversation.html', context)


@login_required
def group_settings(request, conversation_id):
    """Group settings and management"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        is_group=True
    )

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
                    ChatNotification.objects.create(
                        user=user,
                        notification_type='group_invite',
                        conversation=conversation,
                        content=f"You were added to group '{conversation.group_name}' by {request.user.username}"
                    )
                    messages.success(request, f'{user.username} added to group.')
                else:
                    messages.warning(request, 'User is already in the group.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')

        elif 'remove_member' in request.POST:
            user_id = request.POST.get('user_id')
            try:
                user = CustomUser.objects.get(id=user_id)
                if user != request.user and user in conversation.participants.all():
                    conversation.participants.remove(user)
                    messages.success(request, f'{user.username} removed from group.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')

        elif 'update_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            group_description = request.POST.get('group_description', '').strip()

            if group_name:
                conversation.group_name = group_name
            if group_description:
                conversation.group_description = group_description
            conversation.save()
            messages.success(request, 'Group updated successfully.')

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
                    ChatNotification.objects.create(
                        user=user,
                        notification_type='group_invite',
                        conversation=conversation,
                        content=f"You were invited to group '{conversation.group_name}' by {request.user.username}"
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
            messages_data.append({
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'is_own': False,
                'is_read': message.is_read
            })

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
    """Get user notifications"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        notifications = ChatNotification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]

        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'content': notification.content,
                'conversation_id': str(notification.conversation.id) if notification.conversation else None,
                'created_at': notification.created_at.strftime('%H:%M'),
                'is_message': notification.notification_type == 'message'
            })

        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': notifications.count()
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        notification = get_object_or_404(ChatNotification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def send_message_ajax(request, conversation_id):
    """Send message via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        content = request.POST.get('content', '').strip()

        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()

            # Create notifications for other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                ChatNotification.objects.create(
                    user=participant,
                    notification_type='message',
                    conversation=conversation,
                    message=message,
                    content=f"New message from {request.user.username}"
                )

            return JsonResponse({
                'success': True,
                'message_id': str(message.id),
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'sender': message.sender.username,
                'is_own': True
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
            messages_data.append({
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'is_own': message.sender.id == request.user.id,
                'is_read': message.is_read
            })

        return JsonResponse({'messages': messages_data})

    return JsonResponse({'error': 'Invalid request'})


@login_required
def update_online_status(request):
    """Update user's online status"""
    if request.method == 'POST':
        online = request.POST.get('online', 'false') == 'true'

        # Update or create user status
        user_status, created = UserStatus.objects.get_or_create(user=request.user)
        user_status.online = online
        user_status.last_seen = timezone.now()
        user_status.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})


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


# Update the get_messages_ajax view to include new fields
@login_required
def get_messages_ajax(request, conversation_id):
    """Get messages via AJAX"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        messages_list = conversation.messages.all().order_by('timestamp')

        messages_data = []
        for message in messages_list:
            messages_data.append({
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
                'user_reaction': message.get_user_reaction(request.user)
            })

        return JsonResponse({'messages': messages_data})

    return JsonResponse({'error': 'Invalid request'})


# Update send_message_ajax to include new fields
@login_required
def send_message_ajax(request, conversation_id):
    """Send message via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        content = request.POST.get('content', '').strip()

        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()

            # Create notifications for other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                ChatNotification.objects.create(
                    user=participant,
                    notification_type='message',
                    conversation=conversation,
                    message=message,
                    content=f"New message from {request.user.username}"
                )

            return JsonResponse({
                'success': True,
                'message_id': str(message.id),
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'sender': message.sender.username,
                'is_own': True,
                'is_edited': False,
                'is_unsent': False,
                'reactions': {},
                'user_reaction': None
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'})