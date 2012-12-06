from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json

from hyperadmin.mediatypes.json import JSON, JSONP

from common import MediaTypeTestCase

class JsonTestCase(MediaTypeTestCase):
    def get_adaptor(self):
        class MockView(object):
            resource = self.resource
            request = self.factory.get('/')
        return JSON(MockView())
    
    def test_queryset_serialize(self):
        link = self.resource.endpoints['list'].link_prototypes['list'].get_link()
        state = {}
        state['auth'] = self.user
        
        response = self.adaptor.serialize(content_type='application/json', link=link, state=state)
        data = json.loads(response.content)
        self.assertEqual(len(data), ContentType.objects.count())
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        item = self.resource.get_resource_item(instance, endpoint=None)
        link = self.resource.get_item_link(item)
        state = self.resource.state
        state.item = item
        
        response = self.adaptor.serialize(content_type='application/json', link=link, state=state)
        data = json.loads(response.content)
        assert data, str(data)
        #self.assertEqual(len(json_items), 1)

class JsonpTestCase(MediaTypeTestCase):
    def get_adaptor(self):
        class MockView(object):
            resource = self.resource
            request = self.factory.get('/?callback=jscallback')
        return JSONP(MockView())
    
    def test_queryset_serialize(self):
        link = self.resource.endpoints['list'].link_prototypes['list'].get_link()
        state = {}
        state['auth'] = self.user
        
        response = self.adaptor.serialize(content_type='text/javascript', link=link, state=state)
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #self.assertEqual(len(data), len(items))
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        item = self.resource.get_resource_item(instance, endpoint=None)
        link = self.resource.get_item_link(item)
        state = {}
        state.item = item
        
        response = self.adaptor.serialize(content_type='text/javascript', link=link, state=state)
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #assert data, str(data)
        #self.assertEqual(len(json_items), 1)
        

