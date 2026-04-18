from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Movie, Theatre, Show


def movie_list(request):
    movies = Movie.objects.all()

    query = request.GET.get("q", "").strip()
    selected_languages = request.GET.getlist("language")
    selected_genres = request.GET.getlist("genre")

    if query:
        movies = movies.filter(title__icontains=query)

    if selected_languages:
        filtered_ids = []
        for movie in movies:
            movie_languages = movie.language.split()
            if any(lang in movie_languages for lang in selected_languages):
                filtered_ids.append(movie.id)
        movies = movies.filter(id__in=filtered_ids)

    if selected_genres:
        filtered_ids = []
        for movie in movies:
            movie_genres = movie.genre.split()
            if any(genre in movie_genres for genre in selected_genres):
                filtered_ids.append(movie.id)
        movies = movies.filter(id__in=filtered_ids)

    all_languages_raw = Movie.objects.values_list("language", flat=True)
    language_set = set()
    for value in all_languages_raw:
        if value:
            for lang in value.split():
                language_set.add(lang.strip())

    all_genres_raw = Movie.objects.values_list("genre", flat=True)
    genre_set = set()
    for value in all_genres_raw:
        if value:
            for genre in value.split():
                genre_set.add(genre.strip())

    context = {
        "movies": movies.distinct(),
        "all_languages": sorted(language_set),
        "all_genres": sorted(genre_set),
        "selected_languages": selected_languages,
        "selected_genres": selected_genres,
        "query": query,
    }
    return render(request, "movies/movie_list.html", context)


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    shows = movie.shows.select_related("theatre").all()
    reviews = movie.reviews.all().order_by("-created_at")
    comments = movie.comments.filter(parent__isnull=True).order_by("-created_at")
    now = timezone.localtime()

    for show in shows:
        show.is_ended = show.show_time <= now
        show.is_sold_out = int(show.available_seats) <= 0
        show.can_book = (not show.is_ended) and (not show.is_sold_out)

    user_liked_reviews = set()
    if request.user.is_authenticated:
        user_liked_reviews = set(
            request.user.like_set.filter(review__movie=movie).values_list("review_id", flat=True)
        )

    return render(request, "movies/movie_detail.html", {
        "movie": movie,
        "shows": shows,
        "reviews": reviews,
        "comments": comments,
        "user_liked_reviews": user_liked_reviews,
        "now": now,
    })

def browse_cinemas(request):
    now = timezone.localtime()

    theatres = Theatre.objects.filter(
        shows__show_time__gt=now
    ).distinct()

    theatre_data = []
    for theatre in theatres:
        active_shows = Show.objects.filter(
            theatre=theatre,
            show_time__gt=now,
            available_seats__gt=0
        ).select_related("movie").order_by("show_time")

        if active_shows.exists():
            theatre_data.append({
                "theatre": theatre,
                "shows": active_shows,
            })

    return render(request, "movies/browse_cinemas.html", {
        "theatre_data": theatre_data,
    })