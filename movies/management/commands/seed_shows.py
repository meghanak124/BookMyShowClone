import random
from datetime import datetime, timedelta, time

from django.core.management.base import BaseCommand
from django.utils import timezone

from movies.models import Movie, Show, Theatre


class Command(BaseCommand):
    help = "Create sample shows for the first 30 movies for the next 3 days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--movies",
            type=int,
            default=30,
            help="Number of movies to use (default: 30)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=3,
            help="Number of days to create shows for (default: 3)",
        )

    def handle(self, *args, **options):
        movie_limit = options["movies"]
        days = options["days"]

        theatres = Theatre.objects.filter(
            name__in=[
                "PVR Hyderabad",
                "INOX Bengaluru",
                "AMB Cinemas Hyderabad",
                "Cinepolis Mumbai",
            ]
        )

        if theatres.count() < 4:
            self.stdout.write(
                self.style.ERROR(
                    "Please create these 4 theatres first in admin:\n"
                    "- PVR Hyderabad\n"
                    "- INOX Bengaluru\n"
                    "- AMB Cinemas Hyderabad\n"
                    "- Cinepolis Mumbai"
                )
            )
            return

        movies = Movie.objects.all().order_by("id")[:movie_limit]

        if not movies.exists():
            self.stdout.write(self.style.ERROR("No movies found in database."))
            return

        time_slots = [
            time(10, 0),
            time(13, 30),
            time(17, 0),
            time(20, 30),
        ]

        created_count = 0
        skipped_count = 0

        for movie in movies:
            for day_offset in range(days):
                show_date = timezone.localdate() + timedelta(days=day_offset)

                selected_theatres = random.sample(
                    list(theatres),
                    k=random.randint(1, min(3, theatres.count()))
                )

                selected_slots = random.sample(
                    time_slots,
                    k=random.randint(1, min(3, len(time_slots)))
                )

                for theatre in selected_theatres:
                    for slot in selected_slots:
                        naive_datetime = datetime.combine(show_date, slot)
                        aware_datetime = timezone.make_aware(
                            naive_datetime,
                            timezone.get_current_timezone()
                        )

                        show, created = Show.objects.get_or_create(
                            movie=movie,
                            theatre=theatre,
                            show_time=aware_datetime,
                            defaults={
                                "total_seats": theatre.rows * theatre.columns,
                                "available_seats": str(theatre.rows * theatre.columns),
                            },
                        )

                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Created: {movie.title} | {theatre.name} | {aware_datetime}"
                                )
                            )
                        else:
                            skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Created {created_count} shows, skipped {skipped_count} existing shows."
            )
        )