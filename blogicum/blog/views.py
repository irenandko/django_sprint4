from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Value
from django.db.models.functions import Coalesce

from .models import Post, Category, Comment, User
from .forms import PostForm, CommentForm, ProfileForm
from .mixins import PostMixin, CommentMixin

from core.utils import get_published_posts


# Страница профиля и работа с ней


class ProfileView(ListView):
    """Отображает профиль пользователя и его записи."""

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        self.author = get_object_or_404(
            User,
            username=self.kwargs.get('username')
        )
        if self.author != self.request.user:
            return super().get_queryset().filter(
                author=self.author,
                is_published=True,
                category__is_published=True,
            ).annotate(
                comment_count=Coalesce(Count('comments'), Value(0))
            ).order_by('-pub_date')

        return super().get_queryset().filter(
            author=self.author
        ).annotate(
            comment_count=Coalesce(Count('comments'), Value(0))
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
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


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    """Отображает интерфейс создания поста."""

    login_url = '/login/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user
        return reverse("blog:profile", kwargs={"username": username})


class PostUpdateView(PostMixin, LoginRequiredMixin, UpdateView):
    """Отображает интерфейс редактирования поста + проверяет
    авторизирован ли пользователь и он ли автор поста.
    """

    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):

        self.object = self.get_object()
        is_auth_author = (self.request.user.is_authenticated
                          and self.object.author == self.request.user)

        if not is_auth_author:
            return redirect(
                reverse(
                    'blog:post_detail',
                    kwargs={'pk': self.object.pk}
                )
            )
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.pk}
        )


class PostDetailView(DetailView):
    """Отображает содержание выбранного поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        object = super().get_object(
            self.model.objects.select_related(
                'location', 'category', 'author'
            ),
        )
        if object.author != self.request.user:
            return get_object_or_404(
                self.model.objects.select_related(
                    'location', 'category', 'author'
                ).filter(
                    pub_date__lte=timezone.now(),
                    category__is_published=True,
                    is_published=True
                ),
                pk=self.kwargs['pk']
            )
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Отображает форму удаления поста + проверяет,
    пытается ли это сделать именно авторизированный автор поста.
    """

    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class PostListView(ListView):
    """Отображает список постов главной страницы."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = get_published_posts(super().get_queryset())
        queryset = (
            queryset.select_related('author')
            .prefetch_related('category', 'location')
            .annotate(comment_count=Coalesce(Count('comments'), Value(0)))
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
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

        return super().get_queryset().filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
            category__slug=self.kwargs['category_slug']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


# Комментарии и работа с ними


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Отображает форму создания комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs.get('post_id')
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:post_detail',
                       kwargs={'pk': self.kwargs.get('post_id')})


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    """Отображает форму редактирования комментария."""
    
    form_class = CommentForm
    success_url = reverse_lazy('blog:index')


class DeleteCommentView(CommentMixin, LoginRequiredMixin, DeleteView):
    """Отображает форму удаления комментария."""
