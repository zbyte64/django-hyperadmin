from StringIO import StringIO

from django.utils import unittest
from django.contrib.auth.models import User, Group
from django.test.client import FakePayload
from django.utils import simplejson as json
from django.core.files.base import ContentFile

from hyperadmin.resources import ModelResource, InlineModelResource
from hyperadmin.sites import ResourceSite

from common import GenericURLResolver, SuperUserRequestFactory

class GroupsInline(InlineModelResource):
    model = User.groups.through
    rel_name = 'user' #TODO this should not be needed

class UserResource(ModelResource):
    inlines = [GroupsInline]
    list_display = ['username', 'email']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    date_hierarchy = 'date_joined'
    search_fields = ['email', 'username']

class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.site = ResourceSite()
        self.site.register_builtin_media_types()
        
        self.user = User.objects.get_or_create(username='superuser', is_staff=True, is_active=True, is_superuser=True)[0]
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
        self.site.register(User, UserResource)
        return self.site.registry[User]
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('items' in data)
        self.assertTrue('queries' in data)
        
        #assert False, response.content
    
    def test_get_detail(self):
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request, pk=instance.pk)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        #assert False, response.content
    
    def test_post_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        update_data = {
            'username': 'normaluser',
            'email': 'z@z.com',
        }
        payload = json.dumps({'data':update_data})
        request = self.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        response = view(request)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('error' in data)
        self.assertTrue('items' in data)
        
        #assert False, response.content
    
    def test_post_detail(self):
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        update_data = {
            'email': 'z@z.com',
        }
        payload = json.dumps({'data':update_data})
        request = self.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        response = view(request, pk=instance.pk)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data, str(view))
        self.assertTrue('error' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        #assert False, response.content

class InlineModelResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, UserResource)
        return self.site.registry[User].inline_instances[0]
    
    def test_get_list(self):
        group = Group.objects.get_or_create(name='testgroup')[0]
        self.user.groups.add(group)
        
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request, pk=self.user.pk)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        #assert False, response.content
    
    #TODO
    def test_get_detail(self):
        return
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request, pk=instance.pk)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        #assert False, response.content
    
    #TODO
    def test_post_list(self):
        return
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        update_data = {
            'username': 'normaluser',
            'email': 'z@z.com',
        }
        payload = json.dumps({'data':update_data})
        request = self.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        response = view(request)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('error' in data)
        self.assertTrue('items' in data)
        
        #assert False, response.content
    
    #TODO
    def test_post_detail(self):
        return
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        update_data = {
            'email': 'z@z.com',
        }
        payload = json.dumps({'data':update_data})
        request = self.factory.post('/', **{'wsgi.input':FakePayload(payload), 'CONTENT_LENGTH':len(payload)})
        response = view(request, pk=instance.pk)
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data, str(view))
        self.assertTrue('error' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        #assert False, response.content

class SiteResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, ModelResource)
        return self.site.site_resource
    
    '''
    def test_index(self):
        factory = SuperUserRequestFactory(user=self.user)
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = factory.get('/')
        response = view(request)
    '''
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        
        self.assertEqual(data['collection']['items'][0]['href'], "auth/")

class ApplicationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, ModelResource)
        return self.site.applications.values()[0]
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        
        self.assertEqual(data['collection']['items'][0]['href'], "auth/user/")

class StorageResourceTestCase(ResourceTestCase):
    def register_resource(self):
        from django.conf import settings
        import os, shutil
        for directory in (settings.MEDIA_ROOT, settings.STATIC_ROOT):
            try:
                shutil.rmtree(directory, ignore_errors=True)
                os.makedirs(directory)
            except:
                pass
        self.site.install_storage_resources()
        return self.site.applications['-storages'].resource_adaptor['media']
    
    def test_get_list(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
        self.assertEqual(len(data['collection']['items']), 1)
    
    def test_get_detail(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request, path='test.txt')
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        self.assertEqual(data['items'][0]['href'], '-storages/media/test.txt/')
    
    def test_post_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        update_data = {
            'name': 'test.txt',
            'upload': StringIO('test2'),
        }
        update_data['upload'].name = 'test.txt'
        request = self.factory.post('/', update_data, HTTP_ACCEPT='application/vnd.Collection+JSON')
        response = view(request)
        #TODO this returns a redirect, we need to test a failure
        '''
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data)
        self.assertTrue('error' in data)
        self.assertTrue('items' in data)
        
        #assert False, response.content
        '''
    
    def test_post_detail(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        update_data = {
            'name': 'test.txt',
            'upload': StringIO('test2'),
        }
        update_data['upload'].name = 'test.txt'
        request = self.factory.post('/', update_data, HTTP_ACCEPT='application/vnd.Collection+JSON')
        response = view(request, path='test.txt')
        '''
        assert False, response.content
        data = json.loads(response.content)
        data = data['collection']
        
        self.assertTrue('template' in data, str(view))
        self.assertTrue('error' in data)
        self.assertTrue('items' in data)
        self.assertEqual(len(data['items']), 1)
        
        #assert False, response.content
        '''

class AuthenticationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        return self.site.site_resource.auth_resource
    
    def test_get_detail(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        response = view(request)
        data = json.loads(response.content)
    
    def test_logout(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.delete('/')
        response = view(request)
        #assert False, response.content
        #data = json.loads(response.content)
        
        #assert False, str(data)

