from django.contrib import admin
from .models import Event, Match
from .models import HeroBanner
from .models import (
    Stream,
    Play,
    Sport,
    Activity,
    League,
    Team,
    LeagueEvent,
)

admin.site.register(Stream)
admin.site.register(Play)
admin.site.register(Sport)
admin.site.register(Activity)
admin.site.register(League)
admin.site.register(Team)
admin.site.register(LeagueEvent)
admin.site.register(HeroBanner)
admin.site.register(Event)
admin.site.register(Match)