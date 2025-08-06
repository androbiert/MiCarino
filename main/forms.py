# love_app/forms.py
from django import forms
from .models import Message
from .models import Profile

from django import forms
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'w-full p-2 border rounded'}),
            'image': forms.FileInput(attrs={'class': 'w-full p-2'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your message here...'}),
        }