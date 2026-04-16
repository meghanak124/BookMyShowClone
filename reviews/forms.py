from django import forms

from .models import Comment, Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["content", "rating"]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
