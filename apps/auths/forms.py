from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.auths.models import User

CREATION_FIELDS = ('email', 'first_name', 'last_name')

class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = CREATION_FIELDS

class UserUpdateForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

class UserPasswordChangeForm(AdminPasswordChangeForm):
    pass