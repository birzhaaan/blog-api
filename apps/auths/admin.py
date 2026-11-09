from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.auths.forms import UserCreateForm, UserPasswordChangeForm, UserUpdateForm
from apps.auths.models import User

INITIALS_LENGTH = 1

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    """Re-registered with Unfold so it does not fall back to the plain admin."""

    search_fields = ('name',)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserUpdateForm
    add_form = UserCreateForm
    change_password_form = UserPasswordChangeForm

    ordering = ('email',)
    list_display = ('user_header', 'active_label', 'staff_label', 'posts_count')
    list_filter = (
        ('is_active', BooleanRadioFilter),
        ('is_staff', BooleanRadioFilter),
    )
    list_filter_submit = True
    search_fields = ('email', 'first_name', 'last_name')
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('last_login',)
    actions = ('activate_users', 'deactivate_users')
    warn_unsaved_form = True

    fieldsets = (
        (
            'Personal info',
            {
                'classes': ('tab',),
                'fields': ('email', 'password', 'first_name', 'last_name'),
            },
        ),
        (
            'Permissions',
            {
                'classes': ('tab',),
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (
            'Important dates',
            {
                'classes': ('tab',),
                'fields': ('last_login',),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'usable_password',
                    'password1',
                    'password2',
                ),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(posts_total=Count('posts'))

    @display(description='User', header=True)
    def user_header(self, obj: User) -> list[str]:
        full_name = f'{obj.first_name} {obj.last_name}'.strip()
        initials = f'{obj.first_name[:INITIALS_LENGTH]}{obj.last_name[:INITIALS_LENGTH]}'
        return [full_name or obj.email, obj.email, initials.upper(), None]

    @display(
        description='Active',
        ordering='is_active',
        label={True: 'success', False: 'danger'},
    )
    def active_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_active, 'Active' if obj.is_active else 'Inactive'

    @display(
        description='Staff',
        ordering='is_staff',
        label={True: 'info', False: 'secondary'},
    )
    def staff_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_staff, 'Staff' if obj.is_staff else 'Regular'

    @display(description='Posts', ordering='posts_total')
    def posts_count(self, obj: User) -> int:
        return obj.posts_total

    @action(description='Activate selected users', icon='person_check')
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')

    @action(description='Deactivate selected users', icon='person_off')
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')