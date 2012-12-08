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
    resource_item_class = ResourceItem
    form_class = EmptyForm
    
    resource_adaptor = None
    site = None
    parent = None
    
    def __init__(self, **kwargs):
        assert 'resource_adaptor' in kwargs
        self.links = LinkCollectionProvider(self)
        super(BaseResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        raise NotImplementedError
    app_name = property(get_app_name)
    
    def get_base_url_name(self):
        return self.app_name
    
    def get_view_endpoints(self):
        """
        Returns a list of dictionaries containing the following elements:
        
        * url: relative regex url
        * view: the view object
        * name: name for urlresolver
        """
        return []
    
    @property
    def endpoints(self):
        if not hasattr(self, '_endpoints'):
            self._endpoints = SortedDict()
            for endpoint in self.get_view_endpoints():
                assert hasattr(endpoint, 'name_suffix')
                self._endpoints[endpoint.name_suffix] = endpoint
        return self._endpoints
    
    @property
    def link_prototypes(self):
        if not hasattr(self, '_link_prototypes'):
            self._link_prototypes = dict()
            for endpoint in self.endpoints.itervalues():
                self._link_prototypes.update(endpoint.get_links())
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
    
    def get_form_class(self):
        return self.form_class
    
    def get_form_kwargs(self, item=None, **kwargs):
        if item is not None:
            kwargs.setdefault('instance', item.instance)
        return kwargs
    
    def get_view_kwargs(self):
        return {
            'resource': self,
            'resource_site': self.site,
        }
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)
    
    def get_absolute_url(self):
        raise NotImplementedError
    
    def get_resource_item_class(self):
        return self.resource_item_class
    
    def get_resource_item(self, instance, **kwargs):
        kwargs.setdefault('endpoint', self)
        return self.get_resource_item_class()(instance=instance, **kwargs)
    
    def get_instances(self):
        return []
    
    def get_resource_link_item(self):
        return None
    
    def get_link(self, **kwargs):
        #must include endpoint in kwargs
        link_kwargs = {'rel':'self',
                       'prompt':self.get_prompt(),}
        link_kwargs.update(kwargs)
        return self.link_prototypes['list'].get_link(**link_kwargs)
    
    def get_breadcrumb(self):
        return self.get_link(rel='breadcrumb')
    
    def get_breadcrumbs(self):
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs()
        else:
            breadcrumbs = self.create_link_collection()
        breadcrumbs.append(self.get_breadcrumb())
        return breadcrumbs
    
    def get_prompt(self):
        return unicode(self)
    
    def get_item_prompt(self, item):
        return unicode(item.instance)
    
    #TODO deprecate
    def get_item_link(self, item, **kwargs):
        link_kwargs = {'url':item.get_absolute_url(),
                       'endpoint':self,
                       'rel':'item',
                       'prompt':item.get_prompt(),}
        link_kwargs.update(kwargs)
        item_link = Link(**link_kwargs)
        return item_link
    
    def get_namespaces(self):
        return dict()
    
    def get_item_namespaces(self, item):
        return dict()
    
    #def get_link_url(self, link):
    #    return self.state.get_link_url(link)
    
    def get_paginator_kwargs(self):
        return {}
