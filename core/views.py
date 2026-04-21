from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from movies.models import Movie, Show
from .models import Event, Match, Stream, Play, Sport, Activity, League, LeagueEvent

def get_selected_location(request):
    selected_location = request.GET.get("location", "").strip()
    if selected_location:
        request.session["selected_location"] = selected_location
    else:
        selected_location = request.session.get("selected_location", "Hyderabad")
    return selected_location


def normalize_comma_separated_text(value):
    """
    Cleans strings like:
    'Telugu,Hindi,Malayalam'
    'Telugu / Hindi / Tamil'
    'Telugu|Hindi'
    and removes duplicates while keeping order.
    """
    if not value:
        return []

    separators_normalized = (
        str(value)
        .replace("/", ",")
        .replace("|", ",")
        .replace(" ,", ",")
        .replace(", ", ",")
    )

    raw_parts = separators_normalized.split(",")
    cleaned_parts = []

    for part in raw_parts:
        item = part.strip()
        if item and item not in cleaned_parts:
            cleaned_parts.append(item)

    return cleaned_parts


def format_movie_languages(movie):
    """
    Returns clean language text for movie cards/list pages.
    Example:
    ['Telugu', 'Hindi', 'Malayalam'] -> 'Telugu, Hindi, Malayalam'
    """
    languages = normalize_comma_separated_text(getattr(movie, "language", ""))
    return ", ".join(languages)


def format_movie_genres(movie):
    genres = normalize_comma_separated_text(getattr(movie, "genre", ""))
    return ", ".join(genres)


def build_uniform_card(item, image_field="image", fallback_image="/static/images/default-event.jpg", detail_url="#", subtitle=""):
    image_obj = getattr(item, image_field, None)

    return {
        "id": item.id,
        "title": getattr(item, "title", ""),
        "image": image_obj.url if image_obj else fallback_image,
        "subtitle": subtitle,
        "url": detail_url,
    }


def get_available_locations():
    """
    Fetch locations dynamically from DB.
    No hardcoding.
    """
    show_locations = list(
        Show.objects.exclude(theatre__location__isnull=True)
        .exclude(theatre__location__exact="")
        .values_list("theatre__location", flat=True)
        .distinct()
    )

    event_locations = list(
        Event.objects.exclude(location__isnull=True)
        .exclude(location__exact="")
        .values_list("location", flat=True)
        .distinct()
    )

    match_locations = list(
        Match.objects.exclude(location__isnull=True)
        .exclude(location__exact="")
        .values_list("location", flat=True)
        .distinct()
    )

    all_locations = []
    for loc in show_locations + event_locations + match_locations:
        cleaned = str(loc).strip()
        if cleaned and cleaned not in all_locations:
            all_locations.append(cleaned)

    return all_locations


def get_popular_locations():
    """
    Popular locations = the locations which actually have movies/shows.
    Still dynamic, not hardcoded.
    """
    locations = list(
        Show.objects.exclude(theatre__location__isnull=True)
        .exclude(theatre__location__exact="")
        .values_list("theatre__location", flat=True)
        .distinct()
    )

    cleaned_locations = []
    for loc in locations:
        loc = str(loc).strip()
        if loc and loc not in cleaned_locations:
            cleaned_locations.append(loc)

    return cleaned_locations[:10]

