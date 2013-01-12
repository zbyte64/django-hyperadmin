from django.contrib.contenttypes.models import ContentType

from hyperadmin.resources.models import ModelResource
from hyperadmin.tests.test_resources import ResourceTestCase

from mock import MagicMock

class MediaTypeTestCase(ResourceTestCase):
    def setUp(self):
        super(MediaTypeTestCase, self).setUp()
        self.adaptor = self.get_adaptor()
        self.adaptor.detect_redirect = MagicMock()
        self.adaptor.detect_redirect.return_value = False
    
    def get_adaptor(self):
        pass
    
    def register_resource(self):
        self.site.register(ContentType, ModelResource)
        return self.site.registry[ContentType]
