from django.urls import path
from .views import home, events_page, concerts_page, matches_page, list_your_show

urlpatterns = [
    path("", home, name="home"),
    path("events/", events_page, name="events_page"),
    path("concerts/", concerts_page, name="concerts_page"),
    path("matches/", matches_page, name="matches_page"),
    path("list-your-show/", list_your_show, name="list_your_show"),
]