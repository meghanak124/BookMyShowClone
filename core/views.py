from django.shortcuts import render
from movies.models import Movie
from .models import Event, Concert, Match
from django.shortcuts import render, get_object_or_404

def home(request):
    city_list = [
        "Bengaluru",
        "Hyderabad",
        "Chennai",
        "Mumbai",
        "Delhi",
        "Kolkata",
        "Pune",
        "Ahmedabad",
        "Kochi",
        "Chandigarh",
    ]

    selected_location = request.GET.get("location", "Bengaluru")

    movies = Movie.objects.all()[:10]
    events = Event.objects.filter(location__icontains=selected_location)[:10]
    concerts = Concert.objects.filter(location__icontains=selected_location)[:10]
    matches = Match.objects.filter(location__icontains=selected_location)[:10]

    hero_images = [
        "images/hero/offer1.png",
        "images/hero/offer2.jpeg",
        "images/hero/offer3.jpg",
    ]

    return render(request, "home.html", {
        "movies": movies,
        "events": events,
        "concerts": concerts,
        "matches": matches,
        "hero_images": hero_images,
        "locations": city_list,
        "selected_location": selected_location,
    })


def events_page(request):
    selected_location = request.GET.get("location", "")
    items = Event.objects.all().order_by("date")
    suggestions = Event.objects.exclude(id__in=items.values_list("id", flat=True))[:5]
    selected_languages = request.GET.getlist("language")
    selected_categories = request.GET.getlist("category")

    if selected_location:
        items = items.filter(location__icontains=selected_location)

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
            item_categories = item.category.split()
            if any(cat in item_categories for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    language_set = set()
    for value in Event.objects.values_list("language", flat=True):
        if value:
            for lang in value.split():
                language_set.add(lang.strip())

    category_set = set()
    for value in Event.objects.values_list("category", flat=True):
        if value:
            for category in value.split():
                category_set.add(category.strip())

    location_set = set(Event.objects.values_list("location", flat=True))

    return render(request, "core/events.html", {
        "title": "Events",
        "items": items.distinct(),
        "all_languages": sorted(language_set),
        "all_categories": sorted(category_set),
        "all_locations": sorted(location_set),
        "selected_languages": selected_languages,
        "selected_categories": selected_categories,
        "selected_location": selected_location,
    })


def concerts_page(request):
    items = Concert.objects.all().order_by("date")
    suggestions = Concert.objects.exclude(id__in=items.values_list("id", flat=True))[:5]
    selected_languages = request.GET.getlist("language")
    selected_categories = request.GET.getlist("genre")

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
            item_genres = item.genre.split()
            if any(cat in item_genres for cat in selected_categories):
                filtered_ids.append(item.id)
        items = items.filter(id__in=filtered_ids)

    language_set = set()
    for value in Concert.objects.values_list("language", flat=True):
        if value:
            for lang in value.split():
                language_set.add(lang.strip())

    genre_set = set()
    for value in Concert.objects.values_list("genre", flat=True):
        if value:
            for genre in value.split():
                genre_set.add(genre.strip())

    return render(request, "core/concerts.html", {
        "title": "Concerts",
        "items": items.distinct(),
        "all_languages": sorted(language_set),
        "all_categories": sorted(genre_set),
        "selected_languages": selected_languages,
        "selected_categories": selected_categories,
    })


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

    return render(request, "core/event_detail.html", {
        "item": item,
        "suggestions": suggestions,
    })


def concert_detail(request, concert_id):
    item = get_object_or_404(Concert, id=concert_id)
    suggestions = Concert.objects.exclude(id=item.id)[:5]

    return render(request, "core/concert_detail.html", {
        "item": item,
        "suggestions": suggestions,
    })


def match_detail(request, match_id):
    item = get_object_or_404(Match, id=match_id)
    suggestions = Match.objects.exclude(id=item.id)[:5]

    return render(request, "core/match_detail.html", {
        "item": item,
        "suggestions": suggestions,
    })