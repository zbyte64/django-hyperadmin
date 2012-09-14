from django.utils import unittest
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json

from hyperadmin.mediatypes.json import JSON, JSONP

from common import BaseMockResourceView

class JsonMockResourceView(BaseMockResourceView):
    content_type='application/json'
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]

class JsonpMockResourceView(BaseMockResourceView):
    content_type='text/javascript'
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]
    
    def __init__(self, items=[]):
        BaseMockResourceView.__init__(self, items)
        self.request = self.factory.get('/?callback=jscallback')

class JsonTestCase(unittest.TestCase):
    def test_queryset_serialize(self):
        items = ContentType.objects.all()
        view = JsonMockResourceView(items)
        adaptor = JSON(view)
        response = adaptor.serialize(content_type='application/json', )
        data = json.loads(response.content)
        self.assertEqual(len(data), len(items))
    
    def test_model_instance_serialize(self):
        items = [ContentType.objects.all()[0]]
        view = JsonMockResourceView(items)
        adaptor = JSON(view)
        response = adaptor.serialize(content_type='application/json')
        data = json.loads(response.content)
        assert data, str(data)
        #self.assertEqual(len(json_items), 1)

class JsonpTestCase(unittest.TestCase):
    def test_queryset_serialize(self):
        items = ContentType.objects.all()
        view = JsonpMockResourceView(items)
        adaptor = JSONP(view)
        response = adaptor.serialize(content_type='text/javascript')
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #self.assertEqual(len(data), len(items))
    
    def test_model_instance_serialize(self):
        items = [ContentType.objects.all()[0]]
        view = JsonpMockResourceView(items)
        adaptor = JSONP(view)
        response = adaptor.serialize(content_type='text/javascript')
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #assert data, str(data)
        #self.assertEqual(len(json_items), 1)
        

