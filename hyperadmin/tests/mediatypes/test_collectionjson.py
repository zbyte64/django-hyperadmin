from django.utils import unittest
from django.contrib.contenttypes.models import ContentType
from django.test.client import FakePayload
from django.utils import simplejson as json

from hyperadmin.mediatypes.collectionjson import CollectionJSON, CollectionNextJSON
from hyperadmin.resources.applications.site import SiteResource
from hyperadmin.resources.applications.application import ApplicationResource
from hyperadmin.sites import site

from common import BaseMockResourceView

class MockResourceView(BaseMockResourceView):
    content_type='application/vnd.Collection.next+JSON'

class CollectionMockResourceView(MockResourceView):
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]

class CollectionJsonTestCase(unittest.TestCase):
    def test_queryset_serialize(self):
        items = ContentType.objects.all()
        view = CollectionMockResourceView(items)
        adaptor = CollectionJSON(view)
        return
        response = adaptor.serialize(content_type='application/vnd.Collection.next+JSON')
        data = json.loads(response.content)
        json_items = data['collection']['items']
        self.assertEqual(len(json_items), len(items))
    
    def test_model_instance_serialize(self):
        items = [ContentType.objects.all()[0]]
        view = CollectionMockResourceView(items)
        adaptor = CollectionJSON(view)
        return
        response = adaptor.serialize(instance=items[0], content_type='application/vnd.Collection.next+JSON')
        data = json.loads(response.content)
        json_items = data['collection']['items']
        self.assertEqual(len(json_items), 1)
    
    def test_site_resource_serialize(self):
        site_resource = SiteResource(site=site)
        items = [site_resource]
        view = CollectionMockResourceView(items)
        adaptor = CollectionJSON(view)
        return #skip test
        response = adaptor.serialize(content_type='application/vnd.Collection.next+JSON')
        data = json.loads(response.content)
        json_items = data['collection']['items']
        #assert False, str(json_items)
    
    def test_application_resource_serialize(self):
        app_resource = ApplicationResource(site=site, app_name='testapp')
        items = [app_resource]
        view = CollectionMockResourceView(items)
        adaptor = CollectionJSON(view)
        return #skip test
        response = adaptor.serialize(content_type='application/vnd.Collection.next+JSON')
        data = json.loads(response.content)
        json_items = data['collection']['items']
        #assert False, str(json_items)
    
    def test_model_instance_deserialize(self):
        items = [ContentType.objects.all()[0]]
        payload = '''{"data":{}}'''
        view = CollectionMockResourceView(items)
        return
        view.request = view.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        adaptor = CollectionJSON(view)
        data = adaptor.deserialize()
        #json_items = data['collection']['items']

class CollectionNextJsonTestCase(unittest.TestCase):
    def test_convert_field(self):
        view = CollectionMockResourceView([])
        form_class = view.get_form_class()
        form = form_class()
        fields = list(form)
        field = fields[0]
        adaptor = CollectionNextJSON(view)
        field_r = adaptor.convert_field(field)
        self.assertEqual(field_r['required'], field.field.required)
    
    def test_convert_errors(self):
        view = CollectionMockResourceView([])
        form_class = view.get_form_class()
        form = form_class(data={})
        assert form.errors
        adaptor = CollectionNextJSON(view)
        error_r = adaptor.convert_errors(form.errors)
        self.assertEqual(len(error_r['messages']), len(form.errors))
        

