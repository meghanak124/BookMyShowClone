"""
Fetches music concerts in India from the Ticketmaster Discovery API
and populates the Event model (category = "Music" or "Concerts").

Usage:
    python manage.py fetch_concerts
    python manage.py fetch_concerts --city Mumbai
    python manage.py fetch_concerts --city Bengaluru --pages 2

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

# Indian cities Ticketmaster recognises
INDIA_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad",
    "Chennai", "Kolkata", "Pune", "Ahmedabad",
]


class Command(BaseCommand):
    help = "Fetch music concerts in India from Ticketmaster and save to Event model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--city",
            type=str,
            default=None,
            help="City to search concerts in (default: all major Indian cities)",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=1,
            help="Pages to fetch per city (default: 1, ~20 events per page)",
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
        total_pages = options["pages"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"\n🎵  Fetching concerts from Ticketmaster for: {', '.join(cities)}\n")
        )

        created_count = 0
        skipped_count = 0
        error_count = 0

        for city in cities:
            self.stdout.write(f"\n  📍 City: {city}")
            for page in range(total_pages):
                try:
                    events = self._fetch_events(api_key, city, page)
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"    API error: {e}"))
                    continue

                for ev in events:
                    try:
                        result = self._save_event(ev, city)
                        if result == "created":
                            created_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        title = ev.get("name", "unknown")
                        self.stderr.write(self.style.ERROR(f"    ❌  Error saving '{title}': {e}"))
                        error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✨  Done! Created: {created_count} | Skipped: {skipped_count} | Errors: {error_count}\n"
            )
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _fetch_events(self, api_key, city, page):
        """Fetch one page of music events for a city from Ticketmaster."""
        params = {
            "apikey": api_key,
            "classificationName": "music",
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

    def _save_event(self, ev, city):
        """Parse a Ticketmaster event dict and create an Event record. Returns 'created'/'skipped'."""
        title = ev.get("name", "").strip()
        if not title:
            return "skipped"

        # Skip duplicates by title + city
        if Event.objects.filter(title__iexact=title, location__icontains=city).exists():
            self.stdout.write(f"    ⏭  Skipping (exists): {title}")
            return "skipped"

        # Category
        classifications = ev.get("classifications", [{}])
        genre = classifications[0].get("genre", {}).get("name", "") if classifications else ""
        category = genre if genre and genre != "Undefined" else "Music"

        # Location: venue name + city
        venues = ev.get("_embedded", {}).get("venues", [{}])
        venue_name = venues[0].get("name", city) if venues else city
        location = f"{venue_name}, {city}"

        # Date
        dates = ev.get("dates", {})
        start = dates.get("start", {})
        date_str = start.get("dateTime") or (start.get("localDate", "") + "T19:00:00+05:30")
        try:
            date = parse_datetime(date_str) or timezone.now()
        except Exception:
            date = timezone.now()

        # Description
        info = ev.get("info") or ev.get("pleaseNote") or ""
        description = info if info else f"{title} — live concert in {city}."

        # Language (Ticketmaster doesn't give this; default to English)
        language = "English"

        # Image: pick the largest available image
        image_cloudinary = self._upload_image(ev, title)

        event = Event(
            title=title,
            category=category,
            location=location,
            language=language,
            date=date,
            description=description,
        )
        if image_cloudinary:
            event.image = image_cloudinary
        event.save()

        self.stdout.write(self.style.SUCCESS(f"    ✅  {title} — {location}"))
        return "created"

    def _upload_image(self, ev, title):
        """Download event image and upload to Cloudinary. Returns public_id or None."""
        images = ev.get("images", [])
        if not images:
            return None

        # Pick the highest-resolution image
        best = max(images, key=lambda img: img.get("width", 0) * img.get("height", 0))
        img_url = best.get("url")
        if not img_url:
            return None

        try:
            resp = requests.get(img_url, timeout=15)
            resp.raise_for_status()
            result = cloudinary.uploader.upload(
                io.BytesIO(resp.content),
                folder="concert_images",
                public_id=f"tm_{ev.get('id', title[:20])}",
                overwrite=False,
                resource_type="image",
            )
            return result.get("public_id")
        except Exception as e:
            self.stderr.write(f"      ⚠  Image upload failed for '{title}': {e}")
            return None
