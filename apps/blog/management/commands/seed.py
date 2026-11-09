import random
import time
from collections.abc import Sequence
from typing import Any

from faker import Faker

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify

from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

SEED_PASSWORD = 'seed-password-123'
EMAIL_DOMAIN = 'example.com'

INACTIVE_USER_RATIO = 0.15
STAFF_USER_RATIO = 0.10
PUBLISHED_POST_RATIO = 0.70
POST_WITHOUT_CATEGORY_RATIO = 0.10

MIN_TAGS_PER_POST = 0
MAX_TAGS_PER_POST = 5
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
POST_TITLE_WORDS = 6
POST_PARAGRAPHS = 4

BULK_BATCH_SIZE = 500
FIRST_SUFFIX = 2
LABEL_WIDTH = 11
VALUE_WIDTH = 4
SECONDS_PRECISION = 2

SLUG_MAX_LENGTH: int = Post._meta.get_field('slug').max_length
FALLBACK_SLUG = 'post'

CATEGORY_NAMES = (
    'Python',
    'Django',
    'DevOps',
    'Databases',
    'Frontend',
    'Testing',
    'Security',
    'Career',
)

TAG_NAMES = (
    'REST API',
    'ORM',
    'Migrations',
    'Celery',
    'Redis',
    'PostgreSQL',
    'SQLite',
    'Docker',
    'Kubernetes',
    'CI/CD',
    'Nginx',
    'Gunicorn',
    'Pytest',
    'Type Hints',
    'Async',
    'Caching',
    'Authentication',
    'Deployment',
    'Performance',
    'Code Review',
)


