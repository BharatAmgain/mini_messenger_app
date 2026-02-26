# chat/views.py - COMPLETE WITH VOICE MESSAGE AND DOWNLOAD SUPPORT
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
import os
from django.conf import settings
import emoji
import uuid
import base64
import mimetypes
from django.core.files.base import ContentFile
import urllib.parse

# Local chat models imports
from .models import Conversation, Message, UserStatus, ChatNotification, GroupInvitation, ChatMedia

# Local accounts models imports
from accounts.models import CustomUser, Notification, Friendship, FriendRequest, BlockedUser

# Local utils imports
from .utils import EmojiManager


@login_required(login_url='/accounts/login/')
def chat_home(request):
    """Chat home page with conversations and search"""
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')

    conversation_data = []
    for conversation in conversations:
        if conversation.is_group:
            display_name = conversation.group_name
            display_photo = conversation.group_photo.url if conversation.group_photo else None
            is_online = False
        else:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            display_name = other_user.username if other_user else "Unknown User"
            display_photo = other_user.profile_picture.url if other_user and other_user.profile_picture else None
            is_online = other_user.status.online if other_user and hasattr(other_user, 'status') else False

        unread_count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).count()

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

    unread_notifications_count = request.user.account_notifications.filter(is_read=False).count()

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


@login_required(login_url='/accounts/login/')
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
            messages.error(request, 'User not found. Please check the email or phone number.')
            return redirect('start_chat')

        if user == request.user:
            messages.error(request, 'You cannot start a chat with yourself.')
            return redirect('start_chat')

        if not Friendship.are_friends(request.user, user):
            messages.error(request, 'You need to be friends to chat with this user.')
            return redirect('start_chat')

        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=user
        ).filter(
            is_group=False
        ).first()

        if existing_conversation:
            return redirect('conversation', conversation_id=existing_conversation.id)

        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, user)

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"Started chat with {user.username}",
            is_read=True
        )

        messages.success(request, f'Started chat with {user.username}')
        return redirect('conversation', conversation_id=conversation.id)

    return render(request, 'chat/start_chat.html')


@login_required(login_url='/accounts/login/')
def start_chat_with_user(request, user_id):
    """Start a chat with a specific user by ID"""
    try:
        try:
            if isinstance(user_id, str) and '-' in user_id:
                target_user = get_object_or_404(CustomUser, id=user_id)
            else:
                target_user = CustomUser.objects.get(id=int(user_id))
        except (ValueError, TypeError):
            target_user = get_object_or_404(CustomUser, id=user_id)

        if target_user == request.user:
            messages.error(request, 'You cannot start a chat with yourself.')
            return redirect('chat_home')

        if not Friendship.are_friends(request.user, target_user):
            messages.error(request, 'You need to be friends to chat with this user.')
            return redirect('chat_home')

        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=target_user
        ).filter(
            is_group=False
        ).first()

        if existing_conversation:
            return redirect('conversation', conversation_id=existing_conversation.id)

        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, target_user)

        messages.success(request, f'Started chat with {target_user.username}')
        return redirect('conversation', conversation_id=conversation.id)

    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('chat_home')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('chat_home')


