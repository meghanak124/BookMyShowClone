from django.urls import path
from .views import movie_list, movie_detail, browse_cinemas

urlpatterns = [
    path("", movie_list, name="movie_list"),
    path("browse-cinemas/", browse_cinemas, name="browse_cinemas"),
    path("<int:movie_id>/", movie_detail, name="movie_detail"),
]