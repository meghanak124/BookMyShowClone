from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Movie, Show, Theatre


def movie_list(request):
    movies = Movie.objects.all()

    query = request.GET.get("q", "").strip()
    selected_location = request.GET.get("location", "").strip()
    if selected_location:
        request.session["selected_location"] = selected_location
    else:
        selected_location = request.session.get("selected_location", "Hyderabad")
    selected_languages = request.GET.getlist("language")
    selected_genres = request.GET.getlist("genre")
    selected_formats = request.GET.getlist("format")

    if selected_location:
        request.session["selected_location"] = selected_location

    if query:
        movies = movies.filter(title__icontains=query)

    if selected_location:
        movie_ids = Show.objects.filter(
            theatre__location__icontains=selected_location
        ).values_list("movie_id", flat=True).distinct()
        movies = movies.filter(id__in=movie_ids)

    if selected_languages:
        filtered_ids = []
        for movie in movies:
            langs = [lang.strip() for lang in movie.language.split(",")]
            if any(lang in langs for lang in selected_languages):
                filtered_ids.append(movie.id)
        movies = movies.filter(id__in=filtered_ids)

    if selected_genres:
        filtered_ids = []
        for movie in movies:
            genres = [genre.strip() for genre in movie.genre.split(",")]
            if any(genre in genres for genre in selected_genres):
                filtered_ids.append(movie.id)
        movies = movies.filter(id__in=filtered_ids)

    if selected_formats:
        filtered_ids = []
        for movie in movies:
            formats = [fmt.strip() for fmt in (movie.format or "").split(",") if fmt.strip()]
            if any(fmt in formats for fmt in selected_formats):
                filtered_ids.append(movie.id)
        movies = movies.filter(id__in=filtered_ids)

    all_languages = set()
    all_genres = set()
    all_formats = set()

    for movie in Movie.objects.all():
        for lang in movie.language.split(","):
            if lang.strip():
                all_languages.add(lang.strip())

        for genre in movie.genre.split(","):
            if genre.strip():
                all_genres.add(genre.strip())

        for fmt in (movie.format or "").split(","):
            if fmt.strip():
                all_formats.add(fmt.strip())

    context = {
        "movies": movies.distinct(),
        "all_languages": sorted(all_languages),
        "all_genres": sorted(all_genres),
        "all_formats": sorted(all_formats),
        "selected_location": selected_location,
        "selected_languages": selected_languages,
        "selected_genres": selected_genres,
        "selected_formats": selected_formats,
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
            request.user.like_set.filter(review__movie=movie).values_list(
                "review_id", flat=True
            )
        )

    recommended_movies = Movie.objects.exclude(id=movie.id)[:5]

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "shows": shows,
            "reviews": reviews,
            "comments": comments,
            "user_liked_reviews": user_liked_reviews,
            "now": now,
            "recommended_movies": recommended_movies,
        },
    )


def browse_cinemas(request):
    now = timezone.localtime()

    theatres = Theatre.objects.filter(shows__show_time__gt=now).distinct()

    theatre_data = []
    for theatre in theatres:
        active_shows = (
            Show.objects.filter(
                theatre=theatre, show_time__gt=now, available_seats__gt=0
            )
            .select_related("movie")
            .order_by("show_time")
        )

        if active_shows.exists():
            theatre_data.append(
                {
                    "theatre": theatre,
                    "shows": active_shows,
                }
            )

    return render(
        request,
        "movies/browse_cinemas.html",
        {
            "theatre_data": theatre_data,
        },
    )