@login_required(login_url='/accounts/login/')
def create_group(request):
    """Create a new group chat"""
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip()
        group_description = request.POST.get('group_description', '').strip()
        participant_ids = request.POST.getlist('participants')

        if not group_name:
            messages.error(request, 'Group name is required.')
            return redirect('create_group')

        try:
            from django.db import transaction

            with transaction.atomic():
                conversation = Conversation.objects.create(
                    is_group=True,
                    group_name=group_name,
                    group_description=group_description,
                    created_by=request.user
                )

                conversation.participants.add(request.user)
                conversation.admins.add(request.user)

                added_users = []
                for user_id in participant_ids:
                    try:
                        user = CustomUser.objects.get(id=user_id)
                        if user != request.user:
                            conversation.participants.add(user)
                            added_users.append(user)
                            Notification.objects.create(
                                user=user,
                                notification_type='group_invite',
                                title=f"Added to group: {group_name}",
                                message=f"{request.user.username} added you to the group '{group_name}'",
                                related_url=f"/chat/{conversation.id}/"
                            )
                    except CustomUser.DoesNotExist:
                        continue

                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=f"Welcome to {group_name}! This group was created by {request.user.username}.",
                    is_read=True
                )

            messages.success(request, f'Group "{group_name}" created successfully with {len(added_users)} members!')
            return redirect('conversation', conversation_id=conversation.id)

        except Exception as e:
            messages.error(request, f'Error creating group: {str(e)}')
            return redirect('create_group')

    users = CustomUser.objects.exclude(id=request.user.id).order_by('username')
    return render(request, 'chat/create_group.html', {'users': users})


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
def conversation(request, conversation_id):
    """View conversation and messages"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)

        if request.user not in conversation.participants.all():
            messages.error(request, 'You are not a participant in this conversation.')
            return redirect('chat_home')

    except Conversation.DoesNotExist:
        messages.error(request, 'Conversation not found. Please start a new chat from the chat home page.')
        return redirect('chat_home')

    if not conversation.is_group:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            is_blocked = BlockedUser.objects.filter(
                Q(blocker=request.user, blocked=other_user) |
                Q(blocker=other_user, blocked=request.user)
            ).exists()

            if is_blocked:
                messages.error(request, 'This conversation is not available due to blocking.')
                return redirect('chat_home')

            if not Friendship.are_friends(request.user, other_user):
                messages.error(request, 'You need to be friends to chat with this user.')
                return redirect('chat_home')

    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user)

    for message in unread_messages:
        message.is_read = True
        message.save()

    request.user.account_notifications.filter(
        notification_type='message',
        related_url=f"/chat/{conversation.id}/"
    ).update(is_read=True)

    messages_list = conversation.messages.all().order_by('timestamp')

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


@login_required(login_url='/accounts/login/')
def group_settings(request, conversation_id):
    """Group settings and management"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        is_group=True
    )

    if not conversation.participants.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this group.')
        return redirect('chat_home')

    if request.method == 'POST':
        from django.db import transaction

        try:
            with transaction.atomic():
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
                                title=f"Added to group: {conversation.group_name}",
                                message=f"{request.user.username} added you to the group",
                                related_url=f"/chat/{conversation.id}/"
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

                            Message.objects.create(
                                conversation=conversation,
                                sender=request.user,
                                content=f"{user.username} was removed from the group by {request.user.username}",
                                is_read=True
                            )

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

                    if 'group_photo' in request.FILES and request.FILES['group_photo']:
                        group_photo = request.FILES['group_photo']

                        if group_photo.content_type.startswith('image/'):
                            if group_photo.size <= 5 * 1024 * 1024:
                                conversation.group_photo = group_photo
                            else:
                                messages.error(request, 'Image too large. Max 5MB.')
                        else:
                            messages.error(request, 'Please select a valid image file.')

                    conversation.save()
                    messages.success(request, 'Group updated successfully.')

                elif 'remove_group_photo' in request.POST:
                    if conversation.group_photo:
                        conversation.group_photo.delete(save=True)
                        messages.success(request, 'Group photo removed successfully.')
                    else:
                        messages.warning(request, 'No group photo to remove.')

                elif 'leave_group' in request.POST:
                    conversation.participants.remove(request.user)

                    if request.user in conversation.admins.all():
                        conversation.admins.remove(request.user)

                    Message.objects.create(
                        conversation=conversation,
                        sender=request.user,
                        content=f"{request.user.username} left the group",
                        is_read=True
                    )

                    messages.success(request, f'You have left the group "{conversation.group_name}".')
                    return redirect('chat_home')

                elif 'delete_group' in request.POST:
                    if request.user in conversation.admins.all():
                        group_name = conversation.group_name
                        conversation.delete()
                        messages.success(request, f'Group "{group_name}" has been deleted.')
                        return redirect('chat_home')
                    else:
                        messages.error(request, 'Only group admins can delete the group.')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('group_settings', conversation_id=conversation_id)

    all_users = CustomUser.objects.exclude(
        Q(id=request.user.id) | Q(conversations=conversation)
    ).order_by('username')

    context = {
        'conversation': conversation,
        'group_members': conversation.participants.all().order_by('username'),
        'group_admins': conversation.admins.all(),
        'all_users': all_users,
    }
    return render(request, 'chat/group_settings.html', context)


