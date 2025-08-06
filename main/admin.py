# love_app/admin.py
from django.contrib import admin
from .models import Message , Profile, Discussion

admin.site.register(Message)
admin.site.register(Profile)
admin.site.register(Discussion)