def home(request):
    selected_location = get_selected_location(request)

    city_query = request.GET.get("city_query", "").strip()

    all_locations = get_available_locations()
    popular_locations = get_popular_locations()

    searched_locations = []
    if city_query:
        searched_locations = [
            location for location in all_locations
            if city_query.lower() in location.lower()
        ]

    hero_slides = [
        {"image": "/static/images/hero/offer1.png", "link": "#"},
        {"image": "/static/images/hero/offer2.jpeg", "link": "#"},
        {"image": "/static/images/hero/offer3.jpg", "link": "#"},
    ]

    movie_ids_in_city = Show.objects.filter(
        theatre__location__icontains=selected_location
    ).values_list("movie_id", flat=True).distinct()

    movies = Movie.objects.filter(id__in=movie_ids_in_city)[:12]
    premiere_movies = Movie.objects.filter(is_premiere=True)[:12]
    events = Event.objects.filter(location__icontains=selected_location)[:12]
    matches = Match.objects.filter(location__icontains=selected_location)[:12]

    movie_cards = []
    for movie in movies:
        genre_text = format_movie_genres(movie)

        movie_cards.append(
            build_uniform_card(
                item=movie,
                image_field="poster",
                fallback_image="/static/images/default-poster.jpg",
                detail_url=f"/movies/{movie.id}/",
                subtitle=genre_text if genre_text else "Entertainment",
            )
        )

    premiere_cards = []
    for movie in premiere_movies:
        genre_text = format_movie_genres(movie)

        premiere_cards.append(
            build_uniform_card(
                item=movie,
                image_field="poster",
                fallback_image="/static/images/default-poster.jpg",
                detail_url=f"/movies/{movie.id}/",
                subtitle=genre_text if genre_text else "Entertainment",
            )
        )

    event_cards = []
    for event in events:
        category_text = ", ".join(normalize_comma_separated_text(getattr(event, "category", "")))
        subtitle = category_text if category_text else getattr(event, "location", "")

        event_cards.append(
            build_uniform_card(
                item=event,
                image_field="image",
                fallback_image="/static/images/default-event.jpg",
                detail_url=f"/events/{event.id}/",
                subtitle=subtitle,
            )
        )

    match_cards = []
    for match in matches:
        sport_text = ", ".join(normalize_comma_separated_text(getattr(match, "sport", "")))
        subtitle = sport_text if sport_text else getattr(match, "location", "")

        match_cards.append(
            build_uniform_card(
                item=match,
                image_field="image",
                fallback_image="/static/images/default-event.jpg",
                detail_url=f"/matches/{match.id}/",
                subtitle=subtitle,
            )
        )

    context = {
        "selected_location": selected_location,
        "hero_slides": hero_slides,
        "movie_cards": movie_cards,
        "premiere_cards": premiere_cards,
        "event_cards": event_cards,
        "match_cards": match_cards,
        "city_query": city_query,
        "searched_locations": searched_locations,
        "popular_locations": popular_locations,
    }
    return render(request, "home.html", context)


