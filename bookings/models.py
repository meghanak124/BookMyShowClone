from django.contrib.auth.models import User
from django.db import models

from movies.models import Show


class Booking(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("watched", "Watched"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="bookings")
    seats_booked = models.PositiveIntegerField()
    booking_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    selected_seats = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f"{self.user.username} - {self.show}"