@login_required(login_url='/accounts/login/')
def leave_group(request, conversation_id):
    """Leave a group"""
    if request.method == 'POST':
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user,
            is_group=True
        )

        conversation.participants.remove(request.user)

        if request.user in conversation.admins.all():
            conversation.admins.remove(request.user)

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


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
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

        last_timestamp = request.GET.get('last_timestamp')

        if last_timestamp:
            try:
                from django.utils.dateparse import parse_datetime
                last_time = parse_datetime(last_timestamp)
                new_messages = Message.objects.filter(
                    conversation=conversation,
                    timestamp__gt=last_time
                ).order_by('timestamp')
            except:
                new_messages = Message.objects.filter(
                    conversation=conversation,
                    timestamp__gt=timezone.now() - timezone.timedelta(seconds=30)
                ).order_by('timestamp')
        else:
            new_messages = Message.objects.filter(
                conversation=conversation,
                timestamp__gt=timezone.now() - timezone.timedelta(seconds=30)
            ).order_by('timestamp')

        messages_data = []
        for message in new_messages:
            message_data = {
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'full_timestamp': message.timestamp.isoformat(),
                'is_own': message.sender.id == request.user.id,
                'is_read': message.is_read,
                'message_type': message.message_type,
                'is_edited': message.is_edited,
                'is_unsent': message.is_unsent,
                'reactions': message.get_reaction_summary() if hasattr(message, 'get_reaction_summary') else {},
                'user_reaction': message.get_user_reaction(request.user) if hasattr(message, 'get_user_reaction') else None,
                'file_url': message.file.url if message.file else None,
                'file_name': message.file_name,
                'file_size': message.get_file_size_display() if hasattr(message, 'get_file_size_display') else None,
                'is_image': message.is_image_file() if hasattr(message, 'is_image_file') else False,
                'is_video': message.is_video_file() if hasattr(message, 'is_video_file') else False,
                'is_audio': message.is_audio_file() if hasattr(message, 'is_audio_file') else False,
                'is_voice': message.message_type == 'voice',
                'voice_duration': message.voice_duration,
                'voice_waveform': message.voice_waveform,
            }
            messages_data.append(message_data)

            if message.sender != request.user:
                message.is_read = True
                message.save()

        return JsonResponse({
            'success': True,
            'new_messages': messages_data,
            'has_new_messages': len(messages_data) > 0,
            'last_timestamp': timezone.now().isoformat()
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
def get_notifications(request):
    """Get user notifications for dropdown"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
@csrf_exempt
def send_message_ajax(request, conversation_id):
    """Send message via AJAX with download support"""
    print(f"\n=== SEND MESSAGE DEBUG ===")
    print(f"Conversation ID: {conversation_id}")
    print(f"User: {request.user.username}")
    print(f"Method: {request.method}")
    print(f"X-Requested-With: {request.headers.get('x-requested-with')}")

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request type'}, status=400)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Conversation not found'}, status=404)

        if request.user not in conversation.participants.all():
            return JsonResponse({'success': False, 'error': 'You are not a participant in this conversation'}, status=403)

        if not conversation.is_group:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            if other_user:
                is_blocked = BlockedUser.objects.filter(
                    Q(blocker=request.user, blocked=other_user) |
                    Q(blocker=other_user, blocked=request.user)
                ).exists()

                if is_blocked:
                    return JsonResponse({'success': False, 'error': 'Cannot send message. User is blocked.'})

        content = request.POST.get('content', '').strip()
        file = request.FILES.get('file')

        is_voice = request.POST.get('is_voice') == 'true'
        voice_duration = request.POST.get('voice_duration')
        voice_waveform = request.POST.get('voice_waveform')
        voice_data = request.POST.get('voice_data')

        if not content and not file and not voice_data:
            return JsonResponse({'success': False, 'error': 'Message content or file is required'})

        if file and file.size > 50 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File too large. Maximum size is 50MB.'})

        message_type = 'text'
        file_name = None
        file_size = None
        voice_duration_int = None
        voice_waveform_data = None

        if is_voice or voice_data:
            message_type = 'voice'
            if voice_duration:
                voice_duration_int = int(voice_duration)
            if voice_waveform:
                try:
                    voice_waveform_data = json.loads(voice_waveform)
                except:
                    voice_waveform_data = None

            if voice_data and not file:
                try:
                    format, audio_data = voice_data.split(';base64,')
                    audio_bytes = base64.b64decode(audio_data)
                    file = ContentFile(audio_bytes, name=f"voice_{uuid.uuid4()}.webm")
                    file_name = file.name
                    file_size = file.size
                except Exception as e:
                    print(f"Error processing voice data: {e}")

        elif file:
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
        elif content:
            try:
                import emoji
                emoji_count = sum(1 for char in content if emoji.is_emoji(char))
                total_chars = len(content.strip())

                if (emoji_count > 0 and total_chars <= 3) or (total_chars > 0 and emoji_count / total_chars > 0.7):
                    message_type = 'emoji'
            except:
                pass

        try:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
                message_type=message_type,
                file=file if file else None,
                file_name=file_name,
                file_size=file_size,
                voice_duration=voice_duration_int,
                voice_waveform=voice_waveform_data
            )
            print(f"Message created with ID: {message.id}, Type: {message_type}")
        except Exception as e:
            print(f"Error creating message: {e}")
            return JsonResponse({'success': False, 'error': f'Failed to create message: {str(e)}'})

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

        response_data = {
            'success': True,
            'id': str(message.id),
            'message_id': str(message.id),
            'content': message.content,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'full_timestamp': message.timestamp.isoformat(),
            'sender': message.sender.username,
            'sender_id': str(message.sender.id),
            'is_own': True,
            'is_edited': message.is_edited,
            'is_unsent': message.is_unsent,
            'reactions': {},
            'user_reaction': None,
            'message_type': message.message_type,
            'file_url': message.file.url if message.file else None,
            'file_name': message.file_name,
            'file_size': message.get_file_size_display() if message.file_size else None,
            'is_image': message.is_image_file() if message.file else False,
            'is_video': message.is_video_file() if message.file else False,
            'is_audio': message.is_audio_file() if message.file else False,
            'is_voice': message.message_type == 'voice',
            'voice_duration': message.voice_duration,
            'voice_waveform': message.voice_waveform,
        }

        return JsonResponse(response_data)

    except Exception as e:
        print(f"UNHANDLED EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)


@login_required(login_url='/accounts/login/')
def download_file(request, message_id):
    """Download file from message - FIXED for mobile devices"""
    try:
        message = get_object_or_404(Message, id=message_id)

        if request.user not in message.conversation.participants.all():
            return HttpResponse('Unauthorized', status=401)

        if not message.file:
            return HttpResponse('File not found', status=404)

        file_path = message.file.path
        if not os.path.exists(file_path):
            return HttpResponse('File not found on server', status=404)

        file_name = message.file_name or os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{urllib.parse.quote(file_name)}"'
            response['Content-Length'] = os.path.getsize(file_path)
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response

    except Exception as e:
        print(f"Download error: {e}")
        return HttpResponse(f'Error downloading file: {str(e)}', status=500)


@login_required(login_url='/accounts/login/')
def search_emojis(request):
    """Search emojis via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()

        if query:
            results = EmojiManager.search_emojis(query)
        else:
            results = EmojiManager.get_all_emojis()[:30]

        return JsonResponse({
            'success': True,
            'emojis': results,
            'query': query
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
def get_emoji_categories(request):
    """Get emoji categories via AJAX"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        categories = EmojiManager.get_emoji_categories()
        return JsonResponse({
            'success': True,
            'categories': categories
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
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
                'full_timestamp': message.timestamp.isoformat(),
                'is_own': message.sender.id == request.user.id,
                'is_read': message.is_read,
                'is_edited': message.is_edited,
                'is_unsent': message.is_unsent,
                'reactions': message.get_reaction_summary() if hasattr(message, 'get_reaction_summary') else {},
                'user_reaction': message.get_user_reaction(request.user) if hasattr(message, 'get_user_reaction') else None,
                'message_type': message.message_type,
                'file_url': message.file.url if message.file else None,
                'file_name': message.file_name,
                'file_size': message.get_file_size_display() if hasattr(message, 'get_file_size_display') else None,
                'is_image': message.is_image_file() if hasattr(message, 'is_image_file') else False,
                'is_video': message.is_video_file() if hasattr(message, 'is_video_file') else False,
                'is_audio': message.is_audio_file() if hasattr(message, 'is_audio_file') else False,
                'is_voice': message.message_type == 'voice',
                'voice_duration': message.voice_duration,
                'voice_waveform': message.voice_waveform,
            }

            messages_data.append(message_data)

        return JsonResponse({'messages': messages_data})

    return JsonResponse({'error': 'Invalid request'})


@csrf_exempt
@login_required
def update_online_status(request):
    """Update user's online status"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        user = request.user
        user.last_seen = timezone.now()

        if request.body:
            try:
                data = json.loads(request.body)
                if 'online' in data:
                    user.is_online = bool(data.get('online', False))
            except json.JSONDecodeError:
                pass

        if hasattr(user, 'is_verified'):
            if callable(user.is_verified):
                user.is_verified = user.is_verified()
            else:
                user.is_verified = bool(user.is_verified)

        if hasattr(user, 'is_online'):
            user.save(update_fields=['last_seen', 'is_online'])
        else:
            user.save(update_fields=['last_seen'])

        return JsonResponse({
            'success': True,
            'last_seen': user.last_seen.isoformat(),
            'is_online': getattr(user, 'is_online', False)
        })

    except ValidationError as e:
        error_dict = {}
        if hasattr(e, 'error_dict'):
            error_dict = e.error_dict
        elif hasattr(e, 'messages'):
            error_dict = {'error': e.messages}
        else:
            error_dict = {'error': str(e)}

        print(f"Validation Error in update_online_status: {error_dict}")
        return JsonResponse({'success': False, 'error': str(error_dict)}, status=400)

    except Exception as e:
        print(f"Error in update_online_status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
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


@login_required(login_url='/accounts/login/')
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

            if reaction and len(reaction) <= 10:
                if hasattr(message, 'add_reaction'):
                    success = message.add_reaction(request.user, reaction)
                else:
                    success = True

                if success:
                    return JsonResponse({
                        'success': True,
                        'message_id': str(message.id),
                        'reactions': message.get_reaction_summary() if hasattr(message, 'get_reaction_summary') else {},
                        'user_reaction': reaction
                    })

            return JsonResponse({'success': False, 'error': 'Invalid reaction'})

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
def discover_users(request):
    """Merged page for discovering all users and searching users"""
    query = request.GET.get('q', '').strip()

    blocked_users_ids = BlockedUser.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
    blocked_by_ids = BlockedUser.objects.filter(blocked=request.user).values_list('blocker_id', flat=True)
    all_blocked_ids = set(blocked_users_ids) | set(blocked_by_ids)

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

    online_users = []
    users_with_status = []

    for user in users:
        if hasattr(user, 'status') and user.status.online:
            online_users.append(user.id)

        friend_status = user.get_friend_status(request.user) if hasattr(user, 'get_friend_status') else 'not_friends'

        received_request_id = None
        if friend_status == 'request_received':
            received_request = FriendRequest.objects.filter(
                from_user=user,
                to_user=request.user,
                status='pending'
            ).first()
            if received_request:
                received_request_id = received_request.id

        sent_request_id = None
        if friend_status == 'request_sent':
            sent_request = FriendRequest.objects.filter(
                from_user=request.user,
                to_user=user,
                status='pending'
            ).first()
            if sent_request:
                sent_request_id = sent_request.id

        user_info = {
            'user': user,
            'friend_status': friend_status,
            'received_request_id': received_request_id,
            'sent_request_id': sent_request_id,
            'is_online': user.id in online_users
        }
        users_with_status.append(user_info)

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
        'online_users': online_users,
        'total_users': total_users,
        'query': query,
        'is_search': is_search,
    }
    return render(request, 'chat/discover_users.html', context)


@login_required(login_url='/accounts/login/')
def block_user(request, user_id):
    """Block a user"""
    if request.method == 'POST':
        try:
            try:
                user_to_block = CustomUser.objects.get(id=user_id)
            except (ValueError, ValidationError):
                try:
                    user_to_block = CustomUser.objects.get(id=int(user_id))
                except (ValueError, TypeError):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Invalid user ID format'})
                    messages.error(request, 'Invalid user ID format')
                    return redirect('discover_users')

            if user_to_block == request.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'You cannot block yourself.'})
                messages.error(request, 'You cannot block yourself.')
                return redirect('discover_users')

            if BlockedUser.objects.filter(blocker=request.user, blocked=user_to_block).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f'You have already blocked {user_to_block.username}.'})
                messages.warning(request, f'You have already blocked {user_to_block.username}.')
                return redirect('discover_users')

            block = BlockedUser.objects.create(
                blocker=request.user,
                blocked=user_to_block,
                reason=request.POST.get('reason', '')
            )

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

            Friendship.objects.filter(
                (Q(user1=request.user) & Q(user2=user_to_block)) |
                (Q(user1=user_to_block) & Q(user2=request.user))
            ).delete()

            try:
                Notification.objects.create(
                    user=user_to_block,
                    notification_type='system',
                    title="User Blocked You",
                    message=f"{request.user.username} has blocked you",
                    related_url="/accounts/settings/"
                )

                Notification.objects.create(
                    user=request.user,
                    notification_type='system',
                    title="User Blocked",
                    message=f"You have blocked {user_to_block.username}",
                    related_url="/chat/blocked-users/"
                )
            except:
                pass

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'You have blocked {user_to_block.username}.',
                    'block_id': block.id
                })

            messages.success(request, f'You have blocked {user_to_block.username}.')
            return redirect('discover_users')

        except CustomUser.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'User not found.'})
            messages.error(request, 'User not found.')
            return redirect('discover_users')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    return redirect('discover_users')


