from django.shortcuts import get_object_or_404, render

from .models import Movie


def movie_list(request):
    movies = Movie.objects.all()
    return render(request, "movies/movie_list.html", {"movies": movies})


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    shows = movie.shows.all()
    reviews = movie.reviews.all().order_by("-created_at")
    comments = movie.comments.filter(parent__isnull=True).order_by("-created_at")

    user_liked_reviews = set()
    if request.user.is_authenticated:
        user_liked_reviews = set(
            request.user.like_set.filter(review__movie=movie).values_list(
                "review_id", flat=True
            )
        )

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "shows": shows,
            "reviews": reviews,
            "comments": comments,
            "user_liked_reviews": user_liked_reviews,
        },
    )
