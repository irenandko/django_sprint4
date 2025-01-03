from blog.models import Post
from django.utils import timezone


def get_all_posts():
    """Возвращает все посты."""
    query_set = (
        Post.objects.select_related(
            "category",
            "location",
            "author",
        )
    )
    return query_set


def get_published_posts(queryset):
    """Фильтрует посты по опубликованности категории"""
    """и самого поста + времени публикации."""

    query_set = get_all_posts().filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )
    return query_set