@login_required(login_url='/accounts/login/')
def unblock_user(request, user_id):
    """Unblock a user"""
    if request.method == 'POST':
        try:
            try:
                user_to_unblock = CustomUser.objects.get(id=user_id)
            except (ValueError, ValidationError):
                try:
                    user_to_unblock = CustomUser.objects.get(id=int(user_id))
                except (ValueError, TypeError):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Invalid user ID format'})
                    messages.error(request, 'Invalid user ID format')
                    return redirect('blocked_users')

            blocked_entry = BlockedUser.objects.filter(
                blocker=request.user,
                blocked=user_to_unblock
            )

            if blocked_entry.exists():
                blocked_entry.delete()

                try:
                    Notification.objects.create(
                        user=user_to_unblock,
                        notification_type='system',
                        title="User Unblocked You",
                        message=f"{request.user.username} has unblocked you",
                        related_url="/"
                    )

                    Notification.objects.create(
                        user=request.user,
                        notification_type='system',
                        title="User Unblocked",
                        message=f"You have unblocked {user_to_unblock.username}",
                        related_url="/"
                    )
                except:
                    pass

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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    return redirect('blocked_users')


@login_required(login_url='/accounts/login/')
def blocked_users(request):
    """Show list of blocked users"""
    blocked_users = BlockedUser.objects.filter(blocker=request.user).select_related('blocked')

    context = {
        'blocked_users': blocked_users,
    }
    return render(request, 'chat/blocked_users.html', context)


