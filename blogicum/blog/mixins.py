from .models import Post, Comment
from .forms import PostForm
from django.shortcuts import redirect
from django.urls import reverse


class PostMixin:
    """Миксин для создания и редактирования поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class CommentMixin:
    """Миксин для редактирования и удаления комментария."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['post_id']])
