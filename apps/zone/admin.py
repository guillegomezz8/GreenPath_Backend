from django.contrib.gis import admin
from django.contrib.gis import forms
from django.contrib.gis.db import models as geomodels
from apps.zone.models import Zone

@admin.register(Zone)
class ZoneAdmin(admin.GISModelAdmin):
    list_display = ('id', 'name', 'company')
    list_filter = ('company',)
    search_fields = ('name', 'company__name')

    formfield_overrides = {
        geomodels.PolygonField: {
            'widget': forms.OSMWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'default_lat': 37.3886,
                    'default_lon': -5.9823,
                }
            )
        },
    }
