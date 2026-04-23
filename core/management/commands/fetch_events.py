"""
Fetches general events (arts, sports, food, tech etc.) in India from Eventbrite
and saves to the Event model.

Usage:
    python manage.py fetch_events
    python manage.py fetch_events --city Hyderabad
    python manage.py fetch_events --category 105   # Arts & Theatre
    python manage.py fetch_events --category 108   # Sports

Category IDs:
    103 = Music        105 = Arts & Theatre   104 = Film & Media
    108 = Sports       110 = Food & Drink     113 = Community
    102 = Science/Tech 101 = Business

Add to .env:  EVENTBRITE_TOKEN=your_private_token_here
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

INDIA_CITIES = [
    "Mumbai, India", "Delhi, India", "Bengaluru, India",
    "Hyderabad, India", "Chennai, India", "Kolkata, India",
    "Pune, India", "Ahmedabad, India",
]

CATEGORY_MAP = {
    "103": "Music", "105": "Arts & Theatre", "104": "Film",
    "108": "Sports & Fitness", "110": "Food & Drink",
    "113": "Community", "101": "Business", "102": "Technology",
}

# Fetch these categories by default (skip music — that's fetch_concerts)
DEFAULT_CATEGORIES = ["105", "108", "110", "104", "113"]


class Command(BaseCommand):
    help = "Fetch general events in India from Eventbrite → Event model"

    def add_arguments(self, parser):
        parser.add_argument("--city", type=str, default=None)
        parser.add_argument("--pages", type=int, default=2)
        parser.add_argument("--category", type=str, default=None,
                            help="Single category ID to fetch (default: arts, sports, food, film, community)")

    def handle(self, *args, **options):
        token = os.environ.get("EVENTBRITE_TOKEN")
        if not token:
            raise CommandError(
                "\n\n  ❌  EVENTBRITE_TOKEN is not set.\n"
                "  Get free token at: https://www.eventbrite.com/platform/api\n"
                "  Add to .env:  EVENTBRITE_TOKEN=your_token\n"
            )

        cities = [options["city"] + ", India"] if options["city"] else INDIA_CITIES
        categories = [options["category"]] if options["category"] else DEFAULT_CATEGORIES
        total_pages = options["pages"]
        headers = {"Authorization": f"Bearer {token}"}

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n🎪  Fetching events from Eventbrite\n"
            f"    Cities: {', '.join(c.split(',')[0] for c in cities)}\n"
            f"    Categories: {', '.join(CATEGORY_MAP.get(c, c) for c in categories)}\n"
        ))

        created_count = skipped_count = error_count = 0

        for city in cities:
            city_short = city.split(",")[0]
            for cat_id in categories:
                cat_name = CATEGORY_MAP.get(cat_id, "Event")
                self.stdout.write(f"\n  📍 {city_short} — {cat_name}")
                for page in range(1, total_pages + 1):
                    try:
                        params = {
                            "location.address": city,
                            "location.within": "50km",
                            "categories": cat_id,
                            "expand": "venue",
                            "sort_by": "date",
                            "page": page,
                        }
                        resp = requests.get(f"{EVENTBRITE_BASE}/events/search/",
                                            headers=headers, params=params, timeout=15)
                        resp.raise_for_status()
                        data = resp.json()
                        results = data.get("events", [])
                        has_more = data.get("pagination", {}).get("has_more_items", False)
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"    API error: {e}"))
                        break

                    for ev in results:
                        try:
                            title = (ev.get("name") or {}).get("text", "").strip()
                            if not title:
                                skipped_count += 1
                                continue

                            if Event.objects.filter(title__iexact=title,
                                                    location__icontains=city_short).exists():
                                skipped_count += 1
                                continue

                            venue = ev.get("venue") or {}
                            venue_name = venue.get("name", "")
                            location = f"{venue_name}, {city_short}" if venue_name else city_short

                            start = ev.get("start", {})
                            date_str = start.get("utc") or start.get("local", "")
                            try:
                                date = parse_datetime(date_str) if date_str else timezone.now()
                                if date and timezone.is_naive(date):
                                    date = timezone.make_aware(date)
                            except Exception:
                                date = timezone.now()

                            description = (ev.get("description") or {}).get("text", "") or \
                                          f"{title} — {cat_name} event in {city_short}."

                            image_cloudinary = None
                            logo = ev.get("logo")
                            if logo:
                                img_url = (logo.get("original") or {}).get("url") or logo.get("url")
                                if img_url:
                                    try:
                                        img_resp = requests.get(img_url, timeout=15)
                                        img_resp.raise_for_status()
                                        result = cloudinary.uploader.upload(
                                            io.BytesIO(img_resp.content),
                                            folder="event_images",
                                            public_id=f"eb_{ev.get('id', title[:15])}",
                                            overwrite=False,
                                            resource_type="image",
                                        )
                                        image_cloudinary = result.get("public_id")
                                    except Exception:
                                        pass

                            event = Event(
                                title=title, category=cat_name, location=location,
                                language="English", date=date,
                                description=description[:1000],
                            )
                            if image_cloudinary:
                                event.image = image_cloudinary
                            event.save()
                            self.stdout.write(self.style.SUCCESS(f"    ✅  {title}"))
                            created_count += 1

                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"    ❌  Error: {e}"))
                            error_count += 1

                    if not has_more:
                        break

        self.stdout.write(self.style.SUCCESS(
            f"\n✨  Done! Created: {created_count} | Skipped: {skipped_count} | Errors: {error_count}\n"
        ))
