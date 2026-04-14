from django.shortcuts import render

from movies.models import Movie


# Create your views here.
def home(request):
    query = request.GET.get("q")
    movies = Movie.objects.all()

    if query:
        movies = movies.filter(title__icontains=query)

    return render(request, "home.html", {"movies": movies})
