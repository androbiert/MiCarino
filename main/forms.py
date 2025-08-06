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
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'اكتب رسالتك هنا...'}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'})
        }