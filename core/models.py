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
    
    from django.db import models
from cloudinary.models import CloudinaryField


class Stream(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    image = CloudinaryField("image", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    badge = models.CharField(max_length=100, blank=True, null=True)
    rating_text = models.CharField(max_length=100, blank=True, null=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Play(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=100, blank=True, null=True)
    date_text = models.CharField(max_length=100, blank=True, null=True)
    image = CloudinaryField("image", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class Sport(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=100, blank=True, null=True)
    date_text = models.CharField(max_length=100, blank=True, null=True)
    image = CloudinaryField("image", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class Activity(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=100, blank=True, null=True)
    date_text = models.CharField(max_length=100, blank=True, null=True)
    image = CloudinaryField("image", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    promoted = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class League(models.Model):
    title = models.CharField(max_length=255)
    sport = models.CharField(max_length=100, default="Cricket")
    season_text = models.CharField(max_length=255, blank=True, null=True)
    interest_text = models.CharField(max_length=100, blank=True, null=True)
    image = CloudinaryField("image", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class Team(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)
    logo = CloudinaryField("image", blank=True, null=True)

    def __str__(self):
        return self.name


class LeagueEvent(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="events")
    match_number = models.CharField(max_length=100, blank=True, null=True)
    date_heading = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    team_one = models.CharField(max_length=255)
    team_two = models.CharField(max_length=255)
    team_one_logo = CloudinaryField("image", blank=True, null=True)
    team_two_logo = CloudinaryField("image", blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, null=True)
    time_text = models.CharField(max_length=100, blank=True, null=True)
    booking_text = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.team_one} vs {self.team_two}"