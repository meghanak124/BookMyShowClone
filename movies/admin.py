from django.contrib import admin

# Register your models here.
from .models import Movie, Show, Theatre

admin.site.register(Movie)
admin.site.register(Theatre)
admin.site.register(Show)
