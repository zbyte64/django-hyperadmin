from django.utils import unittest
from django.contrib.contenttypes.models import ContentType
from django import forms
from django.test.client import RequestFactory, FakePayload
from django.utils import simplejson as json

from hyperadmin.mediatypes import CollectionJSON
from hyperadmin.views import ResourceViewMixin
from hyperadmin.resources import SiteResource, ApplicationResource
from hyperadmin.sites import site

class MockResourceView(ResourceViewMixin):
    def __init__(self, items=[], content_type='application/vnd.Collection+JSON'):
        self.items = items
        self.content_type = 'application/vnd.Collection+JSON'
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        ResourceViewMixin.__init__(self)
    
    def get_items(self, **kwargs):
        return self.items
    
    def get_content_type(self):
        return self.content_type
    
    def get_form_class(self, **kwargs):
        class GenForm(forms.ModelForm):
            class Meta:
                model = ContentType
        return GenForm
    
    def get_instance_url(self, instance):
        return None
    
    def get_embedded_links(self, instance=None):
        return []
    
    def get_outbound_links(self, instance=None):
        return []
    
    def get_templated_queries(self):
        return []
    
    def get_ln_links(self, instance=None):
        return []
    
    def get_li_links(self, instance=None):
        return []

class CollectionJsonTestCase(unittest.TestCase):
    def test_queryset_serialize(self):
        items = ContentType.objects.all()
        view = MockResourceView(items)
        adaptor = CollectionJSON(view)
        response = adaptor.serialize()
        data = json.loads(response.content)
        json_items = data['collection']['items']
        '''
        {'items': [{'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'content type'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'contenttypes'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'contenttype'}], 'links': []}, {'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'group'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'auth'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'group'}], 'links': []}, {'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'permission'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'auth'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'permission'}], 'links': []}, {'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'session'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'sessions'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'session'}], 'links': []}, {'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'site'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'sites'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'site'}], 'links': []}, {'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'user'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'auth'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'user'}], 'links': []}], 'template': {'data': [{'prompt': u'Name', 'name': u'name', 'value': None}, {'prompt': u'App label', 'name': u'app_label', 'value': None}, {'prompt': u'Python model class name', 'name': u'model', 'value': None}]}, 'links': [], 'queries': []}
        '''
    
    def test_model_instance_serialize(self):
        items = [ContentType.objects.all()[0]]
        view = MockResourceView(items)
        adaptor = CollectionJSON(view)
        response = adaptor.serialize(instance=items[0])
        data = json.loads(response.content)
        json_items = data['collection']['items']
        '''
        {'items': [{'href': None, 'data': [{'prompt': u'Name', 'name': u'name', 'value': u'content type'}, {'prompt': u'App label', 'name': u'app_label', 'value': u'contenttypes'}, {'prompt': u'Python model class name', 'name': u'model', 'value': u'contenttype'}], 'links': []}], 'template': {'data': [{'prompt': u'Name', 'name': u'name', 'value': None}, {'prompt': u'App label', 'name': u'app_label', 'value': None}, {'prompt': u'Python model class name', 'name': u'model', 'value': None}]}, 'links': [], 'queries': []}
        '''
    
    def test_site_resource_serialize(self):
        site_resource = SiteResource(site=site)
        items = [site_resource]
        view = MockResourceView(items)
        adaptor = CollectionJSON(view)
        response = adaptor.serialize()
        data = json.loads(response.content)
        json_items = data['collection']['items']
        #assert False, str(json_items)
    
    def test_application_resource_serialize(self):
        app_resource = ApplicationResource(site=site, app_name='testapp')
        items = [app_resource]
        view = MockResourceView(items)
        adaptor = CollectionJSON(view)
        response = adaptor.serialize()
        data = json.loads(response.content)
        json_items = data['collection']['items']
        #assert False, str(json_items)
    
    def test_model_instance_deserialize(self):
        items = [ContentType.objects.all()[0]]
        payload = '{}'
        view = MockResourceView(items)
        view.request = view.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        adaptor = CollectionJSON(view)
        data = adaptor.deserialize()
        #json_items = data['collection']['items']

