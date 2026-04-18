from django.shortcuts import render
from movies.models import Movie

def home(request):
    movies = Movie.objects.all()[:10]

    hero_images = [
        "images/hero/offer1.png",
        "images/hero/offer2.jpeg",
        "images/hero/offer3.jpg",
    ]

    return render(request, "home.html", {
        "movies": movies,
        "hero_images": hero_images,
    })


def events_page(request):
    return render(request, "core/events.html")


def concerts_page(request):
    return render(request, "core/concerts.html")


def matches_page(request):
    return render(request, "core/matches.html")


def list_your_show(request):
    return render(request, "core/list_your_show.html")