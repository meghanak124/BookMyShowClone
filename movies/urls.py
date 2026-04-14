from django.urls import path

from .views import movie_detail, movie_list

urlpatterns = [
    path("", movie_list, name="movie_list"),
    path("<int:movie_id>/", movie_detail, name="movie_detail"),
]
