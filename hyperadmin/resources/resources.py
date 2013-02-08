from django import forms
from django.conf.urls.defaults import patterns
from django.utils.datastructures import SortedDict

from hyperadmin.endpoints import VirtualEndpoint, GlobalSiteMixin
from hyperadmin.resources.hyperobjects import ResourceItem


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)

class BaseResource(GlobalSiteMixin, VirtualEndpoint):
    resource_class = '' #hint to the client how this resource is used
    form_class = EmptyForm
    resource_item_class = ResourceItem
    name_suffix = 'resource'
    
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
        """
        Return the application name of this resource.
        Provides the return value of the `app_name` property.
        """
        return getattr(self, '_app_name', None)
    
    def _get_app_name(self):
        return self.get_app_name()
    
    def _set_app_name(self, name):
        self._app_name = name
    
    app_name = property(_get_app_name, _set_app_name, None, 'Set or get the application name')
    
    def get_resource_name(self):
        """
        Return the name of this resource.
        Provides the return value of the `resource_name` property.
        """
        return self._resource_name
    
    def _get_resource_name(self):
        return self.get_resource_name()
    
    def _set_resource_name(self, name):
        self._resource_name = name
    
    resource_name = property(_get_resource_name, _set_resource_name, None, 'Set or get the name of the resource')
    
    def get_prompt(self):
        return self.resource_name
    
    def get_base_url_name_suffix(self):
        if self.base_url_name_suffix is None:
            return self.resource_name
        return self.base_url_name_suffix
    
    def register_endpoints(self):
        self.endpoints = SortedDict()
        for endpoint_cls, kwargs in self.get_view_endpoints():
            self.register_endpoint(endpoint_cls, **kwargs)
    
    def register_endpoint(self, endpoint_cls, **kwargs):
        kwargs = self.get_endpoint_kwargs(**kwargs)
        endpoint = endpoint_cls(**kwargs)
        self.endpoints[endpoint.get_name_suffix()] = endpoint
    
    def get_view_endpoints(self):
        """
        Returns a list of tuples containing
        (endpoint class, endpoint kwargs)
        """
        return []
    
    def get_children_endpoints(self):
        return self.endpoints.values()
    
    def reverse(self, name, *args, **kwargs):
        return self.site.reverse(name, *args, **kwargs)
    
    def api_permission_check(self, request):
        return self.site.api_permission_check(request)
    
    def get_state_data(self):
        data = super(BaseResource, self).get_state_data()
        data.update({'resource_name': self.resource_name,
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
