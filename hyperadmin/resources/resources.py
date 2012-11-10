from copy import copy, deepcopy

from django import forms
from django.conf.urls.defaults import patterns

from hyperadmin.hyperobjects import Link, ResourceItem, ResourceState, global_state


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)

class BaseResource(object):
    resource_class = '' #hint to the client how this resource is used
    resource_item_class = ResourceItem
    state_class = ResourceState
    form_class = EmptyForm
    donot_copy = ['state'] #indicates which attributes should not be deepcopied
    
    def __init__(self, resource_adaptor, site_state, parent_resource=None):
        self.resource_adaptor = resource_adaptor
        self.site_state = site_state
        self.parent = parent_resource
        self.state = self.create_state()
    
    @property
    def site(self):
        return self.state.site
    
    def create_state(self):
        state = self.get_state_class()(**self.get_state_kwargs())
        return state
    
    def get_state_kwargs(self):
        return {
            'resource': self,
            'meta': {},
            'substates': [self.site_state],
        }
    
    def fork_state(self, **kwargs):
        new_resource = copy(self)
        new_resource.state = self.state.fork(resource=new_resource, data=kwargs)
        return new_resource
    
    def __deepcopy__(self, memo):
        for attr in self.donot_copy:
            if hasattr(self, attr):
                val = getattr(self, attr)
                memo[id(val)] = val
        
        new = copy(self)
        memo[id(self)] = new
        new.__dict__.update(deepcopy(self.__dict__, memo))
        new.state = new.create_state()
        memo[id(self.state)] = new.state
        return new
    
    def get_app_name(self):
        raise NotImplementedError
    app_name = property(get_app_name)
    
    def get_urls(self):
        urlpatterns = self.get_extra_urls()
        return urlpatterns
    
    def get_extra_urls(self):
        return patterns('',)
    
    def urls(self):
        return self.get_urls(), self.app_name, None
    urls = property(urls)
    
    def reverse(self, name, *args, **kwargs):
        return self.state.reverse(name, *args, **kwargs)
    
    def as_view(self, view, cacheable=False):
        return self.site.as_view(view, cacheable)
    
    def as_nonauthenticated_view(self, view, cacheable=False):
        return self.site.as_nonauthenticated_view(view, cacheable)
    
    def get_view_kwargs(self):
        return {'resource':self,
                'resource_site':self.site,
                'global_state':dict(global_state),} #store a snapshot of the current global state
    
    def get_embedded_links(self):
        return []
    
    def get_item_embedded_links(self, item):
        return []
    
    def get_outbound_links(self):
        return self.get_breadcrumbs()
    
    def get_item_outbound_links(self, item):
        return []
    
    def get_indexes(self):
        return {}
    
    def get_index_query(self, name):
        raise NotImplementedError
    
    def get_index_queries(self):
        return []
    
    def get_templated_queries(self):
        return []
    
    def get_item_templated_queries(self, item):
        return []
    
    #TODO find a better name
    def get_ln_links(self):
        return []
    
    #TODO find a better name
    def get_item_ln_links(self, item):
        return []
    
    #TODO find a better name
    def get_idempotent_links(self):
        return []
    
    #TODO find a better name
    def get_item_idempotent_links(self, item):
        return []
    
    def get_item_url(self, item):
        return None
    
    def get_state_class(self):
        return self.state_class
    
    def get_form_class(self):
        return self.form_class
    
    def get_form_kwargs(self, item=None, **kwargs):
        if item is not None:
            kwargs.setdefault('instance', item.instance)
        return kwargs
    
    def generate_response(self, media_type, content_type, link):
        return media_type.serialize(content_type=content_type, link=link, state=self.state)
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)
    
    def get_child_resource_links(self):
        return []
    
    def get_absolute_url(self):
        raise NotImplementedError
    
    def get_resource_item_class(self):
        return self.resource_item_class
    
    def get_resource_item(self, instance, **kwargs):
        return self.get_resource_item_class()(resource=self, instance=instance, **kwargs)
    
    def get_resource_items(self):
        return []
    
    def get_resource_link_item(self):
        return None
    
    def get_resource_link(self, **kwargs):
        link_kwargs = {'url':self.get_absolute_url(),
                       'resource':self,
                       'rel':'self',
                       'prompt':self.get_prompt(),}
        link_kwargs.update(kwargs)
        resource_link = Link(**link_kwargs)
        return resource_link
    
    def get_breadcrumb(self):
        return self.get_resource_link(rel='breadcrumb')
    
    def get_breadcrumbs(self):
        breadcrumbs = []
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs()
        breadcrumbs.append(self.get_breadcrumb())
        return breadcrumbs
    
    def get_prompt(self):
        return unicode(self)
    
    def get_item_prompt(self, item):
        return unicode(item.instance)
    
    def get_item_link(self, item, **kwargs):
        link_kwargs = {'url':item.get_absolute_url(),
                       'resource':self,
                       'rel':'item',
                       'prompt':item.get_prompt(),}
        link_kwargs.update(kwargs)
        item_link = Link(**link_kwargs)
        return item_link
    
    def get_namespaces(self):
        return dict()
    
    def get_item_namespaces(self, item):
        return dict()
    
    def get_link_url(self, link):
        return self.state.get_link_url(link)