@login_required(login_url='/accounts/login/')
def quick_chat(request, user_id):
    """Start a quick chat with any user"""
    try:
        try:
            if isinstance(user_id, str) and '-' in user_id:
                target_user = get_object_or_404(CustomUser, id=user_id)
            else:
                target_user = CustomUser.objects.get(id=int(user_id))
        except (ValueError, TypeError):
            target_user = get_object_or_404(CustomUser, id=user_id)

        if target_user == request.user:
            messages.error(request, 'You cannot start a chat with yourself.')
            return redirect('discover_users')

        is_blocked = BlockedUser.objects.filter(
            Q(blocker=request.user, blocked=target_user) |
            Q(blocker=target_user, blocked=request.user)
        ).exists()

        if is_blocked:
            messages.error(request, 'You cannot start a chat with this user due to blocking.')
            return redirect('discover_users')

        if not Friendship.are_friends(request.user, target_user):
            messages.error(request, 'You need to be friends to chat with this user.')
            return redirect('discover_users')

        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=target_user
        ).filter(
            is_group=False
        ).first()

        if existing_conversation:
            print(f"Using existing conversation: {existing_conversation.id}")
            messages.info(request, f'Continuing chat with {target_user.username}')
            return redirect('conversation', conversation_id=existing_conversation.id)

        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, target_user)

        print(f"Created new conversation: {conversation.id}")

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"Started chat with {target_user.username}",
            is_read=True
        )

        messages.success(request, f'Started chat with {target_user.username}')
        return redirect('conversation', conversation_id=conversation.id)

    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('discover_users')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('discover_users')


