"""
Management command to auto-fetch movies from TMDB and save them to the database.
Posters are uploaded directly to Cloudinary (same storage your project already uses).

Usage:
    python manage.py fetch_movies                  # fetches Now Playing (default)
    python manage.py fetch_movies --type popular   # fetches Popular movies
    python manage.py fetch_movies --type upcoming  # fetches Upcoming movies
    python manage.py fetch_movies --pages 3        # fetch 3 pages (~60 movies)
    python manage.py fetch_movies --language hi    # fetch Hindi movies
"""

import io
import os

import cloudinary.uploader
import requests
from django.core.management.base import BaseCommand, CommandError

from movies.models import Movie

# ─── TMDB Configuration ──────────────────────────────────────────────────────

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Map TMDB genre IDs → readable genre names
GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}

# Map TMDB language codes → full language names
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "kn": "Kannada",
    "mr": "Marathi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "it": "Italian",
}


class Command(BaseCommand):
    help = "Fetch movies from TMDB API and save them to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            default="now_playing",
            choices=["now_playing", "popular", "upcoming"],
            help="Type of movies to fetch (default: now_playing)",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=2,
            help="Number of pages to fetch (20 movies per page, default: 2)",
        )
        parser.add_argument(
            "--language",
            type=str,
            default=None,
            help="Filter by original language code e.g. hi, ta, te (default: all)",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            default=True,
            help="Skip movies that already exist in DB by title (default: True)",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("TMDB_API_KEY")
        if not api_key:
            raise CommandError(
                "\n\n  ❌  TMDB_API_KEY is not set.\n"
                "  Add it to your .env file:\n"
                "      TMDB_API_KEY=your_key_here\n\n"
                "  Get a free key at: https://www.themoviedb.org/settings/api\n"
            )

        movie_type = options["type"]
        total_pages = options["pages"]
        lang_filter = options["language"]
        skip_existing = options["skip_existing"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n🎬  Fetching '{movie_type}' movies from TMDB  (pages: {total_pages})\n"
            )
        )

        created_count = 0
        skipped_count = 0
        error_count = 0

        for page in range(1, total_pages + 1):
            self.stdout.write(f"  📄 Fetching page {page}/{total_pages}...")

            try:
                results = self._fetch_tmdb_page(api_key, movie_type, page, lang_filter)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Failed to fetch page {page}: {e}"))
                continue

            for item in results:
                title = item.get("title", "").strip()
                if not title:
                    continue

                # Skip if already in DB
                if skip_existing and Movie.objects.filter(title__iexact=title).exists():
                    self.stdout.write(f"    ⏭  Skipping (already exists): {title}")
                    skipped_count += 1
                    continue

                try:
                    movie = self._create_movie(api_key, item)
                    self.stdout.write(self.style.SUCCESS(f"    ✅  Added: {movie.title}"))
                    created_count += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"    ❌  Error saving '{title}': {e}"))
                    error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✨  Done! Created: {created_count} | Skipped: {skipped_count} | Errors: {error_count}\n"
            )
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _fetch_tmdb_page(self, api_key, movie_type, page, lang_filter):
        """Fetch one page of movies from TMDB."""
        params = {
            "api_key": api_key,
            "language": "en-US",
            "page": page,
            "region": "IN",  # India region for relevant releases
        }
        if lang_filter:
            params["with_original_language"] = lang_filter

        url = f"{TMDB_BASE_URL}/movie/{movie_type}"
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("results", [])

    def _fetch_movie_details(self, api_key, tmdb_id):
        """Fetch full movie details including runtime."""
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        resp = requests.get(url, params={"api_key": api_key}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _create_movie(self, api_key, item):
        """Build and save a Movie object from a TMDB result dict."""
        tmdb_id = item["id"]

        # Fetch full details for runtime
        details = self._fetch_movie_details(api_key, tmdb_id)

        # ── Fields mapping ────────────────────────────────────────────────
        title = item.get("title", "Unknown")

        # Genre: join all genre names as comma-separated string
        genre_ids = item.get("genre_ids", [])
        genre = ", ".join(
            GENRE_MAP.get(gid, "") for gid in genre_ids if GENRE_MAP.get(gid)
        ) or "General"

        # Duration: TMDB gives runtime in minutes
        runtime = details.get("runtime") or 0
        duration = f"{runtime} min" if runtime else "N/A"

        # Language: map code to full name
        orig_lang_code = item.get("original_language", "en")
        language = LANGUAGE_MAP.get(orig_lang_code, orig_lang_code.upper())

        # Format: default to "2D" (admin can change to 3D/IMAX if needed)
        format_ = "2D"

        # Release date
        release_date = item.get("release_date") or "2024-01-01"

        # Description
        description = item.get("overview", "No description available.")

        # Meta: use vote_average as rating
        vote_avg = item.get("vote_average", 0)
        meta_type = "rating"
        meta_value = str(round(vote_avg, 1)) if vote_avg else ""

        # Card subtitle: e.g. "Action • Hindi"
        card_subtitle = f"{genre.split(',')[0].strip()} • {language}"

        # ── Poster: upload to Cloudinary ──────────────────────────────────
        poster_cloudinary = self._upload_poster_to_cloudinary(item, title)

        # ── Create the Movie object ───────────────────────────────────────
        movie = Movie(
            title=title,
            genre=genre,
            duration=duration,
            language=language,
            format=format_,
            release_date=release_date,
            description=description,
            meta_type=meta_type,
            meta_value=meta_value,
            card_subtitle=card_subtitle,
            is_premiere=False,
        )

        # Assign poster if upload succeeded
        if poster_cloudinary:
            movie.poster = poster_cloudinary

        movie.save()
        return movie

    def _upload_poster_to_cloudinary(self, item, title):
        """Download poster from TMDB and upload to Cloudinary. Returns public_id or None."""
        poster_path = item.get("poster_path")
        if not poster_path:
            return None

        try:
            img_url = f"{TMDB_IMAGE_BASE}{poster_path}"
            img_resp = requests.get(img_url, timeout=15)
            img_resp.raise_for_status()

            # Upload raw bytes to Cloudinary under a 'movie_posters/' folder
            result = cloudinary.uploader.upload(
                io.BytesIO(img_resp.content),
                folder="movie_posters",
                public_id=f"tmdb_{item['id']}",
                overwrite=False,          # don't re-upload if already there
                resource_type="image",
            )
            # Return the public_id so CloudinaryField can store it
            return result.get("public_id")
        except Exception as e:
            self.stderr.write(f"      ⚠  Poster upload failed for '{title}': {e}")
            return None
