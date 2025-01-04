from django.utils import timezone


def get_published_posts(queryset):
    """Фильтрует посты по опубликованности категории"""
    """и самого поста + времени публикации."""

    query_set = queryset.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )
    return query_set
