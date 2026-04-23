"""
Fetches music concerts & events in India from Eventbrite API
and saves them to the Event model.

Eventbrite actually has Indian events unlike Ticketmaster.

Usage:
    python manage.py fetch_concerts
    python manage.py fetch_concerts --city Mumbai
    python manage.py fetch_concerts --pages 5

Get a FREE token at: https://www.eventbrite.com/platform/api
  → Sign in → Account Settings → Developer Links → API Keys
  → Create API Key → copy the "Private Token"
Add to .env:  EVENTBRITE_TOKEN=your_token_here
"""

import io
import os

import cloudinary.uploader
import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from core.models import Event

EVENTBRITE_BASE = "https://www.eventbriteapi.com/v3"

# Indian cities with their Eventbrite location search terms
INDIA_CITIES = [
    "Mumbai, India",
    "Delhi, India",
    "Bengaluru, India",
    "Hyderabad, India",
    "Chennai, India",
    "Kolkata, India",
    "Pune, India",
    "Ahmedabad, India",
]

# Eventbrite music category ID = 103
# Arts = 105, Film = 104, Food = 110, Sports = 108
CATEGORY_MAP = {
    "103": "Music",
    "105": "Arts & Theatre",
    "104": "Film",
    "108": "Sports & Fitness",
    "110": "Food & Drink",
    "113": "Community",
    "101": "Business",
    "102": "Science & Technology",
}


class Command(BaseCommand):
    help = "Fetch concerts & events in India from Eventbrite → Event model"

    def add_arguments(self, parser):
        parser.add_argument("--city", type=str, default=None,
                            help="City to search (default: all major Indian cities)")
        parser.add_argument("--pages", type=int, default=3,
                            help="Pages to fetch per city (default: 3, ~50 events per page)")
        parser.add_argument("--category", type=str, default="103",
                            help="Eventbrite category ID (103=Music, 105=Arts, 108=Sports). Default: 103")

    def handle(self, *args, **options):
        token = os.environ.get("EVENTBRITE_TOKEN")
        if not token:
            raise CommandError(
                "\n\n  ❌  EVENTBRITE_TOKEN is not set in your .env file.\n"
                "  Get a free token at: https://www.eventbrite.com/platform/api\n"
                "  → Sign in → Account Settings → Developer Links → API Keys\n"
                "  Then add:  EVENTBRITE_TOKEN=your_private_token_here\n"
            )

        cities = [options["city"] + ", India"] if options["city"] else INDIA_CITIES
        total_pages = options["pages"]
        category_id = options["category"]
        category_name = CATEGORY_MAP.get(category_id, "Event")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n🎵  Fetching '{category_name}' events from Eventbrite\n"
            f"    Cities: {', '.join(c.split(',')[0] for c in cities)}\n"
        ))

        headers = {"Authorization": f"Bearer {token}"}
        created_count = 0
        skipped_count = 0
        error_count = 0

        for city in cities:
            city_short = city.split(",")[0]
            self.stdout.write(f"\n  📍 {city_short}")

            for page in range(1, total_pages + 1):
                try:
                    results, has_more = self._fetch_page(headers, city, category_id, page)
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"    API error: {e}"))
                    break

                for ev in results:
                    try:
                        result = self._save_event(ev, city_short, category_name)
                        if result == "created":
                            created_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        name = ev.get("name", {}).get("text", "unknown")
                        self.stderr.write(self.style.ERROR(f"    ❌  '{name}': {e}"))
                        error_count += 1

                if not has_more:
                    break

        self.stdout.write(self.style.SUCCESS(
            f"\n✨  Done! Created: {created_count} | Skipped: {skipped_count} | Errors: {error_count}\n"
        ))

    def _fetch_page(self, headers, city, category_id, page):
        params = {
            "location.address": city,
            "location.within": "50km",
            "categories": category_id,
            "expand": "venue",
            "sort_by": "date",
            "page": page,
        }
        resp = requests.get(f"{EVENTBRITE_BASE}/events/search/", headers=headers,
                            params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        has_more = data.get("pagination", {}).get("has_more_items", False)
        return events, has_more

    def _save_event(self, ev, city, category_name):
        title = (ev.get("name") or {}).get("text", "").strip()
        if not title:
            return "skipped"

        if Event.objects.filter(title__iexact=title, location__icontains=city).exists():
            self.stdout.write(f"    ⏭  Skipping (exists): {title}")
            return "skipped"

        # Description
        description = (ev.get("description") or {}).get("text", "") or \
                      (ev.get("summary") or f"{title} — event in {city}.")

        # Venue / location
        venue = ev.get("venue") or {}
        venue_name = venue.get("name", "")
        address = (venue.get("address") or {}).get("localized_address_display", city)
        location = f"{venue_name}, {city}" if venue_name else address or city

        # Date
        start = ev.get("start", {})
        date_str = start.get("utc") or start.get("local", "")
        try:
            date = parse_datetime(date_str) if date_str else timezone.now()
            if date and timezone.is_naive(date):
                date = timezone.make_aware(date)
        except Exception:
            date = timezone.now()

        # Category
        category_ids = [c.get("id") for c in (ev.get("category", []) or [])]
        category = CATEGORY_MAP.get(str(category_ids[0]), category_name) if category_ids else category_name

        # Image
        image_cloudinary = self._upload_image(ev, title)

        event = Event(
            title=title,
            category=category,
            location=location,
            language="English",
            date=date,
            description=description[:1000],
        )
        if image_cloudinary:
            event.image = image_cloudinary
        event.save()

        self.stdout.write(self.style.SUCCESS(f"    ✅  {title} — {location}"))
        return "created"

    def _upload_image(self, ev, title):
        logo = ev.get("logo")
        if not logo:
            return None
        img_url = (logo.get("original") or {}).get("url") or logo.get("url")
        if not img_url:
            return None
        try:
            resp = requests.get(img_url, timeout=15)
            resp.raise_for_status()
            result = cloudinary.uploader.upload(
                io.BytesIO(resp.content),
                folder="concert_images",
                public_id=f"eb_{ev.get('id', title[:20])}",
                overwrite=False,
                resource_type="image",
            )
            return result.get("public_id")
        except Exception as e:
            self.stderr.write(f"      ⚠  Image upload failed for '{title}': {e}")
            return None
