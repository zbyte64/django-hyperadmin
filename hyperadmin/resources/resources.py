from django import forms
from django.conf.urls.defaults import patterns
from django.utils.datastructures import SortedDict

from hyperadmin.hyperobjects import Link, ResourceItem, LinkCollectionProvider
from hyperadmin.resources.endpoints import BaseEndpoint


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)

class BaseResource(BaseEndpoint):
    resource_class = '' #hint to the client how this resource is used
    form_class = EmptyForm
    
    resource_adaptor = None
    parent = None
    
    def __init__(self, **kwargs):
        assert 'resource_adaptor' in kwargs
        self.links = LinkCollectionProvider(self)
        super(BaseResource, self).__init__(**kwargs)
        
        #if self.api_request:
        #    self.initialize_state()
        
        self.register_endpoints()
    
    def get_app_name(self):
        raise NotImplementedError
    app_name = property(get_app_name)
    
    def get_base_url_name(self):
        return self.app_name
    
    def register_endpoints(self):
        self.endpoints = SortedDict()
        for endpoint_cls, kwargs in self.get_view_endpoints():
            self.register_endpoint(endpoint_cls, **kwargs)
    
    def register_endpoint(self, endpoint_cls, **kwargs):
        kwargs = self.get_endpoint_kwargs(**kwargs)
        endpoint = endpoint_cls(**kwargs)
        self.endpoints[endpoint.name_suffix] = endpoint
    
    def get_endpoint_kwargs(self, **kwargs):
        kwargs.setdefault('resource', self)
        kwargs.setdefault('site', self.site)
        kwargs.setdefault('api_request', self.api_request)
        return kwargs
    
    def get_view_endpoints(self):
        """
        Returns a list of tuples containing
        (endpoint class, endpoint kwargs)
        """
        return []
    
    @property
    def link_prototypes(self):
        if not hasattr(self, '_link_prototypes'):
            self._link_prototypes = dict()
            for endpoint in self.endpoints.itervalues():
                for prototype in endpoint.get_link_prototypes().itervalues():
                    self._link_prototypes[prototype.name] = prototype
        return self._link_prototypes
    
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
    
    def get_resource_link_item(self):
        return None
    
    def get_url_name(self):
        return self.get_main_link_prototype().get_url_name()
    
    def get_main_link_name(self):
        return 'list'
    
    def get_breadcrumb(self):
        return self.get_link(rel='breadcrumb', link_factor='LO')
    
    def get_breadcrumbs(self):
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs()
        else:
            breadcrumbs = self.create_link_collection()
        breadcrumbs.append(self.get_breadcrumb())
        return breadcrumbs
    
    def get_paginator_kwargs(self):
        return {}