@login_required(login_url='/accounts/login/')
def group_chat(request, conversation_id=None):
    """Group chat interface"""
    if conversation_id:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            is_group=True,
            participants=request.user
        )

        messages_list = conversation.messages.all().order_by('timestamp')

        context = {
            'conversation': conversation,
            'messages': messages_list,
            'is_group': True,
            'group_members': conversation.participants.all(),
            'group_admins': conversation.admins.all(),
        }
        return render(request, 'chat/group_chat.html', context)
    else:
        if request.method == 'POST':
            group_name = request.POST.get('group_name', '').strip()
            group_description = request.POST.get('group_description', '').strip()
            participant_ids = request.POST.getlist('participants')

            if not group_name:
                messages.error(request, 'Group name is required.')
                return redirect('create_group')

            conversation = Conversation.objects.create(
                is_group=True,
                group_name=group_name,
                group_description=group_description,
                created_by=request.user
            )

            conversation.participants.add(request.user)
            conversation.admins.add(request.user)

            for user_id in participant_ids:
                try:
                    user = CustomUser.objects.get(id=user_id)
                    if user != request.user:
                        conversation.participants.add(user)
                        try:
                            Notification.objects.create(
                                user=user,
                                notification_type='group_invite',
                                title="Group Invitation",
                                message=f"You were added to group '{group_name}' by {request.user.username}",
                                related_url=f"/chat/group/{conversation.id}/"
                            )
                        except:
                            pass
                except CustomUser.DoesNotExist:
                    continue

            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=f"Welcome to {group_name}! This group was created by {request.user.username}.",
                is_read=True
            )

            messages.success(request, f'Group "{group_name}" created successfully!')
            return redirect('group_chat', conversation_id=conversation.id)

        users = CustomUser.objects.exclude(id=request.user.id)
        return render(request, 'chat/create_group.html', {'users': users})


@login_required(login_url='/accounts/login/')
def video_chat(request, conversation_id):
    """Start a video chat in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    import hashlib
    import time
    room_seed = f"{conversation_id}_{request.user.id}_{time.time()}"
    room_hash = hashlib.md5(room_seed.encode()).hexdigest()[:12]

    context = {
        'conversation': conversation,
        'room_name': room_hash,
        'is_group': conversation.is_group,
    }

    return render(request, 'chat/video_chat.html', context)


@login_required(login_url='/accounts/login/')
def audio_chat(request, conversation_id):
    """Start an audio chat in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    import hashlib
    import time
    room_seed = f"{conversation_id}_{request.user.id}_{time.time()}_audio"
    room_hash = hashlib.md5(room_seed.encode()).hexdigest()[:12]

    context = {
        'conversation': conversation,
        'room_name': room_hash,
        'is_group': conversation.is_group,
    }

    return render(request, 'chat/audio_chat.html', context)


@login_required(login_url='/accounts/login/')
def message_search(request, conversation_id=None):
    """Search messages within a conversation or globally"""
    query = request.GET.get('q', '').strip()

    if not query:
        messages.error(request, 'Please enter a search query.')
        return redirect(request.META.get('HTTP_REFERER', 'chat_home'))

    if conversation_id:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        search_results = Message.objects.filter(
            conversation=conversation,
            content__icontains=query
        ).order_by('-timestamp')

        context = {
            'query': query,
            'search_results': search_results,
            'conversation': conversation,
            'search_scope': 'conversation',
        }
    else:
        user_conversations = Conversation.objects.filter(participants=request.user)

        search_results = Message.objects.filter(
            conversation__in=user_conversations,
            content__icontains=query
        ).order_by('-timestamp')

        context = {
            'query': query,
            'search_results': search_results,
            'search_scope': 'global',
        }

    return render(request, 'chat/message_search.html', context)


@login_required(login_url='/accounts/login/')
def pin_message(request, message_id):
    """Pin a message in conversation"""
    if request.method == 'POST':
        try:
            message = Message.objects.get(id=message_id)
            conversation = message.conversation

            if not conversation.participants.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Not authorized.'})

            message.is_pinned = not message.is_pinned
            message.save()

            return JsonResponse({
                'success': True,
                'is_pinned': message.is_pinned,
                'message': 'Message pinned successfully.' if message.is_pinned else 'Message unpinned.'
            })

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found.'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
def star_message(request, message_id):
    """Star (favorite) a message"""
    if request.method == 'POST':
        try:
            message = Message.objects.get(id=message_id)

            if request.user in message.starred_by.all():
                message.starred_by.remove(request.user)
                is_starred = False
                action = 'unstarred'
            else:
                message.starred_by.add(request.user)
                is_starred = True
                action = 'starred'

            return JsonResponse({
                'success': True,
                'is_starred': is_starred,
                'action': action,
                'star_count': message.starred_by.count()
            })

        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found.'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/accounts/login/')
def delete_conversation(request, conversation_id):
    """Delete a conversation (archive)"""
    if request.method == 'POST':
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )

            conversation.is_archived = True
            conversation.archived_at = timezone.now()
            conversation.archived_by = request.user
            conversation.save()

            conversation.participants.remove(request.user)

            messages.success(request, 'Conversation archived successfully.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Conversation archived successfully.'
                })

        except Conversation.DoesNotExist:
            messages.error(request, 'Conversation not found.')

    return redirect('chat_home')


