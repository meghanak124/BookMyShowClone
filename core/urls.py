from django.urls import path
from .views import (
    home,
    events_page,
    concerts_page,
    matches_page,
    list_your_show,
    event_detail,
    concert_detail,
    match_detail,
)

urlpatterns = [
    path("", home, name="home"),
    path("events/", events_page, name="events_page"),
    path("events/<int:event_id>/", event_detail, name="event_detail"),
    path("concerts/", concerts_page, name="concerts_page"),
    path("concerts/<int:concert_id>/", concert_detail, name="concert_detail"),
    path("matches/", matches_page, name="matches_page"),
    path("matches/<int:match_id>/", match_detail, name="match_detail"),
    path("list-your-show/", list_your_show, name="list_your_show"),
]