from django.utils import unittest
from django.contrib import admin

from hyperadmin import get_api
from hyperadmin.sites import ResourceSite, site

class SiteTestCase(unittest.TestCase):
    def test_install_from_admin_site(self):
        
        site = ResourceSite()
        admin.autodiscover()
        site.install_models_from_site(admin.site)
        
        self.assertTrue(site.registry)
    
    def test_get_api(self):
        found_site = get_api('hyperadmin')
        self.assertEqual(found_site, site)