@login_required(login_url='/accounts/login/')
def restore_conversation(request, conversation_id):
    """Restore an archived conversation"""
    if request.method == 'POST':
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                archived_by=request.user
            )

            conversation.is_archived = False
            conversation.archived_at = None
            conversation.archived_by = None
            conversation.save()

            conversation.participants.add(request.user)

            messages.success(request, 'Conversation restored successfully.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Conversation restored successfully.'
                })

        except Conversation.DoesNotExist:
            messages.error(request, 'Conversation not found.')

    return redirect('chat_home')


@login_required(login_url='/accounts/login/')
def archived_conversations(request):
    """View archived conversations"""
    archived_convos = Conversation.objects.filter(
        is_archived=True,
        archived_by=request.user
    ).order_by('-archived_at')

    context = {
        'archived_conversations': archived_convos,
    }
    return render(request, 'chat/archived_conversations.html', context)


@login_required(login_url='/accounts/login/')
def clear_conversation(request, conversation_id):
    """Clear all messages in a conversation"""
    if request.method == 'POST':
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )

            deleted_count, _ = conversation.messages.all().delete()

            messages.success(request, f'Cleared {deleted_count} messages from conversation.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Cleared {deleted_count} messages from conversation.',
                    'deleted_count': deleted_count
                })

        except Conversation.DoesNotExist:
            messages.error(request, 'Conversation not found.')

    return redirect('conversation', conversation_id=conversation_id)


