# love_app/admin.py
from django.contrib import admin
from .models import Message , Profile, Discussion,DiscussionPresence

admin.site.register(Message)
admin.site.register(Profile)
admin.site.register(Discussion)
admin.site.register(DiscussionPresence)