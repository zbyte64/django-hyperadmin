from StringIO import StringIO

from django.utils import unittest
from django.utils.datastructures import MergeDict
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.core.files.base import ContentFile

from hyperadmin.resources.models import ModelResource, InlineModelResource
from hyperadmin.sites import ResourceSite
from hyperadmin.apirequests import InternalAPIRequest, NamespaceAPIRequest
from hyperadmin.endpoints import RootEndpoint

from common import GenericURLResolver, SuperUserRequestFactory, URLReverseMixin

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

class ResourceTestCase(URLReverseMixin, unittest.TestCase):
    def setUp(self):
        self.site = ResourceSite()
        self.site.register_builtin_media_types()
        
        self.user = User.objects.get_or_create(username='superuser', is_staff=True, is_active=True, is_superuser=True)[0]
        self.resource = self.register_resource()
        
        self.factory = SuperUserRequestFactory(user=self.user, HTTP_ACCEPT='text/html')
        
        self.resolver = GenericURLResolver(r'^', self.site.get_urls())
        
        self.patch_reverse(self.resolver)
    
    def tearDown(self):
        self.unpatch_reverse()
    
    def get_api_request(self, **kwargs):
        kwargs.setdefault('site', self.site)
        kwargs.setdefault('user', self.user)
        kwargs.setdefault('params', {})
        kwargs.setdefault('method', 'GET')
        kwargs.setdefault('payload', {})
        kwargs.setdefault('request', self.factory.get('/'))
        api_request = InternalAPIRequest(**kwargs)
        
        api_request.generate_response = MagicMock(return_value=HttpResponse())
        
        return api_request
    
    def register_resource(self):
        raise NotImplementedError

class ModelResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, UserResource, app_name='auth')
        return self.site.registry[User]
    
    def test_get_url_name(self):
        urlname = self.resource.get_url_name()
        self.assertEqual(urlname, 'admin_auth_user_resource')
    
    def test_get_list(self):
        api_request = self.get_api_request()
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertEqual(len(state.get_resource_items()), User.objects.count())
        
        links = state.links.get_filter_links()
        self.assertTrue(links, 'filter links are empty')
        
        links = state.links.get_breadcrumbs()
        self.assertTrue(links, 'breadcrumbs are empty')
        
        links = state.links.get_outbound_links()
        self.assertTrue(links, 'outbound links are empty')
    
    def test_get_detail(self):
        instance = self.user
        api_request = self.get_api_request(url_kwargs={'pk':instance.pk})
        endpoint = self.resource.endpoints['detail'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertEqual(len(state.get_resource_items()), 1)
        self.assertTrue(state.item)
        self.assertEqual(state.item.instance, instance)
        
        links = state.links.get_breadcrumbs()
        #TODO check for item breadcrumb
        self.assertTrue(links, 'breadcrumbs are empty')
        
        links = state.item.links.get_item_outbound_links()
        self.assertTrue(links, 'outbound links are empty')
    
    def test_negative_primary_key(self):
        instance = User.objects.create(pk=-1, username='anonymous', email='nowhere@nowhere.com')
        api_request = self.get_api_request(url_kwargs={'pk':instance.pk})
        endpoint = self.resource.endpoints['detail'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertEqual(len(state.get_resource_items()), 1)
    
    def test_internal_dispatch(self):
        instance = self.user
        response = self.resource.endpoints['detail'].internal_dispatch(url_kwargs={'pk':instance.pk})
        print response
    
    def test_post_list(self):
        update_data = {
            'username': 'normaluser',
            'email': 'z@z.com',
        }
        api_request = self.get_api_request(payload={'data': update_data}, method='POST')
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertTrue(link.form)
        self.assertTrue(link.form.errors)
    
    def test_post_detail(self):
        instance = self.user
        update_data = {
            'email': 'z@z.com',
        }
        api_request = self.get_api_request(url_kwargs={'pk':instance.pk}, payload={'data': update_data}, method='POST')
        endpoint = self.resource.endpoints['detail'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertTrue(link.form)
        self.assertTrue(link.form.errors)
        
        self.assertTrue(state.item)
        self.assertEqual(state.item.instance, instance)

class InlineModelResourceTestCase(ResourceTestCase):
    def setUp(self):
        super(InlineModelResourceTestCase, self).setUp()
        self.test_group = Group.objects.get_or_create(name='testgroup')[0]
        self.user.groups.add(self.test_group)
    
    def register_resource(self):
        self.site.register(User, UserResource, app_name='auth')
        self.user_resource = self.site.registry[User]
        return self.user_resource.inline_instances[0]
    
    def test_get_list(self):
        api_request = self.get_api_request(url_kwargs={'pk':self.user.pk})
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertEqual(len(state.get_resource_items()), self.user.groups.all().count())
    
    def test_namespaced_form(self):
        instance = self.user
        api_request = self.get_api_request(url_kwargs={'pk':self.user.pk})
        endpoint = self.user_resource.endpoints['detail'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertEqual(len(state.get_resource_items()), 1)
        self.assertTrue(state.item)
        self.assertEqual(state.item.instance, instance)
        
        #self.skipTest("Need to patch namespace's api_request's reverse")
        item_namespaces = state.item.get_namespaces()
        self.assertTrue(item_namespaces)
        namespace = item_namespaces.values()[0]
        self.assertTrue(namespace.link.get_absolute_url())
            
        inline_items = namespace.state.get_resource_items()
        self.assertTrue(inline_items)
        item = inline_items[0]
        inline_link = item.get_outbound_link()
        self.assertEqual(inline_link.get_link_factor(), 'LO')
        self.assertTrue(inline_link.get_absolute_url())
        
        edit_link = inline_link.follow()
        self.assertEqual(edit_link.method, 'POST', str(edit_link.endpoint))
    
    #TODO
    def test_get_detail(self):
        return
        instance = self.user
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.detail_view.as_view(**view_kwargs)
        request = self.factory.get('/')
        view(request, pk=instance.pk)
        
        media_type, response_type, link = self.site.generate_response.call_args[0]
            
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
        
        media_type, response_type, link = self.site.generate_response.call_args[0]
    
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
        
        media_type, response_type, link = self.site.generate_response.call_args[0]

class SiteResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, ModelResource, app_name='auth')
        return self.site.directory_resource
    
    '''
    def test_index(self):
        factory = SuperUserRequestFactory(user=self.user)
        view_kwargs = self.resource.get_view_kwargs()
        view = self.resource.list_view.as_view(**view_kwargs)
        request = factory.get('/')
        response = view(request)
    '''
    
    def test_get_list(self):
        api_request = self.get_api_request()
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertTrue(state.get_resource_items())
    
    def test_url_stability_after_fork(self):
        api_request = self.get_api_request()
        bound_site = self.site.fork(api_request=api_request)
        print self.site.get_urls()
        print api_request.get_site().get_urls()
        self.assertEqual(str(self.site.get_urls()), str(bound_site.get_urls()))
        self.assertEqual(str(self.site.get_urls()), str(api_request.get_site().get_urls()))

class ApplicationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        self.site.register(User, ModelResource, app_name='auth')
        return self.site.applications['auth']
    
    def test_get_list(self):
        api_request = self.get_api_request()
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
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
        
        api_request = self.get_api_request()
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        #list view sets the state here
        #self.assertEqual(len(state.get_resource_items()), 1)
    
    def test_get_detail(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        
        api_request = self.get_api_request(url_kwargs={'path':'test.txt'})
        endpoint = self.resource.endpoints['detail'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        #with state.push_session(self.popped_states):
        self.assertEqual(len(state.get_resource_items()), 1)
        
        item = state.get_resource_items()[0]
        
        self.assertEqual(item.instance.url, '/media/test.txt')
    
    def test_post_list(self):
        update_data = {
            'name': 'test.txt',
            'upload': StringIO('test2'),
        }
        update_data['upload'].name = 'test.txt'
        
        api_request = self.get_api_request(payload={'data':update_data}, method='POST')
        endpoint = self.resource.endpoints['list'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        #self.assertEqual(link.rel, 'item')
        #if there was an error:
        #self.assertTrue(link.form)
        #self.assertTrue(link.form.errors)
    
    def test_post_detail(self):
        self.resource.resource_adaptor.save('test.txt', ContentFile('foobar'))
        update_data = {
            'name': 'test.txt',
            'upload': StringIO('test2'),
        }
        update_data['upload'].name = 'test.txt'
        api_request = self.get_api_request(url_kwargs={'path':'test.txt'}, payload={'data':update_data}, method='POST')
        endpoint = self.resource.endpoints['detail'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        self.assertEqual(link.rel, 'update')
        #if not rel
        #self.assertTrue(link.form.errors)

class AuthenticationResourceTestCase(ResourceTestCase):
    def register_resource(self):
        return self.site.auth_resource
    
    def test_get_detail(self):
        api_request = self.get_api_request(request=self.factory.get('/'))
        endpoint = self.resource.endpoints['login'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        #with state.push_session(self.popped_states):
        self.assertTrue(state['authenticated'])
        self.assertTrue(state.links.get_outbound_links()) #TODO logout link?
    
    def test_restful_logout(self):
        api_request = self.get_api_request(method='DELETE', request=self.factory.get('/'))
        endpoint = self.resource.endpoints['login'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        #TODO it seems we aren't tracking test states properly
        #with state.push_session(self.popped_states):
        #    self.assertFalse(state['authenticated'])
    
    def test_logout(self):
        api_request = self.get_api_request(method='POST', request=self.factory.get('/'))
        endpoint = self.resource.endpoints['logout'].fork(api_request=api_request)
        response = endpoint.dispatch_api(api_request)
        
        call_kwargs = api_request.generate_response.call_args[1]
        link = call_kwargs['link']
        state = call_kwargs['state']
        
        #TODO it seems we aren't tracking test states properly
        #with state.push_session(self.popped_states):
        #    self.assertFalse(state['authenticated'])