@login_required(login_url='/accounts/login/')
def export_conversation(request, conversation_id):
    """Export conversation messages"""
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )

        messages = conversation.messages.all().order_by('timestamp')

        export_data = {
            'conversation_id': str(conversation.id),
            'conversation_type': 'group' if conversation.is_group else 'direct',
            'export_date': timezone.now().isoformat(),
            'exported_by': request.user.username,
            'messages': []
        }

        if conversation.is_group:
            export_data['group_name'] = conversation.group_name
            export_data['group_description'] = conversation.group_description
        else:
            other_user = conversation.participants.exclude(id=request.user.id).first()
            if other_user:
                export_data['other_user'] = other_user.username

        for msg in messages:
            message_data = {
                'id': str(msg.id),
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'message_type': msg.message_type,
                'is_edited': msg.is_edited,
                'is_unsent': msg.is_unsent,
                'voice_duration': msg.voice_duration,
            }

            if msg.edited_at:
                message_data['edited_at'] = msg.edited_at.isoformat()

            export_data['messages'].append(message_data)

        response = JsonResponse(export_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="conversation_{conversation_id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'

        return response

    except Conversation.DoesNotExist:
        messages.error(request, 'Conversation not found.')
        return redirect('chat_home')


@login_required(login_url='/accounts/login/')
def conversation_info(request, conversation_id):
    """Get conversation information"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    total_messages = conversation.messages.count()
    total_participants = conversation.participants.count()
    recent_messages = conversation.messages.all().order_by('-timestamp')[:10]
    participants = conversation.participants.all()

    context = {
        'conversation': conversation,
        'total_messages': total_messages,
        'total_participants': total_participants,
        'recent_messages': recent_messages,
        'participants': participants,
    }

    return render(request, 'chat/conversation_info.html', context)


@login_required(login_url='/accounts/login/')
def typing_status_ws(request, conversation_id):
    """WebSocket endpoint for typing status (simplified for HTTP fallback)"""
    return JsonResponse({
        'success': True,
        'message': 'WebSocket endpoint would be here in production',
        'conversation_id': conversation_id
    })


@login_required(login_url='/accounts/login/')
def message_stats(request):
    """Get message statistics for user"""
    total_sent = Message.objects.filter(sender=request.user).count()

    user_conversations = Conversation.objects.filter(participants=request.user)
    total_received = Message.objects.filter(
        conversation__in=user_conversations
    ).exclude(sender=request.user).count()

    from django.db.models import Count
    active_conversations = Message.objects.filter(
        conversation__in=user_conversations
    ).values(
        'conversation__id',
        'conversation__is_group'
    ).annotate(
        message_count=Count('id')
    ).order_by('-message_count')[:5]

    active_convos_data = []
    for conv in active_conversations:
        conv_obj = Conversation.objects.get(id=conv['conversation__id'])
        if conv_obj.is_group:
            name = conv_obj.group_name
            is_group = True
        else:
            other_user = conv_obj.participants.exclude(id=request.user.id).first()
            name = other_user.username if other_user else "Unknown"
            is_group = False

        active_convos_data.append({
            'id': conv['conversation__id'],
            'name': name,
            'is_group': is_group,
            'message_count': conv['message_count']
        })

    context = {
        'total_sent': total_sent,
        'total_received': total_received,
        'total_messages': total_sent + total_received,
        'active_conversations': active_convos_data,
    }

    return render(request, 'chat/message_stats.html', context)


@login_required(login_url='/accounts/login/')
def bulk_delete_messages(request, conversation_id):
    """Bulk delete messages in conversation"""
    if request.method == 'POST':
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )

            message_ids = request.POST.getlist('message_ids[]')

            deleted_count, _ = Message.objects.filter(
                id__in=message_ids,
                conversation=conversation,
                sender=request.user
            ).delete()

            messages.success(request, f'Deleted {deleted_count} messages.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Deleted {deleted_count} messages.',
                    'deleted_count': deleted_count
                })

        except Conversation.DoesNotExist:
            messages.error(request, 'Conversation not found.')

    return redirect('conversation', conversation_id=conversation_id)


@login_required
def debug_conversations(request):
    """Debug view to list all conversations"""
    conversations = Conversation.objects.filter(participants=request.user)
    html = "<h1>Your Conversations</h1>"
    html += "<ul>"
    for conv in conversations:
        other_users = conv.participants.exclude(id=request.user.id)
        other_names = ", ".join([u.username for u in other_users])
        html += f"<li><a href='/chat/{conv.id}/'>{conv.id} - with: {other_names}</a></li>"
    html += "</ul>"
    html += "<p><a href='/chat/'>Back to Chat Home</a></p>"
    return HttpResponse(html)


@login_required(login_url='/accounts/login/')
def video_chat(request, conversation_id):
    """Start a video chat in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # Determine if user is caller or callee
    is_caller = request.GET.get('caller', 'true') == 'true'

    # Get other participant for display
    if not conversation.is_group:
        other_user = conversation.participants.exclude(id=request.user.id).first()
    else:
        other_user = None

    context = {
        'conversation': conversation,
        'is_group': conversation.is_group,
        'is_caller': is_caller,
        'other_user': other_user,
        'target_user': other_user,
    }

    return render(request, 'chat/video_chat.html', context)


@login_required(login_url='/accounts/login/')
def audio_chat(request, conversation_id):
    """Start an audio chat in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # Determine if user is caller or callee
    is_caller = request.GET.get('caller', 'true') == 'true'

    # Get other participant for display
    if not conversation.is_group:
        other_user = conversation.participants.exclude(id=request.user.id).first()
    else:
        other_user = None

    context = {
        'conversation': conversation,
        'is_group': conversation.is_group,
        'is_caller': is_caller,
        'other_user': other_user,
        'target_user': other_user,
    }

    return render(request, 'chat/audio_chat.html', context)


@login_required
@csrf_exempt
def upload_voice_message(request, conversation_id=None):
    """Upload voice message - FIXED for proper audio handling"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Handle both URL patterns
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        else:
            conversation_id = request.POST.get('conversation_id')
            if not conversation_id:
                return JsonResponse({'success': False, 'error': 'Conversation ID required'})
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

        # Get voice data
        voice_data = request.POST.get('voice_data')
        voice_duration = request.POST.get('duration')
        voice_waveform = request.POST.get('waveform')

        if not voice_data:
            return JsonResponse({'success': False, 'error': 'No voice data provided'})

        # Parse duration
        try:
            duration = int(voice_duration) if voice_duration else 0
        except ValueError:
            duration = 0

        # Parse waveform
        try:
            waveform = json.loads(voice_waveform) if voice_waveform else None
        except:
            waveform = None

        # Decode base64 audio
        try:
            # Remove data URL prefix if present
            if ';base64,' in voice_data:
                format, audio_data = voice_data.split(';base64,')
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = base64.b64decode(voice_data)

            # Validate file size (max 5MB for voice)
            if len(audio_bytes) > 5 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'Voice message too large'})

            # Generate filename
            filename = f"voice_{uuid.uuid4()}.webm"

            # Save file
            file_path = default_storage.save(
                f"voice_messages/{filename}",
                ContentFile(audio_bytes)
            )

            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='voice',
                file=file_path,
                file_name=filename,
                file_size=len(audio_bytes),
                voice_duration=duration,
                voice_waveform=waveform
            )

            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])

            # Create notifications for other participants
            for participant in conversation.participants.exclude(id=request.user.id):
                if participant.message_notifications:
                    Notification.objects.create(
                        user=participant,
                        notification_type='message',
                        title=f"Voice message from {request.user.username}",
                        message=f"🎤 Voice message ({duration}s)",
                        related_url=f"/chat/{conversation.id}/"
                    )

            return JsonResponse({
                'success': True,
                'message': 'Voice message sent',
                'message_id': str(message.id),
                'file_url': message.file.url,
                'duration': duration,
                'waveform': waveform,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'full_timestamp': message.timestamp.isoformat()
            })

        except Exception as e:
            print(f"Error processing voice data: {e}")
            return JsonResponse({'success': False, 'error': f'Error processing audio: {str(e)}'})

    except Exception as e:
        print(f"Voice upload error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def play_voice_message(request, message_id):
    """Stream voice message for playback"""
    try:
        message = get_object_or_404(Message, id=message_id)

        # Check if user is participant
        if request.user not in message.conversation.participants.all():
            return HttpResponse('Unauthorized', status=401)

        if not message.file or message.message_type != 'voice':
            return HttpResponse('Voice message not found', status=404)

        file_path = message.file.path
        if not os.path.exists(file_path):
            return HttpResponse('File not found', status=404)

        # Stream the audio file
        response = FileResponse(open(file_path, 'rb'), content_type='audio/webm')
        response['Content-Disposition'] = f'inline; filename="{message.file_name}"'
        return response

    except Exception as e:
        print(f"Error playing voice message: {e}")
        return HttpResponse(f'Error: {str(e)}', status=500)