from django import forms
from django.conf.urls.defaults import patterns
from django.utils.datastructures import SortedDict

from hyperadmin.endpoints import BaseEndpoint
from hyperadmin.resources.hyperobjects import ResourceItem


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)

class BaseResource(BaseEndpoint):
    resource_class = '' #hint to the client how this resource is used
    form_class = EmptyForm
    resource_item_class = ResourceItem
    
    resource_adaptor = None
    
    def __init__(self, **kwargs):
        assert 'resource_adaptor' in kwargs
        super(BaseResource, self).__init__(**kwargs)
    
    @property
    def resource(self):
        #endpoints have a resource attribute
        return self
    
    def post_register(self):
        self.register_endpoints()
        super(BaseResource, self).post_register()
    
    def get_app_name(self):
        return None
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        raise NotImplementedError
    resource_name = property(get_resource_name)
    
    def get_base_url_name(self):
        if self.app_name:
            return '%s_%s_' % (self.app_name, self.resource_name)
        else:
            return '%s_' % self.resource_name
    
    def create_link_prototypes(self):
        link_prototypes = super(BaseResource, self).create_link_prototypes()
        
        for endpoint in self.endpoints.itervalues():
            link_prototypes.update(endpoint.link_prototypes)
        
        return link_prototypes
    
    def register_endpoints(self):
        self.endpoints = SortedDict()
        for endpoint_cls, kwargs in self.get_view_endpoints():
            self.register_endpoint(endpoint_cls, **kwargs)
    
    def register_endpoint(self, endpoint_cls, **kwargs):
        kwargs = self.get_endpoint_kwargs(**kwargs)
        endpoint = endpoint_cls(**kwargs)
        self.endpoints[endpoint.get_name_suffix()] = endpoint
    
    def get_endpoint_kwargs(self, **kwargs):
        kwargs.setdefault('parent', self)
        kwargs.setdefault('site', self._site)
        kwargs.setdefault('api_request', self.api_request)
        return kwargs
    
    def get_view_endpoints(self):
        """
        Returns a list of tuples containing
        (endpoint class, endpoint kwargs)
        """
        return []
    
    def get_view_kwargs(self):
        """
        :rtype: dict
        """
        return {}
    
    def get_urls(self):
        urlpatterns = self.get_extra_urls()
        urls = [endpoint.get_url_object() for endpoint in self.endpoints.itervalues()]
        urlpatterns += patterns('', *urls)
        return urlpatterns
    
    def get_extra_urls(self):
        return patterns('',)
    
    def urls(self):
        return self.get_urls(), self.app_name, None
    urls = property(urls)
    
    def reverse(self, name, *args, **kwargs):
        return self.site.reverse(name, *args, **kwargs)
    
    def api_permission_check(self, request):
        return self.site.api_permission_check(request)
    
    def get_state_data(self):
        data = super(BaseResource, self).get_state_data()
        data.update({'resource_name': getattr(self, 'resource_name', None),
                     'app_name': self.app_name,})
        return data
    
    def get_indexes(self):
        return {}
    
    def get_index(self, name):
        return self.get_indexes()[name]
    
    def get_index_query(self, name):
        raise NotImplementedError
    
    def get_item_url(self, item):
        return None
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)
    
    def get_absolute_url(self):
        return self.get_url()
    
    def get_url(self, **kwargs):
        return self.get_main_link_prototype().get_url(**kwargs)
    
    def get_resource_link_item(self):
        return None
    
    def get_url_name(self):
        return self.get_base_url_name() + 'resource'
    
    def get_main_link_name(self):
        return 'list'
    
    def get_breadcrumb(self):
        bread = self.create_link_collection()
        bread.add_link('list', rel='breadcrumb', link_factor='LO', prompt=self.get_prompt())
        return bread
    
    def get_breadcrumbs(self):
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs()
        else:
            breadcrumbs = self.create_link_collection()
        breadcrumbs.extend(self.get_breadcrumb())
        return breadcrumbs
    
    def get_paginator_kwargs(self):
        return {}
