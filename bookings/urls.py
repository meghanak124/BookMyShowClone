from django.urls import path
from .views import book_show, delete_booking, my_bookings
urlpatterns = [
    path("book/<int:show_id>/", book_show, name="book_show"),
    path("my-bookings/", my_bookings, name="my_bookings"),
    path("delete/<int:booking_id>/", delete_booking, name="delete_booking"),
]