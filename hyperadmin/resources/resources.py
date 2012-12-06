from copy import copy

from django import forms
from django.conf.urls.defaults import patterns
from django.utils.datastructures import SortedDict

from hyperadmin.hyperobjects import Link, LinkCollectionProvider, ResourceItem
from hyperadmin.states import ResourceState


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)


#TODO more like:
#resource.links.get_<name>()
#resource.links.get_item_<name>(item)
#resource.links.add_<name>(link) #goes to that items internal state
#resource.links.get_internal_<name>() #those belonging to this container
#resource.links.get_internal_item_<name>(item)

class BaseResource(object):
    resource_class = '' #hint to the client how this resource is used
    resource_item_class = ResourceItem
    state_class = ResourceState
    form_class = EmptyForm
    
    def __init__(self, resource_adaptor, site, parent_resource=None):
        self.resource_adaptor = resource_adaptor
        self.site = site
        self.parent = parent_resource
        #self.links = LinkCollectionProvider(self)
    '''
    def create_state(self):
        state = self.get_state_class()(**self.get_state_kwargs())
        return state
    
    def get_state_kwargs(self):
        return {
            'site_state': self.site_state,
            'data':self.get_state_data(),
        }
    
    def get_state_data(self):
        return {
            'resource': self
        }
    
    def fork_state(self, **kwargs):
        new_resource = copy(self)
        #TODO this is not ideal...
        for uncache in ('_endpoints', '_link_prototypes'):
            if hasattr(new_resource, uncache):
                delattr(new_resource, uncache)
        new_resource.state = self.state.copy()
        new_resource.state['resource'] = new_resource
        new_resource.state.update(kwargs)
        new_resource.links = LinkCollectionProvider(new_resource)
        return new_resource
    '''
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
    
    #TODO replace with get_url(url_name)
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
    
    def get_view_kwargs(self):
        return {'resource':self,
                'resource_site':self.site,}
                #'global_state':dict(self.site.state.global_state),} #store a snapshot of the current global state
    
    #def get_outbound_links(self):
    #    return self.get_breadcrumbs()
    
    def get_indexes(self, state):
        return {}
    
    def get_index(self, state, name):
        return self.get_indexes(state)[name]
    
    def get_index_query(self, state, name):
        raise NotImplementedError
    
    def get_item_url(self, item):
        return None
    
    def get_state_class(self):
        return self.state_class
    
    def get_form_class(self, state):
        return self.form_class
    
    def get_form_kwargs(self, state, item=None, **kwargs):
        if item is not None:
            kwargs.setdefault('instance', item.instance)
        return kwargs
    
    def generate_response(self, media_type, content_type, link, state):
        return media_type.serialize(content_type=content_type, link=link, state=state)
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)
    
    def get_absolute_url(self):
        raise NotImplementedError
    
    def get_resource_item_class(self):
        return self.resource_item_class
    
    def get_resource_item(self, instance, **kwargs):
        assert 'endpoint' in kwargs
        return self.get_resource_item_class()(instance=instance, **kwargs)
    
    def get_instances(self, state):
        return []
    
    #def get_resource_items(self):
    #    return [self.get_resource_item(instance) for instance in self.get_instances()]
    
    def get_resource_link_item(self):
        return None
    
    def get_resource_link(self, **kwargs):
        #TODO we want the endpoint state
        #assert False
        #return self.link_prototypes['list'].get_link(**kwargs)
        link_kwargs = {#'url':self.get_absolute_url(),
                       #'resource':self, #endpoint=endpoint
                       'rel':'self',
                       'prompt':self.get_prompt(),}
        link_kwargs.update(kwargs)
        return self.link_prototypes['list'].get_link(**kwargs)
        resource_link = Link(**link_kwargs)
        return resource_link
    
    def get_breadcrumb(self, state):
        return self.get_resource_link(rel='breadcrumb', endpoint=state.endpoint)
    
    def get_breadcrumbs(self, state):
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs(state)
        else:
            breadcrumbs = self.create_link_collection()
        breadcrumbs.append(self.get_breadcrumb(state))
        return breadcrumbs
    
    def get_prompt(self):
        return unicode(self)
    
    def get_item_prompt(self, item):
        return unicode(item.instance)
    
    #TODO deprecate
    def get_item_link(self, item, **kwargs):
        link_kwargs = {'url':item.get_absolute_url(),
                       'resource':self,
                       'rel':'item',
                       'prompt':item.get_prompt(),}
        link_kwargs.update(kwargs)
        item_link = Link(**link_kwargs)
        return item_link
    
    def get_namespaces(self, state):
        return dict()
    
    def get_item_namespaces(self, state, item):
        return dict()
    
    #def get_link_url(self, link):
    #    return self.state.get_link_url(link)
    
    def get_paginator_kwargs(self, state):
        return {}
