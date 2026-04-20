from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("movies/", include("movies.urls")),
    path("accounts/", include("accounts.urls")),
    path("bookings/", include("bookings.urls")),
    path("reviews/", include("reviews.urls")),
]