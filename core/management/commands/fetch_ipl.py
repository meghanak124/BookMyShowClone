"""
Fetches IPL schedule from CricAPI and populates:
  - League  (one IPL league record)
  - LeagueEvent  (one per match: team names, venue, date/time, city)

The League.image and team logos are NOT auto-fetched (CricAPI free tier
doesn't serve images). You can upload them once in Django Admin.

Usage:
    python manage.py fetch_ipl
    python manage.py fetch_ipl --clear     # wipe existing LeagueEvents first

Get a free API key at https://www.cricapi.com/
Add to .env:  CRICAPI_KEY=your_key_here
"""

import os
from datetime import datetime

import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import League, LeagueEvent


CRICAPI_BASE = "https://api.cricapi.com/v1"

# IPL team short names → full names mapping
TEAM_NAME_MAP = {
    "CSK": "Chennai Super Kings",
    "MI": "Mumbai Indians",
    "RCB": "Royal Challengers Bengaluru",
    "KKR": "Kolkata Knight Riders",
    "DC": "Delhi Capitals",
    "SRH": "Sunrisers Hyderabad",
    "PBKS": "Punjab Kings",
    "RR": "Rajasthan Royals",
    "GT": "Gujarat Titans",
    "LSG": "Lucknow Super Giants",
}


class Command(BaseCommand):
    help = "Fetch IPL schedule from CricAPI and save to League / LeagueEvent"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing LeagueEvents before fetching",
        )

    def handle(self, *args, **options):
        api_key = os.environ.get("CRICAPI_KEY")
        if not api_key:
            raise CommandError(
                "\n\n  ❌  CRICAPI_KEY is not set in your .env file.\n"
                "  Get a free key at: https://www.cricapi.com/\n"
                "  Then add:  CRICAPI_KEY=your_key_here\n"
            )

        self.stdout.write(self.style.MIGRATE_HEADING("\n🏏  Fetching IPL schedule from CricAPI...\n"))

        # ── Get or create the IPL League record ───────────────────────────
        league, created = League.objects.get_or_create(
            title="Indian Premier League",
            defaults={
                "sport": "Cricket",
                "season_text": "IPL 2025",
                "interest_text": "Follow",
                "description": (
                    "The Indian Premier League (IPL) is a professional Twenty20 cricket "
                    "league held annually in India. It features the best players from "
                    "around the world competing for the coveted IPL trophy."
                ),
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("  ✅  Created IPL League record"))
        else:
            self.stdout.write("  ℹ️   IPL League record already exists — reusing it")

        # ── Optionally wipe existing events ──────────────────────────────
        if options["clear"]:
            count, _ = LeagueEvent.objects.filter(league=league).delete()
            self.stdout.write(f"  🗑   Cleared {count} existing LeagueEvents")

        # ── Fetch matches from CricAPI ────────────────────────────────────
        matches = self._fetch_ipl_matches(api_key)
        if not matches:
            self.stdout.write(self.style.WARNING("  ⚠️   No IPL matches returned from API"))
            return

        created_count = 0
        skipped_count = 0

        for match in matches:
            try:
                result = self._save_league_event(league, match)
                if result == "created":
                    created_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                name = match.get("name", "unknown")
                self.stderr.write(self.style.ERROR(f"  ❌  Error saving '{name}': {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✨  Done! Created: {created_count} | Skipped (already exist): {skipped_count}\n"
            )
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _fetch_ipl_matches(self, api_key):
        """Fetch upcoming + recent IPL matches from CricAPI."""
        all_matches = []
        offset = 0

        while True:
            try:
                resp = requests.get(
                    f"{CRICAPI_BASE}/matches",
                    params={"apikey": api_key, "offset": offset},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  API error at offset {offset}: {e}"))
                break

            if data.get("status") != "success":
                self.stderr.write(self.style.ERROR(f"  API returned: {data.get('status')}"))
                break

            results = data.get("data", [])
            if not results:
                break

            # Filter to IPL matches only
            ipl_matches = [
                m for m in results
                if "indian premier league" in (m.get("series_id", "") + " " + m.get("name", "")).lower()
                or "ipl" in m.get("name", "").lower()
            ]
            all_matches.extend(ipl_matches)

            # CricAPI returns 25 per page; stop if fewer returned
            if len(results) < 25:
                break
            offset += 25

        self.stdout.write(f"  📡  Found {len(all_matches)} IPL matches from API")
        return all_matches

    def _save_league_event(self, league, match):
        """Create a LeagueEvent from a CricAPI match dict. Returns 'created' or 'skipped'."""
        teams = match.get("teams", [])
        if len(teams) < 2:
            return "skipped"

        team_one = teams[0]
        team_two = teams[1]

        # Full names if we know the short code
        team_one_full = TEAM_NAME_MAP.get(team_one, team_one)
        team_two_full = TEAM_NAME_MAP.get(team_two, team_two)

        # Venue and city
        venue = match.get("venue", "TBD")
        # CricAPI venue is usually "Stadium Name, City"
        city = venue.split(",")[-1].strip() if "," in venue else "India"

        # Date + time text
        date_str = match.get("date", "")
        time_text = "Check schedule"
        date_heading = ""
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dt_local = timezone.localtime(dt)
                date_heading = dt_local.strftime("%A, %d %B %Y")
                time_text = dt_local.strftime("%I:%M %p IST")
            except Exception:
                date_heading = date_str
                time_text = "Check schedule"

        # Match number / name
        match_name = match.get("name", f"{team_one} vs {team_two}")
        match_number = match_name  # e.g. "CSK vs MI, 5th Match"

        # Skip if already saved (by match_number + league)
        if LeagueEvent.objects.filter(league=league, match_number=match_number).exists():
            return "skipped"

        LeagueEvent.objects.create(
            league=league,
            match_number=match_number,
            date_heading=date_heading,
            city=city,
            team_one=team_one_full,
            team_two=team_two_full,
            venue=venue,
            time_text=time_text,
            booking_text="Book Now",
        )

        self.stdout.write(
            self.style.SUCCESS(f"    ✅  {team_one_full} vs {team_two_full} — {date_heading}")
        )
        return "created"
