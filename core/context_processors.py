from movies.models import Theatre
from .models import Event

DEFAULT_CITY = "Hyderabad"

POPULAR_CITIES = [
    "Mumbai",
    "Delhi-NCR",
    "Bengaluru",
    "Hyderabad",
    "Chandigarh",
    "Ahmedabad",
    "Pune",
    "Chennai",
    "Kolkata",
    "Kochi",
]


def global_locations(request):
    theatre_locations = Theatre.objects.exclude(location__isnull=True).exclude(location__exact="").values_list("location", flat=True)
    event_locations = Event.objects.exclude(location__isnull=True).exclude(location__exact="").values_list("location", flat=True)

    available_cities = sorted(set(theatre_locations) | set(event_locations))

    selected_location = request.GET.get("location", "").strip()

    if selected_location:
        request.session["selected_location"] = selected_location
    else:
        selected_location = request.session.get("selected_location", DEFAULT_CITY)

    return {
        "popular_cities": POPULAR_CITIES,
        "available_cities": available_cities,
        "selected_location": selected_location,
    }