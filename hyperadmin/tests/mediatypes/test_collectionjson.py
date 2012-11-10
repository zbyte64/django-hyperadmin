from django.contrib.contenttypes.models import ContentType
from django.test.client import FakePayload
from django.utils import simplejson as json

from hyperadmin.mediatypes.collectionjson import CollectionJSON, CollectionNextJSON
from hyperadmin.resources.applications.site import SiteResource
from hyperadmin.resources.applications.application import ApplicationResource
from hyperadmin.sites import site

from common import MediaTypeTestCase

class CollectionJsonTestCase(MediaTypeTestCase):
    content_type = 'application/vnd.Collection+JSON'
    
    def get_adaptor(self):
        class MockView(object):
            resource = self.resource
            request = self.factory.get('/')
        return CollectionJSON(MockView())
    
    def test_queryset_serialize(self):
        link = self.resource.get_resource_link()
        state = self.resource.state
        state['auth'] = self.user
        
        response = self.adaptor.serialize(content_type=self.content_type, link=link, state=state)
        data = json.loads(response.content)
        json_items = data['collection']['items']
        self.assertEqual(len(json_items), len(ContentType.objects.all()))
    
    def test_model_instance_serialize(self):
        instance = ContentType.objects.all()[0]
        item = self.resource.get_resource_item(instance)
        link = self.resource.get_item_link(item)
        state = self.resource.state
        state.item = item
        
        response = self.adaptor.serialize(content_type=self.content_type, link=link, state=state)
        data = json.loads(response.content)
        json_items = data['collection']['items']
        self.assertEqual(len(json_items), 1)
    
    def test_site_resource_serialize(self):
        site_resource = SiteResource(site_state={'site':site})
        link = site_resource.get_resource_link()
        state = self.resource.state
        state['auth'] = self.user
        
        response = self.adaptor.serialize(content_type=self.content_type, link=link, state=state)
        data = json.loads(response.content)
        json_items = data['collection']['items']
        #assert False, str(json_items)
    
    def test_application_resource_serialize(self):
        app_resource = ApplicationResource(site_state={'site':site}, app_name='testapp')
        return
        #TODO patch reverse
        link = app_resource.get_resource_link()
        state = self.resource.state
        
        response = self.adaptor.serialize(content_type=self.content_type, link=link, state=state)
        data = json.loads(response.content)
        json_items = data['collection']['items']
        #assert False, str(json_items)
    
    def test_model_instance_deserialize(self):
        pass
        #items = [ContentType.objects.all()[0]]
        #payload = '''{"data":{}}'''
        #return
        #view.request = view.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        #adaptor = CollectionJSON(view)
        #data = adaptor.deserialize()
        #json_items = data['collection']['items']

class CollectionNextJsonTestCase(MediaTypeTestCase):
    def get_adaptor(self):
        class MockView(object):
            resource = self.resource
            request = self.factory.get('/')
        return CollectionNextJSON(MockView())
    
    def test_convert_field(self):
        form_class = self.resource.get_form_class()
        form = form_class()
        fields = list(form)
        field = fields[0]
        field_r = self.adaptor.convert_field(field)
        self.assertEqual(field_r['required'], field.field.required)
    
    def test_convert_errors(self):
        form_class = self.resource.get_form_class()
        form = form_class(data={})
        assert form.errors
        error_r = self.adaptor.convert_errors(form.errors)
        self.assertEqual(len(error_r['messages']), len(form.errors))
        

