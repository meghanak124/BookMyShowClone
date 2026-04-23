from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from core.models import League, LeagueEvent, Team


TEAM_LOGO_FILES = {
    "Chennai Super Kings": "csk.png",
    "Delhi Capitals": "dc.png",
    "Gujarat Titans": "gt.png",
    "Kolkata Knight Riders": "kkr.png",
    "Lucknow Super Giants": "lsg.png",
    "Mumbai Indians": "mi.png",
    "Punjab Kings": "pbks.png",
    "Rajasthan Royals": "rr.png",
    "Royal Challengers Bengaluru": "rcb.png",
    "Sunrisers Hyderabad": "srh.png",
}


class Command(BaseCommand):
    help = "Create IPL teams, attach local logos, and reflect them to LeagueEvent logos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing team logos",
        )

    def handle(self, *args, **options):
        force = options["force"]

        league = League.objects.filter(events__isnull=False).distinct().first()
        if not league:
            raise CommandError("No league with league events found. Load fixture first.")

        events = LeagueEvent.objects.filter(league=league)
        if not events.exists():
            raise CommandError("No IPL league events found.")

        logos_dir = Path(settings.MEDIA_ROOT) / "team_logos"
        if not logos_dir.exists():
            raise CommandError(f"Logo folder not found: {logos_dir}")

        self.stdout.write(self.style.MIGRATE_HEADING("\nSyncing IPL team logos...\n"))

        team_names = set()
        for event in events:
            if event.team_one:
                team_names.add(event.team_one.strip())
            if event.team_two:
                team_names.add(event.team_two.strip())

        created_teams = 0
        attached_logos = 0
        reused_logos = 0
        missing_files = 0

        for team_name in sorted(team_names):
            team, created = Team.objects.get_or_create(
                league=league,
                name=team_name,
            )

            if created:
                created_teams += 1
                self.stdout.write(self.style.SUCCESS(f"Created team: {team_name}"))

            if team.logo and not force:
                reused_logos += 1
                self.stdout.write(f"Logo already present: {team_name}")
                continue

            logo_filename = TEAM_LOGO_FILES.get(team_name)
            if not logo_filename:
                missing_files += 1
                self.stdout.write(self.style.WARNING(f"No filename mapping for: {team_name}"))
                continue

            logo_path = logos_dir / logo_filename
            if not logo_path.exists():
                missing_files += 1
                self.stdout.write(self.style.WARNING(f"Logo file missing: {logo_path}"))
                continue

            relative_logo_path = f"team_logos/{logo_filename}"
            team.logo = relative_logo_path
            team.save(update_fields=["logo"])

            attached_logos += 1
            self.stdout.write(self.style.SUCCESS(f"Attached logo: {team_name}"))

        updated_events = 0

        for event in events:
            team_one_obj = Team.objects.filter(
                league=league,
                name__iexact=event.team_one.strip()
            ).first()

            team_two_obj = Team.objects.filter(
                league=league,
                name__iexact=event.team_two.strip()
            ).first()

            changed = False

            if team_one_obj and team_one_obj.logo:
                event.team_one_logo = team_one_obj.logo
                changed = True

            if team_two_obj and team_two_obj.logo:
                event.team_two_logo = team_two_obj.logo
                changed = True

            if changed:
                event.save(update_fields=["team_one_logo", "team_two_logo"])
                updated_events += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone.\n"
                f"Teams created: {created_teams}\n"
                f"Logos attached: {attached_logos}\n"
                f"Logos reused: {reused_logos}\n"
                f"Missing files: {missing_files}\n"
                f"League events updated: {updated_events}\n"
            )
        )