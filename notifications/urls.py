from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications_list'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
    path('contact-request/<int:user_id>/', views.send_contact_request, name='send_contact_request'),
    path('contact-request/<int:request_id>/<str:action>/', views.handle_contact_request, name='handle_contact_request'),
]