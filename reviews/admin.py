from django.contrib import admin

from .models import Comment, Like, Review

admin.site.register(Review)
admin.site.register(Like)
admin.site.register(Comment)
