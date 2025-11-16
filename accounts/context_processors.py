# messenger_app/accounts/context_processors.py
from .models import FriendRequest

def friend_request_counts(request):
    if request.user.is_authenticated:
        pending_count = FriendRequest.objects.filter(
            to_user=request.user,
            status='pending'
        ).count()
        return {
            'pending_friend_requests_count': pending_count
        }
    return {}