from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
import json
from .models import Invitation, CustomUser
from .forms import InvitationForm, BulkInvitationForm


@login_required
def invite_user(request):
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            # Create invitation logic here
            invitation = Invitation.objects.create(
                inviter=request.user,
                email=form.cleaned_data.get('email'),
                phone_number=form.cleaned_data.get('phone_number'),
                message=form.cleaned_data.get('message', ''),
                invitation_type='email' if form.cleaned_data.get('email') else 'phone',
                expires_at=timezone.now() + timedelta(days=7)
            )

            # Send invitation email
            if invitation.email:
                send_invitation_email(invitation)

            messages.success(request, f"Invitation sent successfully to {invitation.email or invitation.phone_number}!")
            return redirect('invitations_list')
    else:
        form = InvitationForm()

    return render(request, 'accounts/invite_user.html', {
        'form': form,
        'active_tab': 'invite'
    })


@login_required
def bulk_invite(request):
    if request.method == 'POST':
        form = BulkInvitationForm(request.POST)
        if form.is_valid():
            contacts_text = form.cleaned_data['contacts']
            message = form.cleaned_data.get('message', '')

            # Process contacts (simple implementation)
            contacts = [contact.strip() for contact in contacts_text.split('\n') if contact.strip()]
            success_count = 0

            for contact in contacts:
                try:
                    if '@' in contact:  # Email
                        invitation = Invitation.objects.create(
                            inviter=request.user,
                            email=contact,
                            message=message,
                            invitation_type='email',
                            expires_at=timezone.now() + timedelta(days=7)
                        )
                        send_invitation_email(invitation)
                    else:  # Phone
                        invitation = Invitation.objects.create(
                            inviter=request.user,
                            phone_number=contact,
                            message=message,
                            invitation_type='phone',
                            expires_at=timezone.now() + timedelta(days=7)
                        )
                    success_count += 1
                except:
                    pass  # Skip duplicates

            messages.success(request, f"Successfully sent {success_count} invitation(s)!")
            return redirect('invitations_list')
    else:
        form = BulkInvitationForm()

    return render(request, 'accounts/bulk_invite.html', {
        'form': form,
        'active_tab': 'bulk_invite'
    })


@login_required
def invitations_list(request):
    invitations = Invitation.objects.filter(inviter=request.user).order_by('-created_at')
    return render(request, 'accounts/invitations_list.html', {
        'invitations': invitations,
        'active_tab': 'invitations_list'
    })


@login_required
def cancel_invitation(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id, inviter=request.user)

    if invitation.status == 'pending':
        invitation.status = 'expired'
        invitation.save()
        messages.success(request, "Invitation cancelled successfully.")
    else:
        messages.error(request, "Cannot cancel this invitation.")

    return redirect('invitations_list')


def send_invitation_email(invitation):
    """Send invitation email to the recipient"""
    if invitation.invitation_type == 'email' and invitation.email:
        subject = f"Join me on Messenger!"
        message = f"""
        Hi there!

        {invitation.inviter.username} has invited you to join Messenger, a real-time chatting app.

        {invitation.message if invitation.message else "Connect with friends and family with instant messaging, video calls, and more!"}

        Click the link below to join:
        {settings.SITE_URL}/register/

        This invitation will expire in 7 days.

        Looking forward to chatting with you!

        The Messenger Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )


@login_required
def check_contact_exists(request):
    """Check if a contact already exists in the system"""
    email = request.GET.get('email', '')
    phone_number = request.GET.get('phone_number', '')

    exists = False
    message = ''

    if email:
        exists = CustomUser.objects.filter(email=email).exists()
        if exists:
            message = 'User with this email already exists'
    elif phone_number:
        exists = CustomUser.objects.filter(phone_number=phone_number).exists()
        if exists:
            message = 'User with this phone number already exists'

    return JsonResponse({'exists': exists, 'message': message})


@login_required
def get_invitations_stats(request):
    """Get invitation statistics for the current user"""
    total_invitations = Invitation.objects.filter(inviter=request.user).count()
    pending_invitations = Invitation.objects.filter(inviter=request.user, status='pending').count()
    accepted_invitations = Invitation.objects.filter(inviter=request.user, status='accepted').count()

    return JsonResponse({
        'total': total_invitations,
        'pending': pending_invitations,
        'accepted': accepted_invitations
    })