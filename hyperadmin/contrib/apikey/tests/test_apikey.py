from django.utils import unittest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test.client import RequestFactory

from hyperadmin.resources.models import ModelResource
from hyperadmin.sites import ResourceSite
from hyperadmin.apirequests import InternalAPIRequest, NamespaceAPIRequest
from hyperadmin.endpoints import RootEndpoint
from hyperadmin.contrib.apikey.apirequests import HTTPAPIKeyRequest
from hyperadmin.contrib.apikey.models import ApiKey

from hyperadmin.tests.common import GenericURLResolver, SuperUserRequestFactory

from mock import MagicMock


class UserResource(ModelResource):
    list_display = ['username', 'email']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    date_hierarchy = 'date_joined'
    search_fields = ['email', 'username']

class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.site = ResourceSite(apirequest_class=HTTPAPIKeyRequest)
        self.site.register_builtin_media_types()
        
        self.user = User.objects.get_or_create(username='superuser', is_staff=True, is_active=True, is_superuser=True)[0]
        self.resource = self.register_resource()
        
        self.api_key_instance = ApiKey.objects.get_or_create(user=self.user, key='foobar')[0]
        self.api_key = self.api_key_instance.key
        self.factory = RequestFactory(HTTP_ACCEPT='text/html', API_KEY=self.api_key)
        
        self.resolver = GenericURLResolver(r'^', self.site.get_urls())
        
        def reverse(name, *args, **kwargs):
            ret = self.resolver.reverse(name, *args, **kwargs)
            return ret
        self.reverse = reverse
        
        def cls_reverse(slf, name, *args, **kwargs):
            return self.resolver.reverse(name, *args, **kwargs)
        
        original_fork = self.site.fork
        
        def fork(**kwargs):
            ret = original_fork(**kwargs)
            ret.reverse = reverse
            return ret
        
        self.site.fork = fork
        NamespaceAPIRequest.reverse = cls_reverse
        RootEndpoint.reverse = cls_reverse
        self.site.reverse = reverse
    
    def get_api_request(self, **kwargs):
        kwargs.setdefault('site', self.site)
        #kwargs.setdefault('user', self.user)
        #kwargs.setdefault('params', {})
        #kwargs.setdefault('method', 'GET')
        #kwargs.setdefault('payload', {})
        kwargs.setdefault('request', self.factory.get('/'))
        kwargs.setdefault('url_args', [])
        kwargs.setdefault('url_kwargs', {})
        #kwargs.setdefault('reverse', self.reverse)
        api_request = HTTPAPIKeyRequest(**kwargs)
        api_request.populate_session_data_from_request(kwargs['request'])
        
        api_request.generate_response = MagicMock(return_value=HttpResponse())
        
        return api_request
    
    def register_resource(self):
        raise NotImplementedError

class APIKeyTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, UserResource, app_name='auth')
        return self.site.registry[User]
    
    def test_user_lookup(self):
        api_request = self.get_api_request()
        self.assertEqual(self.user, api_request.user)
