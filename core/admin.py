from django.contrib import admin
from .models import Event, Concert, Match
from .models import HeroBanner

admin.site.register(HeroBanner)
admin.site.register(Event)
admin.site.register(Concert)
admin.site.register(Match)