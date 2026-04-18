from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from movies.models import Movie


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


def home(request):
    movies = Movie.objects.all()[:8]

    context = {
        "movies": movies,
    }
    return render(request, "home.html", context)
