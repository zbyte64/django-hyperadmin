from StringIO import StringIO

from django.utils import unittest
from django.contrib.auth.models import User, Group
from django.core.files.base import ContentFile

from hyperadmin.resources.models.models import ModelResource, InlineModelResource
from hyperadmin.sites import ResourceSite

from common import GenericURLResolver, SuperUserRequestFactory

from mock import MagicMock


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
        self.resource.generate_response = MagicMock()
        self.factory = SuperUserRequestFactory(user=self.user, HTTP_ACCEPT='text/html')
        
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
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        
        self.assertEqual(len(state.get_resource_items()), User.objects.count())
        
    
    def test_get_detail(self):
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        view(request, pk=instance.pk)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        
        self.assertEqual(len(state.get_resource_items()), 1)
        self.assertTrue(state.item)
        self.assertEqual(state.item.instance, instance)
    
    def test_put_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        update_data = {
            'username': 'normaluser',
            'email': 'z@z.com',
        }
        request = self.factory.put('/', update_data)
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        
        self.assertTrue(link.form)
        self.assertTrue(link.form.errors)
    
    def test_post_detail(self):
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        update_data = {
            'email': 'z@z.com',
        }
        request = self.factory.post('/', update_data)
        view(request, pk=instance.pk)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        
        self.assertTrue(link.form)
        self.assertTrue(link.form.errors)
        
        self.assertTrue(state.item)
        self.assertEqual(state.item.instance, instance)

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
        view(request, pk=self.user.pk)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        
        self.assertEqual(len(state.get_resource_items()), self.user.groups.all().count())
    
    #TODO
    def test_get_detail(self):
        return
        group = Group.objects.get_or_create(name='testgroup')[0]
        self.user.groups.add(group)
        
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        view(request, pk=instance.pk)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
            
    #TODO
    def test_post_list(self):
        return
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        update_data = {
            'username': 'normaluser',
            'email': 'z@z.com',
        }
        request = self.factory.post('/', update_data)
        view(request, pk=instance.pk)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
    
    #TODO
    def test_post_detail(self):
        return
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        update_data = {
            'email': 'z@z.com',
        }
        request = self.factory.post('/', update_data)
        view(request, pk=instance.pk)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]

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
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        
        self.assertTrue(state.get_resource_items())

class ApplicationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, ModelResource)
        return self.site.applications.values()[0]
    
    def test_get_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        view(request)
        
        media_type, response_type, link, = self.resource.generate_response.call_args[0]
        state = link.resource.state
        
        self.assertTrue(state.get_resource_items())

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
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        #list view sets the state here
        #self.assertEqual(len(state.get_resource_items()), 1)
    
    def test_get_detail(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        view(request, path='test.txt')
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        self.assertEqual(len(state.get_resource_items()), 1)
        
        item = state.get_resource_items()[0]
        
        self.assertEqual(item.instance.url, '/media/test.txt')
    
    def test_put_list(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        update_data = {
            'name': 'test.txt',
            'upload': StringIO('test2'),
        }
        update_data['upload'].name = 'test.txt'
        request = self.factory.put('/', update_data)
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        
        #self.assertEqual(link.rel, 'item')
        #if there was an error:
        #self.assertTrue(link.form)
        #self.assertTrue(link.form.errors)
    
    def test_post_detail(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        update_data = {
            'name': 'test.txt',
            'upload': StringIO('test2'),
        }
        update_data['upload'].name = 'test.txt'
        request = self.factory.post('/', update_data)
        view(request, path='test.txt')
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        
        self.assertEqual(link.rel, 'item')
        #if not rel
        #self.assertTrue(link.form.errors)

class AuthenticationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        return self.site.site_resource.auth_resource
    
    def test_get_detail(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        self.assertTrue(state.get_embedded_links()) #TODO logout link?
        self.assertTrue(state['authenticated'])
    
    def test_logout(self):
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.delete('/')
        view(request)
        
        media_type, response_type, link = self.resource.generate_response.call_args[0]
        state = link.resource.state
        self.assertFalse(state['authenticated'])

