import json
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpRequest
from django.urls import reverse_lazy

from apps.blog.models import Category, Comment, Post
from settings.conf import ENV_ID, ENV_ID_PROD

User = get_user_model()

PERCENT = 100
TOP_AUTHORS_LIMIT = 5
PERCENT_PRECISION = 1
CHART_BAR_COLOR = '#0284c7'
CHART_BAR_RADIUS = 4
CHART_BAR_THICKNESS = 40

ENVIRONMENT_LOCAL = ['Local', 'warning']
ENVIRONMENT_PRODUCTION = ['Production', 'danger']


def environment_callback(request: HttpRequest) -> list[str]:
    """Badge shown next to the site header."""
    if ENV_ID == ENV_ID_PROD:
        return ENVIRONMENT_PRODUCTION

    return ENVIRONMENT_LOCAL


def drafts_badge(request: HttpRequest) -> int:
    """Number of drafts, shown as a badge on the Posts menu item."""
    return Post.objects.filter(status=Post.Status.DRAFT).count()


def navigation_callback(request: HttpRequest) -> list[dict[str, Any]]:
    """Sidebar menu. The last group is visible to superusers only."""
    navigation = [
        {
            'title': 'Overview',
            'separator': False,
            'items': [
                {
                    'title': 'Dashboard',
                    'icon': 'dashboard',
                    'link': reverse_lazy('admin:index'),
                },
            ],
        },
        {
            'title': 'Content',
            'separator': True,
            'items': [
                {
                    'title': 'Posts',
                    'icon': 'article',
                    'link': reverse_lazy('admin:blog_post_changelist'),
                    'badge': 'apps.blog.callbacks.drafts_badge',
                },
                {
                    'title': 'Comments',
                    'icon': 'forum',
                    'link': reverse_lazy('admin:blog_comment_changelist'),
                },
                {
                    'title': 'Categories',
                    'icon': 'folder',
                    'link': reverse_lazy('admin:blog_category_changelist'),
                },
                {
                    'title': 'Tags',
                    'icon': 'sell',
                    'link': reverse_lazy('admin:blog_tag_changelist'),
                },
            ],
        },
    ]

    if request.user.is_superuser:
        navigation.append(
            {
                'title': 'Users & Access',
                'separator': True,
                'items': [
                    {
                        'title': 'Users',
                        'icon': 'person',
                        'link': reverse_lazy('admin:auths_user_changelist'),
                    },
                    {
                        'title': 'Groups',
                        'icon': 'shield_person',
                        'link': reverse_lazy('admin:auth_group_changelist'),
                    },
                ],
            }
        )

    return navigation


def tabs_callback(request: HttpRequest) -> list[dict[str, Any]]:
    """Tabs above the post list. Built at request time so reverse() is safe."""
    posts_url = str(reverse_lazy('admin:blog_post_changelist'))

    return [
        {
            'models': ['blog.post'],
            'items': [
                {'title': 'All', 'link': posts_url},
                {
                    'title': 'Published',
                    'link': f'{posts_url}?status__exact={Post.Status.PUBLISHED}',
                },
                {
                    'title': 'Drafts',
                    'link': f'{posts_url}?status__exact={Post.Status.DRAFT}',
                },
            ],
        },
    ]


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """Data for the admin home page."""
    totals = Post.objects.aggregate(
        published=Count('id', filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count('id', filter=Q(status=Post.Status.DRAFT)),
    )
    published: int = totals['published']
    drafts: int = totals['drafts']

    context.update(
        {
            'kpi_cards': [
                {'title': 'Users', 'value': User.objects.count(), 'icon': 'group'},
                {'title': 'Published posts', 'value': published, 'icon': 'article'},
                {'title': 'Drafts', 'value': drafts, 'icon': 'edit_note'},
                {'title': 'Comments', 'value': Comment.objects.count(), 'icon': 'forum'},
            ],
            'posts_per_category_chart': json.dumps(_posts_per_category()),
            'top_authors_table': _top_authors(),
            'status_progress': _status_progress(published, drafts),
        }
    )

    return context


def _posts_per_category() -> dict[str, Any]:
    categories = Category.objects.annotate(posts_count=Count('posts')).order_by('-posts_count')

    return {
        'labels': [category.name for category in categories],
        'datasets': [
            {
                'label': 'Posts',
                'data': [category.posts_count for category in categories],
                'backgroundColor': CHART_BAR_COLOR,
                'borderRadius': CHART_BAR_RADIUS,
                'maxBarThickness': CHART_BAR_THICKNESS,
            }
        ],
    }


def _top_authors() -> dict[str, Any]:
    authors = (
        User.objects.annotate(posts_count=Count('posts'))
        .filter(posts_count__gt=0)
        .order_by('-posts_count', 'email')[:TOP_AUTHORS_LIMIT]
    )

    return {
        'headers': ['Author', 'Email', 'Posts'],
        'rows': [
            [f'{author.first_name} {author.last_name}', author.email, author.posts_count]
            for author in authors
        ],
    }


def _status_progress(published: int, drafts: int) -> list[dict[str, Any]]:
    total = published + drafts
    if not total:
        return []

    return [
        {
            'title': 'Published',
            'value': round(published / total * PERCENT, PERCENT_PRECISION),
            'count': published,
        },
        {
            'title': 'Drafts',
            'value': round(drafts / total * PERCENT, PERCENT_PRECISION),
            'count': drafts,
        },
    ]