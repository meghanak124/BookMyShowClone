from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("events/", views.events_page, name="events"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("plays/", views.plays_page, name="plays_page"),
    path("sports/", views.sports_page, name="sports_page"),
    path("activities/", views.activities_page, name="activities_page"),
    path("stream/", views.streams_page, name="streams_page"),
    path("ipl/", views.ipl_page, name="ipl_page"),

    path("plays/<int:pk>/", views.play_detail, name="play_detail"),
    path("sports/<int:pk>/", views.sport_detail, name="sport_detail"),
    path("activities/<int:pk>/", views.activity_detail, name="activity_detail"),
    path("stream/<int:pk>/", views.stream_detail, name="stream_detail"),
    path("matches/", views.matches_page, name="matches_page"),
    path("matches/<int:match_id>/", views.match_detail, name="match_detail"),
    path("list-your-show/", views.list_your_show, name="list_your_show"),
]