from django.utils import unittest
from django.contrib import admin

from hyperadmin.sites import ResourceSite

class SiteTestCase(unittest.TestCase):
    def test_install_from_admin_site(self):
        
        site = ResourceSite()
        admin.autodiscover()
        site.install_models_from_site(admin.site)
        
        self.assertTrue(site.registry)
