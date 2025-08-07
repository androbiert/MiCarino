from .models import Message

def unread_message_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            discussion__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        return {'unread_count': count}
    return {'unread_count': 0}
