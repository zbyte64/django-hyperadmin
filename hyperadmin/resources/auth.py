from django.conf.urls.defaults import patterns, url
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django import http

from hyperadmin import views

from resources import CRUDResource
from links import Link

class AuthenticationResourceForm(AuthenticationForm):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(AuthenticationResourceForm, self).__init__(**kwargs)
    
    def check_for_test_cookie(self):
        return
    
    def save(self, commit=True):
        assert self.request
       
        user = self.get_user()
        login(self.request, user)
        return user

class AuthResource(CRUDResource):
    form_class = AuthenticationResourceForm
    
    detail_view = views.AuthenticationResourceView
    
    def __init__(self, **kwargs):
        self._app_name = kwargs.pop('app_name', '-authentication')
        self._resource_name = kwargs.pop('resource_name', 'auth')
        kwargs.setdefault('resource_adaptor', None)
        super(AuthResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        return self._resource_name
    resource_name = property(get_resource_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_nonauthenticated_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.detail_view.as_view(**init)),
                name='authentication'),
        )
        return urlpatterns
    
    def get_form_class(self):
        return self.form_class
    
    def get_instance_url(self, instance):
        return self.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse('authentication')
    
    def get_outbound_links(self, instance=None):
        if instance:
            return []
        else:
            site_link = Link(url=self.reverse('index'), rel='breadcrumb', prompt='root')
            return [site_link]
    
    def form_valid(self, form):
        instance = form.save()
        next_url = self.site.site_resource.get_absolute_url()
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response
    
    def get_embedded_links(self, instance=None):
        return []

