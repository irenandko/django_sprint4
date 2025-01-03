from django import forms
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Post, Comment


class ProfileForm(forms.ModelForm):
    """Форма по модели для профиля пользователя."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class PostForm(forms.ModelForm):
    """Форма для поста."""
    
    class Meta:
        model = Post
        exclude = ['author', ]
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%d.%m.%Y %H:%M',
                attrs={'type': 'datetime-local'}
            ),
        }


class CommentForm(forms.ModelForm):
    """Форма по модели для комментариев."""

    class Meta:
        model = Comment
        fields = ['text',]
