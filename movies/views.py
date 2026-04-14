from django.shortcuts import get_object_or_404, render

from .models import Movie


def movie_list(request):
    movies = Movie.objects.all()
    return render(request, "movies/movie_list.html", {"movies": movies})


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    shows = movie.shows.all()
    return render(request, "movies/movie_detail.html", {"movie": movie, "shows": shows})
