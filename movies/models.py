from cloudinary.models import CloudinaryField
from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    duration = models.CharField(max_length=100)
    language = models.CharField(max_length=255)
    format = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.DateField()
    description = models.TextField()
    poster = CloudinaryField("image", blank=True, null=True)
    

    meta_type = models.CharField(
        max_length=20,
        choices=[
            ("like", "Like"),
            ("rating", "Rating"),
        ],
        default="like",
    )
    meta_value = models.CharField(max_length=100, blank=True, null=True)
    card_subtitle = models.CharField(max_length=255, blank=True, null=True)
    is_premiere = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Theatre(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    rows = models.PositiveIntegerField(default=5)
    columns = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.name} - {self.location}"


class Show(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="shows")
    theatre = models.ForeignKey(Theatre, on_delete=models.CASCADE, related_name="shows")
    show_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField(blank=True, null=True)
    available_seats = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.theatre:
            calculated_total = self.theatre.rows * self.theatre.columns

            if not self.total_seats:
                self.total_seats = calculated_total

            if self.available_seats is None:
                self.available_seats = calculated_total

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.movie.title} at {self.theatre.name} on {self.show_time}"
