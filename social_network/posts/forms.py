from django import forms
from django.core.exceptions import ValidationError

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

    def clean_text(self):
        '''Самая примитивная реализация отбора'''
        old_comment = self.cleaned_data['text']
        comment = self.cleaned_data['text']
        regulation = ['Пушкин', 'Толстой']
        for element in range(len(regulation)):
            regulation[element] = regulation[element].upper()
        regulation = set(regulation)
        comment = comment.upper()
        comment = set(comment.split(' '))
        if comment.intersection(regulation):
            raise ValidationError("Forbidden word!")
        return old_comment
