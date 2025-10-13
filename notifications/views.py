from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification, ContactRequest
from accounts.models import Contact
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return JsonResponse({'success': True})


@login_required
def get_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def send_contact_request(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    # Check if request already exists
    existing_request = ContactRequest.objects.filter(
        from_user=request.user,
        to_user=target_user
    ).first()

    if existing_request:
        return JsonResponse({'success': False, 'error': 'Request already sent'})

    # Check if already contacts
    if Contact.objects.filter(user=request.user, contact_user=target_user).exists():
        return JsonResponse({'success': False, 'error': 'Already contacts'})

    # Create contact request
    contact_request = ContactRequest.objects.create(
        from_user=request.user,
        to_user=target_user
    )

    # Send notification (you'll need to implement this)
    # from .utils import send_contact_request_notification
    # send_contact_request_notification(request.user, target_user)

    return JsonResponse({'success': True})


@login_required
def handle_contact_request(request, request_id, action):
    contact_request = get_object_or_404(ContactRequest, id=request_id, to_user=request.user)

    if action == 'accept':
        contact_request.status = 'accepted'
        contact_request.save()

        # Create contact relationship both ways
        Contact.objects.get_or_create(user=request.user, contact_user=contact_request.from_user)
        Contact.objects.get_or_create(user=contact_request.from_user, contact_user=request.user)

    elif action == 'reject':
        contact_request.status = 'rejected'
        contact_request.save()

    return JsonResponse({'success': True})