from django.utils import unittest
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.test.client import RequestFactory, FakePayload
from django.utils import simplejson as json

from hyperadmin.resources import ModelResource
from hyperadmin.sites import ResourceSite

from common import GenericURLResolver

class SuperUserRequestFactory(RequestFactory):
    def __init__(self, **kwargs):
        self.user = kwargs.pop('user', None)
        super(SuperUserRequestFactory, self).__init__(**kwargs)
    
    def request(self, **request):
        ret = super(SuperUserRequestFactory, self).request(**request)
        ret.user = self.user
        return ret

class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.site = ResourceSite()
        self.site.register_builtin_media_types()
        
        self.user = User(username='superuser', is_staff=True, is_active=True, is_superuser=True)
        self.resource = self.register_resource()
        self.factory = SuperUserRequestFactory(user=self.user, HTTP_ACCEPT='application/vnd.Collection+JSON')
        
        self.resolver = GenericURLResolver(r'^', self.site.get_urls())
        
        def reverse(name, *args, **kwargs):
            ret = self.resolver.reverse(name, *args, **kwargs)
            return ret
        
        self.site.reverse = reverse
    
    def register_resource(self):
        raise NotImplementedError

class ModelResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(ContentType, ModelResource)
        return self.site.registry[ContentType]
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        
        #assert False, response.content
    
    def test_get_detail(self):
        instance = ContentType.objects.all()[0]
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request, pk=instance.pk)
        data = json.loads(response.content)
        
        #assert False, response.content
    
    def test_post_detail(self):
        return
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        #request = self.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        
        assert False, response.content

class SiteResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(ContentType, ModelResource)
        return self.site.site_resource
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        
        self.assertEqual(data['collection']['items'][0]['href'], "contenttypes/")

class ApplicationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(ContentType, ModelResource)
        return self.site.applications.values()[0]
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        
        self.assertEqual(data['collection']['items'][0]['href'], "contenttypes/contenttype/")

