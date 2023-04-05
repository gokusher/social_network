from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model


User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
