from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import Post, Category


def get_posts(post_objects):
    """Фильтрует посты по опубликованности категории"""
    """и самого поста + времени публикации."""
    return post_objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    )


def index(request):
    """Отображает на главной странице 5 последних постов."""
    template = 'blog/index.html'
    post_list = get_posts(Post.objects).order_by('-pub_date')[:5]
    context = {
        'post_list': post_list
    }
    return render(request, template, context)


def post_detail(request, id):
    """Отображает полное описание выбранной записи."""
    template = 'blog/detail.html'
    posts = get_object_or_404(get_posts(Post.objects), id=id)
    context = {
        'post': posts
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    """Отображает публикации категории."""
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    post_list = get_posts(category.posts)
    context = {
        'category': category,
        'post_list': post_list
    }
    return render(request, template, context)
