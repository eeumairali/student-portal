from .models import Notification


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "unread_notification_count": Notification.objects.filter(
            student=request.user, is_read=False
        ).count()
    }
