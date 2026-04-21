from django.contrib import admin
from .models import Movie, Theatre, Show


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "language",
        "genre",
        "format",
        "release_date",
        "meta_type",
        "meta_value",
        "is_premiere",
    )
    list_filter = ("language", "genre", "format", "is_premiere", "meta_type")
    search_fields = ("title", "genre", "language", "format", "card_subtitle")


admin.site.register(Theatre)
admin.site.register(Show)