from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from .forms import CreationForm, EditProfileForm


class UserEditView(UpdateView):
    form_class = EditProfileForm
    template_name = 'users/edit_profile.html'
    success_url = reverse_lazy('posts:index')

    def get_object(self):
        return self.request.user


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'
