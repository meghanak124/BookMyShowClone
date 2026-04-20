from cloudinary.models import CloudinaryField
from django.db import models


class HeroBanner(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    image = CloudinaryField("hero")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"


class Event(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    language = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    image = CloudinaryField("event_image", blank=True, null=True)

    def __str__(self):
        return self.title


class Concert(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    language = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    image = CloudinaryField("concert_image", blank=True, null=True)

    def __str__(self):
        return self.title


class Match(models.Model):
    title = models.CharField(max_length=200)
    sport = models.CharField(max_length=100)
    teams = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    language = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    image = CloudinaryField("match_image", blank=True, null=True)

    def __str__(self):
        return self.title