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
        endpoint = self.resource.endpoints['list']
        endpoint.initialize_state(auth=self.user)
        link = endpoint.link_prototypes['list'].get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='application/json', link=link, state=state)
        data = json.loads(response.content)
        self.assertEqual(len(data), ContentType.objects.count())
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        
        endpoint = self.resource.endpoints['detail']
        endpoint.initialize_state(auth=self.user)
        endpoint.state.item = item = endpoint.get_resource_item(instance)
        link = item.get_link()
        state = endpoint.state
        
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
        endpoint = self.resource.endpoints['list']
        endpoint.initialize_state(auth=self.user)
        link = endpoint.link_prototypes['list'].get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='text/javascript', link=link, state=state)
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #self.assertEqual(len(data), len(items))
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        
        endpoint = self.resource.endpoints['detail']
        endpoint.initialize_state(auth=self.user)
        endpoint.state.item = item = endpoint.get_resource_item(instance)
        link = item.get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='text/javascript', link=link, state=state)
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #assert data, str(data)
        #self.assertEqual(len(json_items), 1)
        