class Command(BaseCommand):
    help = 'Fill the database with fake data.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--users',
            type=int,
            default=DEFAULT_USERS,
            help='Number of users to create',
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=DEFAULT_POSTS,
            help='Number of posts to create',
        )
        parser.add_argument(
            '--comments',
            type=int,
            default=DEFAULT_COMMENTS,
            help='Number of comments to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing data before seeding',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        users_count: int = options['users']
        posts_count: int = options['posts']
        comments_count: int = options['comments']
        clear: bool = options['clear']

        self._validate_counts(users_count, posts_count, comments_count)

        started_at = time.monotonic()
        fake = Faker()

        with transaction.atomic():
            if clear:
                self._clear()

            created = {
                'Users': self._create_users(fake, users_count),
                'Categories': self._create_named(Category, CATEGORY_NAMES),
                'Tags': self._create_named(Tag, TAG_NAMES),
                'Posts': self._create_posts(fake, posts_count),
                'Comments': self._create_comments(fake, comments_count),
            }

        self._report(created, time.monotonic() - started_at)

    def _validate_counts(self, users: int, posts: int, comments: int) -> None:
        for name, value in (('users', users), ('posts', posts), ('comments', comments)):
            if value < 0:
                raise CommandError(f'--{name} must not be negative, got {value}.')

    def _clear(self) -> None:
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('Existing data cleared (superusers kept).')

    def _create_users(self, fake: Faker, count: int) -> int:
        if count == 0:
            return 0

        used_emails = set(User.objects.values_list('email', flat=True))
        hashed_password = make_password(SEED_PASSWORD)
        users = []

        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            users.append(
                User(
                    email=self._unique_email(first_name, last_name, used_emails),
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_active=random.random() >= INACTIVE_USER_RATIO,
                    is_staff=random.random() < STAFF_USER_RATIO,
                )
            )
        User.objects.bulk_create(users, batch_size=BULK_BATCH_SIZE)
        return len(users)

    def _unique_email(self, first_name: str, last_name: str, used: set[str]) -> str:
        base = f'{slugify(first_name)}.{slugify(last_name)}'
        email = f'{base}@{EMAIL_DOMAIN}'
        suffix = FIRST_SUFFIX

        while email in used:
            email = f'{base}{suffix}@{EMAIL_DOMAIN}'
            suffix += 1

        used.add(email)
        return email

    def _create_named(self, model: type[Category] | type[Tag], names: Sequence[str]) -> int:
        used_slugs = set(model.objects.values_list('slug', flat=True))
        used_names = set(model.objects.values_list('name', flat=True))
        objects = []

        for name in names:
            slug = slugify(name)
            if slug in used_slugs or name in used_names:
                continue

            used_slugs.add(slug)
            used_names.add(name)
            objects.append(model(name=name, slug=slug))

        model.objects.bulk_create(objects, batch_size=BULK_BATCH_SIZE)
        return len(objects)

    def _create_posts(self, fake: Faker, count: int) -> int:
        if count == 0:
            return 0

        author_ids = list(User.objects.values_list('id', flat=True))
        if not author_ids:
            raise CommandError(
                'Cannot create posts: there are no users.'
                'Run the command with --users first.'
            )

        category_ids = list(Category.objects.values_list('id', flat=True))
        tag_ids = list(Tag.objects.values_list('id', flat=True))
        used_slugs = set(Post.objects.values_list('slug', flat=True))
        posts = []

        for _ in range(count):
            title = fake.sentence(nb_words=POST_TITLE_WORDS).rstrip('.')
            posts.append(
                Post(
                    author_id = random.choice(author_ids),
                    title=title,
                    slug=self._unique_slug(title, used_slugs),
                    body='\n\n'.join(fake.paragraphs(nb=POST_PARAGRAPHS)),
                    category_id = self._pick_category_id(category_ids),
                    status=self._pick_status(),
                )
            )

        Post.objects.bulk_create(posts, batch_size=BULK_BATCH_SIZE)
        self._attach_tags(posts, tag_ids)
        return len(posts)

    def _pick_category_id(self, category_ids: list[int]) -> int | None:
        if not category_ids or random.random() < POST_WITHOUT_CATEGORY_RATIO:
            return None

        return random.choice(category_ids)

    def _pick_status(self) -> str:
        if random.random() < PUBLISHED_POST_RATIO:
            return Post.Status.PUBLISHED

        return Post.Status.DRAFT

    def _unique_slug(self, title: str, used: set[str]) -> str:
        base = slugify(title)[:SLUG_MAX_LENGTH] or FALLBACK_SLUG
        slug = base
        suffix = FIRST_SUFFIX

        while slug in used:
            tail = f'-{suffix}'
            slug = f'{base[: SLUG_MAX_LENGTH - len(tail)]}{tail}'
            suffix += 1

        used.add(slug)
        return slug

    def _attach_tags(self, posts: list[Post], tag_ids: list[int]) -> None:
        if not tag_ids:
            return

        max_tags = min(MAX_TAGS_PER_POST, len(tag_ids))

        for post in posts:
            tags_count = random.randint(MIN_TAGS_PER_POST, max_tags)
            if tags_count:
                post.tags.set(random.sample(tag_ids, tags_count))

    def _create_comments(self, fake: Faker, count: int) -> int:
        if count == 0:
            return 0

        author_ids = list(User.objects.values_list('id', flat=True))
        if not author_ids:
            raise CommandError(
                'Cannot create comments: there are no users. '
                'Run the command with --users first.'
            )

        post_ids = list(
            Post.objects.filter(status=Post.Status.PUBLISHED).values_list('id', flat=True)
        )
        if not post_ids:
            raise CommandError(
                'Cannot create comments: there are no published posts. '
                'Run the command with --posts first.'
            )

        comments = [
            Comment(
                post_id=random.choice(post_ids),
                author_id=random.choice(author_ids),
                body=' '.join(
                    fake.sentences(
                        nb=random.randint(MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES)
                    )
                ),
            )
            for _ in range(count)
        ]

        Comment.objects.bulk_create(comments, batch_size=BULK_BATCH_SIZE)
        return len(comments)

    def _report(self, created: dict[str, int], elapsed: float) -> None:
        for label, value in created.items():
            self.stdout.write(f'{label + ":":<{LABEL_WIDTH}}{value:>{VALUE_WIDTH}} created')

        self.stdout.write(
            self.style.SUCCESS(f'Done in {elapsed:.{SECONDS_PRECISION}f} seconds')
        )