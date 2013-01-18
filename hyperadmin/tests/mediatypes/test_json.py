from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json

from hyperadmin.mediatypes.json import JSON, JSONP

from common import MediaTypeTestCase


class JsonTestCase(MediaTypeTestCase):
    def get_adaptor(self):
        self.api_request = self.get_api_request()
        return JSON(self.api_request)
    
    def test_queryset_serialize(self):
        endpoint = self.resource.endpoints['list']
        endpoint = endpoint.fork(api_request=self.api_request)
        
        link = endpoint.link_prototypes['list'].get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='application/json', link=link, state=state)
        data = json.loads(response.content)
        self.assertEqual(len(data), ContentType.objects.count())
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        
        endpoint = self.resource.endpoints['detail']
        endpoint = endpoint.fork(api_request=self.api_request)
        endpoint.state.item = item = endpoint.get_resource_item(instance)
        link = item.get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='application/json', link=link, state=state)
        data = json.loads(response.content)
        assert data, str(data)
        #self.assertEqual(len(json_items), 1)

class JsonpTestCase(MediaTypeTestCase):
    def get_adaptor(self):
        self.api_request = self.get_api_request(params={'callback':'jscallback'})
        return JSONP(self.api_request)
    
    def test_queryset_serialize(self):
        
        endpoint = self.resource.endpoints['list']
        endpoint = endpoint.fork(api_request=self.api_request)
        
        link = endpoint.link_prototypes['list'].get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='text/javascript', link=link, state=state)
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #self.assertEqual(len(data), len(items))
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        
        endpoint = self.resource.endpoints['detail']
        endpoint = endpoint.fork(api_request=self.api_request)

        endpoint.state.item = item = endpoint.get_resource_item(instance)
        link = item.get_link()
        state = endpoint.state
        
        response = self.adaptor.serialize(content_type='text/javascript', link=link, state=state)
        self.assertTrue(response.content.startswith('jscallback('))
        #data = json.loads(response.content)
        #assert data, str(data)
        #self.assertEqual(len(json_items), 1)
        

