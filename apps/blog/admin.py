from typing import Any

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from django.contrib import admin, messages
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from apps.blog.models import Category, Comment, Post, Tag

COMMENT_BODY_PREVIEW_LENGTH = 60
INLINE_COMMENTS_PER_PAGE = 10
ELLIPSIS = '…'


class PostCommentsSection(TableSection):
    verbose_name = 'Comments'
    related_name = 'comments'
    fields = ('author', 'body', 'created_at')


class CategoryPostsSection(TableSection):
    verbose_name = 'Posts in this category'
    related_name = 'posts'
    fields = ('title', 'status', 'created_at')


class CommentInline(TabularInline):
    model = Comment
    extra = 0
    tab = True
    per_page = INLINE_COMMENTS_PER_PAGE
    ordering = ('-created_at',)
    fields = ('author', 'body', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('author',)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'posts_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_sections = (CategoryPostsSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return (
            super()
            .get_queryset(request)
            .prefetch_related('posts')
            .annotate(posts_total=Count('posts', distinct=True))
        )

    @display(description='Posts', ordering='posts_total')
    def posts_count(self, obj: Category) -> int:
        return obj.posts_total


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'posts_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return super().get_queryset(request).annotate(posts_total=Count('posts'))

    @display(description='Posts', ordering='posts_total')
    def posts_count(self, obj: Tag) -> int:
        return obj.posts_total


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('post_title', 'author', 'body_preview', 'created_at')
    list_filter = (
        ('post', AutocompleteSelectFilter),
        ('author', AutocompleteSelectFilter),
        ('created_at', RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ('body', 'author__email', 'post__title')
    autocomplete_fields = ('post', 'author')
    list_select_related = ('post', 'author')
    readonly_fields = ('created_at',)

    @display(description='Post', ordering='post__title')
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description='Comment')
    def body_preview(self, obj: Comment) -> str:
        if len(obj.body) <= COMMENT_BODY_PREVIEW_LENGTH:
            return obj.body

        return f'{obj.body[:COMMENT_BODY_PREVIEW_LENGTH].rstrip()}{ELLIPSIS}'


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        'post_header',
        'status_label',
        'category',
        'tags_dropdown',
        'comments_count',
        'created_at',
    )
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('category', RelatedDropdownFilter),
        ('tags', MultipleRelatedDropdownFilter),
        ('author', AutocompleteSelectFilter),
        ('created_at', RangeDateTimeFilter),
    )
    list_filter_submit = True
    ordering = ('-created_at',)
    search_fields = ('title', 'body', 'author__email')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('author', 'category', 'tags')
    readonly_fields = ('created_at', 'updated_at')
    list_sections = (PostCommentsSection,)
    inlines = (CommentInline,)
    warn_unsaved_form = True

    actions = ('publish_selected', 'move_to_drafts')
    actions_row = ('toggle_publish',)
    actions_list = ('publish_all_drafts',)
    actions_detail = ('open_comments',)
    actions_submit_line = ('save_and_publish',)

    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},
    }

    fieldsets = (
        (
            'Content',
            {
                'classes': ('tab',),
                'fields': ('title', 'slug', 'body'),
            },
        ),
        (
            'Classification',
            {
                'classes': ('tab',),
                'fields': ('category', 'tags', 'status'),
            },
        ),
        (
            'Meta',
            {
                'classes': ('tab',),
                'fields': ('author', 'created_at', 'updated_at'),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .select_related('author', 'category')
            .prefetch_related('tags', 'comments__author')
            .annotate(comments_total=Count('comments', distinct=True))
        )

    @display(description='Post', header=True)
    def post_header(self, obj: Post) -> list[str | None]:
        return [obj.title, obj.author.email, None, None]

    @display(
        description='Status',
        ordering='status',
        label={Post.Status.PUBLISHED: 'success', Post.Status.DRAFT: 'warning'},
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description='Tags', dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict[str, Any]:
        tags = list(obj.tags.all())

        return {
            'title': f'{len(tags)} tags',
            'items': [{'title': tag.name} for tag in tags],
        }

    @display(description='Comments', ordering='comments_total')
    def comments_count(self, obj: Post) -> int:
        return obj.comments_total

    @action(description='Publish selected', icon='publish')
    def publish_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f'{updated} post(s) published.', messages.SUCCESS)

    @action(description='Move to drafts', icon='drafts')
    def move_to_drafts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f'{updated} post(s) moved to drafts.', messages.SUCCESS)

    @action(description='Publish / unpublish', icon='swap_horiz', url_path='toggle-publish')
    def toggle_publish(self, request: HttpRequest, object_id: int) -> HttpResponse:
        post = Post.objects.get(pk=object_id)
        post.status = (
            Post.Status.DRAFT
            if post.status == Post.Status.PUBLISHED
            else Post.Status.PUBLISHED
        )
        post.save(update_fields=('status', 'updated_at'))
        self.message_user(
            request, f'"{post.title}" is now {post.get_status_display().lower()}.'
        )

        return redirect(reverse('admin:blog_post_changelist'))

    @action(description='Publish all drafts', icon='publish', url_path='publish-all-drafts')
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponse:
        updated = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED
        )
        self.message_user(request, f'{updated} draft(s) published.', messages.SUCCESS)

        return redirect(reverse('admin:blog_post_changelist'))

    @action(description='Open comments', icon='forum', url_path='open-comments')
    def open_comments(self, request: HttpRequest, object_id: int) -> HttpResponse:
        url = reverse('admin:blog_comment_changelist')

        return redirect(f'{url}?post__id__exact={object_id}')

    @action(description='Save & publish', icon='publish')
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=('status', 'updated_at'))
        self.message_user(request, f'"{obj.title}" published.', messages.SUCCESS)