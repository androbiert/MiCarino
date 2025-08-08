# love_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_images/', default='profile_images/default.png')
    bio = models.TextField(blank=True, default='I LOVE YOU ❤️ !')

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def is_online(self):
        if self.last_seen:
            return timezone.now() - self.last_seen < timedelta(seconds=60)
        return False

class Discussion(models.Model):
    participants = models.ManyToManyField(User, related_name='discussions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Discussion {self.id}"

    def get_other_participant(self, user):
        """Return the other participant in the discussion"""
        return self.participants.exclude(id=user.id).first()

class Message(models.Model):
    discussion = models.ForeignKey(Discussion, related_name='messages', on_delete=models.CASCADE,null=True, blank=True)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    liked_by = models.ManyToManyField(User, related_name="liked_messages", blank=True)  # NEW

    def likes_count(self):
        return self.liked_by.count()
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"



class DiscussionPresence(models.Model):
    discussion = models.ForeignKey('Discussion', on_delete=models.CASCADE, related_name='presences')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('discussion', 'user')

    def __str__(self):
        return f"{self.user.username} presence in discussion {self.discussion_id} at {self.last_seen}"