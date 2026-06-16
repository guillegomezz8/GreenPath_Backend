from django.contrib.admin.sites import AdminSite
from django.contrib.gis import forms as gis_forms
from django.test import SimpleTestCase

from apps.user.admin import ClientAdmin
from apps.user.models.client import Client


class ClientAdminTests(SimpleTestCase):
    def test_client_location_uses_osm_widget(self):
        client_admin = ClientAdmin(Client, AdminSite())

        formfield = client_admin.formfield_for_dbfield(Client._meta.get_field("location"), request=None)

        self.assertIsInstance(formfield.widget, gis_forms.OSMWidget)
        self.assertEqual(formfield.widget.attrs.get("default_lat"), 37.3886)
        self.assertEqual(formfield.widget.attrs.get("default_lon"), -5.9823)
