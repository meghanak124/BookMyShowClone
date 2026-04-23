"""
Fetches general events in India from the Ticketmaster Discovery API
and populates the Event model. Covers arts, theatre, sports, family,
comedy, food — everything except music (that's fetch_concerts).

Usage:
    python manage.py fetch_events
    python manage.py fetch_events --city Mumbai
    python manage.py fetch_events --city Hyderabad --pages 2
    python manage.py fetch_events --category "Arts & Theatre"

Get a FREE API key at: https://developer.ticketmaster.com/
  → Sign up → My Apps → Create App → copy "Consumer Key"
Add to .env:  TICKETMASTER_KEY=your_key_here
"""

import io
import os

import cloudinary.uploader
import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from core.models import Event


TICKETMASTER_BASE = "https://app.ticketmaster.com/discovery/v2"

INDIA_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad",
    "Chennai", "Kolkata", "Pune", "Ahmedabad",
]

# Categories to fetch (Ticketmaster classificationNames)
# Excludes "music" — that's handled by fetch_concerts
DEFAULT_CATEGORIES = [
    "Arts & Theatre",
    "Sports",
    "Family",
    "Film",
    "Miscellaneous",
]


class Command(BaseCommand):
    help = "Fetch general events (arts, sports, family etc.) in India from Ticketmaster → Event model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--city",
            type=str,
            default=None,
            help="City to search (default: all major Indian cities)",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=1,
            help="Pages per city per category (default: 1)",
        )
        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help=(
                "Ticketmaster classification name to fetch "
                "(default: Arts & Theatre, Sports, Family, Film, Miscellaneous)"
            ),
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("TICKETMASTER_KEY")
        if not api_key:
            raise CommandError(
                "\n\n  ❌  TICKETMASTER_KEY is not set in your .env file.\n"
                "  Get a free key at: https://developer.ticketmaster.com/\n"
                "  Then add:  TICKETMASTER_KEY=your_key_here\n"
            )

        cities = [options["city"]] if options["city"] else INDIA_CITIES
        categories = [options["category"]] if options["category"] else DEFAULT_CATEGORIES
        total_pages = options["pages"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n🎪  Fetching events from Ticketmaster\n"
                f"    Cities: {', '.join(cities)}\n"
                f"    Categories: {', '.join(categories)}\n"
            )
        )

        created_count = 0
        skipped_count = 0
        error_count = 0

        for city in cities:
            for category in categories:
                self.stdout.write(f"\n  📍 {city} — {category}")
                for page in range(total_pages):
                    try:
                        events = self._fetch_events(api_key, city, category, page)
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"    API error: {e}"))
                        continue

                    for ev in events:
                        try:
                            result = self._save_event(ev, city, category)
                            if result == "created":
                                created_count += 1
                            else:
                                skipped_count += 1
                        except Exception as e:
                            title = ev.get("name", "unknown")
                            self.stderr.write(self.style.ERROR(f"    ❌  '{title}': {e}"))
                            error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✨  Done! Created: {created_count} | Skipped: {skipped_count} | Errors: {error_count}\n"
            )
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _fetch_events(self, api_key, city, category, page):
        params = {
            "apikey": api_key,
            "classificationName": category,
            "city": city,
            "countryCode": "IN",
            "page": page,
            "size": 20,
            "sort": "date,asc",
        }
        resp = requests.get(f"{TICKETMASTER_BASE}/events.json", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("_embedded", {}).get("events", [])

    def _save_event(self, ev, city, category_label):
        title = ev.get("name", "").strip()
        if not title:
            return "skipped"

        if Event.objects.filter(title__iexact=title, location__icontains=city).exists():
            self.stdout.write(f"    ⏭  Skipping (exists): {title}")
            return "skipped"

        # Sub-genre for more precise category label
        classifications = ev.get("classifications", [{}])
        genre = (classifications[0].get("genre", {}) or {}).get("name", "") if classifications else ""
        sub_genre = (classifications[0].get("subGenre", {}) or {}).get("name", "") if classifications else ""
        category = sub_genre or genre or category_label

        # Venue + location
        venues = ev.get("_embedded", {}).get("venues", [{}])
        venue_name = venues[0].get("name", city) if venues else city
        location = f"{venue_name}, {city}"

        # Date
        dates = ev.get("dates", {})
        start = dates.get("start", {})
        date_str = start.get("dateTime") or (start.get("localDate", "") + "T18:00:00+05:30")
        try:
            date = parse_datetime(date_str) or timezone.now()
        except Exception:
            date = timezone.now()

        # Description
        info = ev.get("info") or ev.get("pleaseNote") or ""
        description = info if info else f"{title} — {category} event in {city}."

        # Image → Cloudinary
        image_cloudinary = self._upload_image(ev, title)

        event = Event(
            title=title,
            category=category,
            location=location,
            language="English",
            date=date,
            description=description,
        )
        if image_cloudinary:
            event.image = image_cloudinary
        event.save()

        self.stdout.write(self.style.SUCCESS(f"    ✅  {title} — {location}"))
        return "created"

    def _upload_image(self, ev, title):
        images = ev.get("images", [])
        if not images:
            return None
        best = max(images, key=lambda img: img.get("width", 0) * img.get("height", 0))
        img_url = best.get("url")
        if not img_url:
            return None
        try:
            resp = requests.get(img_url, timeout=15)
            resp.raise_for_status()
            result = cloudinary.uploader.upload(
                io.BytesIO(resp.content),
                folder="event_images",
                public_id=f"tm_{ev.get('id', title[:20])}",
                overwrite=False,
                resource_type="image",
            )
            return result.get("public_id")
        except Exception as e:
            self.stderr.write(f"      ⚠  Image upload failed for '{title}': {e}")
            return None
