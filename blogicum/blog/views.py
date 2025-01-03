from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView)
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.db.models import Count
from django.http import Http404
from django.core.exceptions import PermissionDenied

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileForm
from core.utils import get_published_posts


User = get_user_model()

# Страница профиля и работа с ней


class ProfileView(ListView):
    """Отображает профиль пользователя и его записи."""

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs['username']      # через URL
        user_profile = get_object_or_404(User, username=username)
        posts = Post.objects.filter(author=user_profile)
        posts = get_published_posts(posts)
        posts = (
            posts.select_related('author')
            .prefetch_related('category', 'location')
        )
        posts_count = posts.annotate(comment_count=Count('comments'))
        return posts_count.order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'profile' not in context:
            context['profile'] = get_object_or_404(
                User, username=self.kwargs['username'])
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля."""

    model = User
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.object.username}
        )

    def get_object(self):
        return self.request.user


# Посты и работа с ними

class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class PostCreateView(CreateView, LoginRequiredMixin):
    """Отображает интерфейс создания поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    login_url = '/login/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user
        return reverse("blog:profile", kwargs={"username": username})


class PostUpdateView(UpdateView, PostMixin, LoginRequiredMixin):
    """Отображает интерфейс редактирования поста + проверяет
    авторизирован ли пользователь и он ли автор поста.
    """

    def dispatch(self, request, *args, **kwargs):

        self.object = self.get_object()
        is_auth_author = (self.request.user.is_authenticated and
                          self.object.author == self.request.user)

        if not is_auth_author:
            return redirect(
                reverse(
                    'blog:post_detail',
                    kwargs={'post_id': self.kwargs['pk']}
                )
            )
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class PostDetailView(DetailView):
    """Отображает содержание выбранного поста."""

    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id)
        if (
            post.author == self.request.user
            or (post.is_published and post.category.is_published
                and post.pub_date <= timezone.now())
        ):
            return post
        raise Http404('Страница с таким адресом не найдена.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        comments = post.comments.all().order_by('created_at')
        context['form'] = CommentForm()
        context['comments'] = comments

        return context


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Отображает форму удаления поста + проверяет,
    пытается ли это сделать именно авторизированный автор поста.
    """

    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)


class PostListView(ListView):
    """Отображает список постов главной страницы."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = get_published_posts(Post.objects)
        queryset = (
            queryset.select_related('author')
            .prefetch_related('category', 'location')
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )
        return queryset


# Страница категории

class CategoryView(ListView):
    """Отображает посты выбранной категории."""

    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )

        queryset = Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category=self.category
        ).select_related('author',
                         'category',
                         'location').order_by('-pub_date')

        queryset = (
            queryset.annotate(comment_count=Count('comments'))
            .filter(category__is_published=True)
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


# Посты и работа с ними

class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'


class CommentCreateView(CreateView, LoginRequiredMixin, CommentMixin):
    """Отображает форму создания комментария."""

    def form_valid(self, form):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'post_id': post_id})


class CommentUpdateView(UpdateView, LoginRequiredMixin, CommentMixin):
    """Отображает форму редактирования комментария."""

    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != request.user:
            raise PermissionDenied(
                'Вы не авторизованы для редактирования этого комментария.'
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_id'] = self.kwargs.get('post_id')
        return context


class DeleteCommentView(DeleteView, LoginRequiredMixin):
    """Отображает форму удаления комментария."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != request.user:
            raise PermissionDenied(
                'Для удаления комментария нужно авторизироваться.'
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
