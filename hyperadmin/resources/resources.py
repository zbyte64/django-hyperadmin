from django import forms
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import slugify

from hyperadmin.endpoints import VirtualEndpoint, GlobalSiteMixin
from hyperadmin.resources.hyperobjects import ResourceItem
from hyperadmin.signals import resource_event


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)

class BaseResource(GlobalSiteMixin, VirtualEndpoint):
    '''
    A collection of endpoints representing a particular service
    '''
    resource_class = '' #hint to the client how this resource is used
    form_class = EmptyForm
    resource_item_class = ResourceItem
    name_suffix = 'resource'
    
    resource_adaptor = None
    '''The object representing the resource connection. Typically passed in during construction'''
    
    def __init__(self, **kwargs):
        assert 'resource_adaptor' in kwargs
        self._installed_endpoints = SortedDict()
        super(BaseResource, self).__init__(**kwargs)
    
    def fork(self, **kwargs):
        kwargs.setdefault('_installed_endpoints', self._installed_endpoints)
        return super(BaseResource, self).fork(**kwargs)
    
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
    
    
    def get_resource_slug(self):
        """
        Return the slug of this resource.
        Provides the return value of the `resource_slug` property.
        """
        if hasattr(self, '_resource_slug'):
            return self._resource_slug
        return slugify(self.get_resource_name())
    
    def _get_resource_slug(self):
        return self.get_resource_slug()
    
    def _set_resource_slug(self, slug):
        self._resource_slug = slug
    
    resource_slug = property(_get_resource_slug, _set_resource_slug, None, 'Set or get the slug of the resource')
    
    def get_prompt(self):
        return self.resource_name
    
    def get_base_url_name_suffix(self):
        if self.base_url_name_suffix is None:
            return self.resource_slug
        return self.base_url_name_suffix
    
    def register_endpoints(self):
        self.endpoints = SortedDict()
        for endpoint_cls, kwargs in self.get_view_endpoints():
            self._register_endpoint(endpoint_cls, **kwargs)
        for key, endpoint in self._installed_endpoints.iteritems():
            self.endpoints[key] = self.fork(**self.get_endpoint_kwargs())
    
    def register_endpoint(self, endpoint_cls, **kwargs):
        endpoint = self._register_endpoint(endpoint_cls, **kwargs)
        self._installed_endpoints[endpoint.get_name_suffix()] = endpoint
        return endpoint
    
    def _register_endpoint(self, endpoint_cls, **kwargs):
        kwargs = self.get_endpoint_kwargs(**kwargs)
        endpoint = endpoint_cls(**kwargs)
        self.endpoints[endpoint.get_name_suffix()] = endpoint
        return endpoint
    
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
    
    def get_index_endpoint(self):
        return self.endpoints['list']
    
    def get_breadcrumb(self):
        bread = self.create_link_collection()
        bread.add_link(self.get_index_endpoint(), rel='breadcrumb', link_factor='LO', prompt=self.get_prompt())
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
    
    def emit_event(self, event, item_list=None):
        """
        Fires of the `resource_event` signal
        """
        sender = '%s!%s' % (self.get_url_name(), event)
        if item_list is None:
            item_list = self.get_resource_items()
        resource_event.send(sender=sender, resource=self, event=event, item_list=item_list)