def events_page(request):
    items = Event.objects.all()

    selected_location = request.GET.get("location", "").strip()
    if selected_location:
        request.session["selected_location"] = selected_location
    else:
        selected_location = request.session.get("selected_location", "Hyderabad")

    selected_categories = request.GET.getlist("category")
    selected_languages = request.GET.getlist("language")

    if selected_location:
        items = items.filter(location__icontains=selected_location)

    if selected_categories:
        filtered_ids = []
        for item in items:
            categories = [c.strip() for c in item.category.split(",")]
            if any(cat in categories for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    if selected_languages:
        filtered_ids = []
        for item in items:
            langs = [l.strip() for l in item.language.split(",")] if item.language else []
            if any(lang in langs for lang in selected_languages):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    all_categories = set()
    all_languages = set()

    for item in Event.objects.all():
        for cat in item.category.split(","):
            if cat.strip():
                all_categories.add(cat.strip())

        if item.language:
            for lang in item.language.split(","):
                if lang.strip():
                    all_languages.add(lang.strip())

    context = {
        "items": items.distinct(),
        "all_categories": sorted(all_categories),
        "all_languages": sorted(all_languages),
        "selected_categories": selected_categories,
        "selected_languages": selected_languages,
        "selected_location": selected_location,
    }
    return render(request, "core/events.html", context)

def matches_page(request):
    items = Match.objects.all().order_by("date")
    suggestions = Match.objects.exclude(id__in=items.values_list("id", flat=True))[:5]
    selected_languages = request.GET.getlist("language")
    selected_categories = request.GET.getlist("sport")

    if selected_languages:
        filtered_ids = []
        for item in items:
            item_languages = item.language.split()
            if any(lang in item_languages for lang in selected_languages):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    if selected_categories:
        filtered_ids = []
        for item in items:
            item_sports = item.sport.split()
            if any(cat in item_sports for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    language_set = set()
    for value in Match.objects.values_list("language", flat=True):
        if value:
            for lang in value.split():
                language_set.add(lang.strip())

    sport_set = set()
    for value in Match.objects.values_list("sport", flat=True):
        if value:
            for sport in value.split():
                sport_set.add(sport.strip())

    return render(request, "core/matches.html", {
        "title": "Matches",
        "items": items.distinct(),
        "all_languages": sorted(language_set),
        "all_categories": sorted(sport_set),
        "selected_languages": selected_languages,
        "selected_categories": selected_categories,
    })


def list_your_show(request):
    return render(request, "core/list_your_show.html")


def event_detail(request, event_id):
    item = get_object_or_404(Event, id=event_id)
    suggestions = Event.objects.exclude(id=item.id)[:5]
    filtered_item_ids = items.values_list("id", flat=True)
    suggestions = Event.objects.exclude(id__in=filtered_item_ids).distinct()[:5]
    return render(request, "core/event_detail.html", {
        "item": item,
        "suggestions": suggestions,
    })


def concert_detail(request, concert_id):
    item = get_object_or_404(Concert, id=concert_id)
    suggestions = Concert.objects.exclude(id=item.id)[:5]
    filtered_item_ids = items.values_list("id", flat=True)
    suggestions = Concert.objects.exclude(id__in=filtered_item_ids).distinct()[:5]
    return render(request, "core/concert_detail.html", {
        "item": item,
        "suggestions": suggestions,
    })


def match_detail(request, match_id):
    item = get_object_or_404(Match, id=match_id)
    suggestions = Match.objects.exclude(id=item.id)[:5]
    filtered_item_ids = items.values_list("id", flat=True)
    suggestions = Match.objects.exclude(id__in=filtered_item_ids).distinct()[:5]
    return render(request, "core/match_detail.html", {
        "item": item,
        "suggestions": suggestions,
    })

from django.shortcuts import render, get_object_or_404
from .models import Event, Stream, Play, Sport, Activity, League, LeagueEvent

def get_selected_location(request):
    selected_location = request.GET.get("location", "").strip()
    if selected_location:
        request.session["selected_location"] = selected_location
    else:
        selected_location = request.session.get("selected_location", "Hyderabad")
    return selected_location


def streams_page(request):
    items = Stream.objects.all()
    return render(request, "core/streams.html", {"items": items})


def stream_detail(request, pk):
    item = get_object_or_404(Stream, pk=pk)
    return render(request, "core/stream_detail.html", {"item": item})


def plays_page(request):
    selected_location = get_selected_location(request)
    items = Play.objects.filter(location__icontains=selected_location)

    selected_categories = request.GET.getlist("category")
    selected_languages = request.GET.getlist("language")

    if selected_categories:
        filtered_ids = []
        for item in items:
            categories = [c.strip() for c in (item.category or "").split(",") if c.strip()]
            if any(cat in categories for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    if selected_languages:
        filtered_ids = []
        for item in items:
            langs = [l.strip() for l in (item.language or "").split(",") if l.strip()]
            if any(lang in langs for lang in selected_languages):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    all_categories = set()
    all_languages = set()

    for item in Play.objects.all():
        for cat in (item.category or "").split(","):
            if cat.strip():
                all_categories.add(cat.strip())
        for lang in (item.language or "").split(","):
            if lang.strip():
                all_languages.add(lang.strip())

    return render(request, "core/plays.html", {
        "items": items,
        "selected_location": selected_location,
        "selected_categories": selected_categories,
        "selected_languages": selected_languages,
        "all_categories": sorted(all_categories),
        "all_languages": sorted(all_languages),
    })


def play_detail(request, pk):
    item = get_object_or_404(Play, pk=pk)
    return render(request, "core/play_detail.html", {"item": item})


def sports_page(request):
    selected_location = get_selected_location(request)
    items = Sport.objects.filter(location__icontains=selected_location)

    selected_categories = request.GET.getlist("category")

    if selected_categories:
        filtered_ids = []
        for item in items:
            categories = [c.strip() for c in (item.category or "").split(",") if c.strip()]
            if any(cat in categories for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    all_categories = set()
    for item in Sport.objects.all():
        for cat in (item.category or "").split(","):
            if cat.strip():
                all_categories.add(cat.strip())

    return render(request, "core/sports.html", {
        "items": items,
        "selected_location": selected_location,
        "selected_categories": selected_categories,
        "all_categories": sorted(all_categories),
    })


def sport_detail(request, pk):
    item = get_object_or_404(Sport, pk=pk)
    return render(request, "core/sport_detail.html", {"item": item})


def activities_page(request):
    selected_location = get_selected_location(request)
    items = Activity.objects.filter(location__icontains=selected_location)

    selected_categories = request.GET.getlist("category")

    if selected_categories:
        filtered_ids = []
        for item in items:
            categories = [c.strip() for c in (item.category or "").split(",") if c.strip()]
            if any(cat in categories for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    all_categories = set()
    for item in Activity.objects.all():
        for cat in (item.category or "").split(","):
            if cat.strip():
                all_categories.add(cat.strip())

    return render(request, "core/activities.html", {
        "items": items,
        "selected_location": selected_location,
        "selected_categories": selected_categories,
        "all_categories": sorted(all_categories),
    })


def activity_detail(request, pk):
    item = get_object_or_404(Activity, pk=pk)
    return render(request, "core/activity_detail.html", {"item": item})


def ipl_page(request):
    league = League.objects.first()
    events = LeagueEvent.objects.filter(league=league)
    teams = league.teams.all() if league else []

    return render(request, "core/ipl.html", {
        "league": league,
        "events": events,
        "teams": teams,
    })