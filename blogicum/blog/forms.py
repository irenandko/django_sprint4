from django import forms

from .models import Post, Comment, User


class ProfileForm(forms.ModelForm):
    """Форма на основе модели для профиля пользователя."""

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):
    """Форма на основе модели для поста."""

    class Meta:
        model = Post
        exclude = ('author', )
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%d.%m.%Y %H:%M',
                attrs={'type': 'datetime-local'}
            ),
        }


class CommentForm(forms.ModelForm):
    """Форма на основе модели для комментариев."""

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(
                attrs={'cols': 10, 'rows': 10}
            )
        }
