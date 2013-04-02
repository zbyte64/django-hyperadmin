from django.core.paginator import Paginator

from hyperadmin.indexes import PrimaryIndex
from hyperadmin.resources.resources import BaseResource
from hyperadmin.resources.crud.hyperobjects import ListResourceItem
from hyperadmin.resources.crud.endpoints import ListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint


class CRUDResource(BaseResource):
    resource_class = 'crudresource'
    
    ordering = None
    list_display = ('__str__',) #TODO should list all field by default
    list_resource_item_class = ListResourceItem
    paginator_class = Paginator
    
    #TODO support the following:
    actions = []
    
    form_class = None
    
    list_endpoint = (ListEndpoint, {})
    create_endpoint = (CreateEndpoint, {})
    detail_endpoint = (DetailEndpoint, {})
    delete_endpoint = (DeleteEndpoint, {})
    
    def get_view_endpoints(self):
        endpoints = super(CRUDResource, self).get_view_endpoints()
        endpoints.extend([
            self.list_endpoint,
            self.create_endpoint,
            self.delete_endpoint,
            self.detail_endpoint,
        ])
        return endpoints
    
    def get_absolute_url(self):
        return self.link_prototypes['list'].get_url()
    
    def get_item_url(self, item):
        if self.has_update_permission(item):
            return self.link_prototypes['update'].get_url(item=item)
        return self.link_prototypes['detail'].get_url(item=item)
    
    def get_item_link(self, item, **kwargs):
        if self.has_update_permission(item):
            return self.link_prototypes['update'].get_link(item=item, **kwargs)
        return self.link_prototypes['detail'].get_link(item=item, **kwargs)
    
    def has_permission(self, perm, **kwargs):
        func_name = 'has_%s_permission' % perm
        if hasattr(self, func_name):
            return getattr(self, func_name)(**kwargs)
        return False
    
    def has_create_permission(self):
        return True
    
    def has_update_permission(self, item=None):
        return True
    
    def has_delete_permission(self, item=None):
        return True
    
    def on_create_success(self, item):
        '''
        Called when an item has been successfully created.
        Fires off the create event.
        May return a link.
        '''
        self.emit_event(event='create', item_list=[item])
        return None
    
    def on_update_success(self, item):
        '''
        Called when an item has been successfully updated.
        Fires off the update event.
        May return a link.
        '''
        self.emit_event(event='update', item_list=[item])
        return None
    
    def on_delete_success(self, item):
        '''
        Called when an item has been successfully deleted.
        Fires off the delete event.
        May return a link.
        '''
        self.emit_event(event='delete', item_list=[item])
        return None
    
    def get_indexes(self):
        return {'primary':PrimaryIndex('primary', self)}
    
    def get_index_query(self, name):
        return self.get_primary_query()
    
    def get_item_breadcrumb(self, item):
        return self.get_item_link(item, rel='breadcrumb', link_factor='LO')
    
    def get_list_resource_item_class(self):
        return self.list_resource_item_class
    
    def get_list_resource_item(self, instance, **kwargs):
        kwargs.setdefault('endpoint', self)
        return self.get_list_resource_item_class()(instance=instance, **kwargs)
    
    def get_instances(self):
        '''
        Returns a set of native objects for a given state
        '''
        if 'page' in self.state:
            return self.state['page'].object_list
        if self.state.has_view_class('change_form'):
            return []
        return self.get_primary_query()
    
    def get_resource_items(self):
        instances = self.get_instances()
        if self.state.has_view_class('change_list'):
            return [self.get_list_resource_item(instance) for instance in instances]
        return [self.get_resource_item(instance) for instance in instances]
    
    def get_primary_query(self, **kwargs):
        return self.resource_adaptor.objects.all()
    
    def get_ordering(self):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)
    
    def get_paginator_class(self):
        return self.paginator_class
    
    def get_paginator_kwargs(self):
        return {'per_page':getattr(self, 'list_per_page', 50),}
    
    def get_paginator(self, index, **kwargs):
        return self.get_paginator_class()(index, **kwargs)
    
    def get_outbound_links(self):
        links = self.create_link_collection()
        links.add_link('list', link_factor='LO')
        links.add_link('create', link_factor='LO')
        return links
    
    def get_actions(self, request):
        actions = self.site.get_actions(request)
        for func in self.actions:
            if isinstance(func, basestring):
                #TODO register as new func in urls, create link for it
                func = getattr(self, func)
            assert callable(func)
            name = func.__name__
            description = getattr(func, 'short_description', name.replace('_', ' '))
            #sorteddictionary
            actions[name] = (func, name, description)
        return actions
    
    def get_action(self, request, action):
        actions = self.get_actions(request)
        return actions[action]
    
    def __unicode__(self):
        return u'CRUD Resource: %s/%s' % (self.app_name, self.resource_name)
    
    def get_form_kwargs(self, **kwargs):
        '''
        CRUD forms are assumed to operate on the active item.
        This inserts the active instance into the form kwargs.
        '''
        if self.state.item:
            kwargs.setdefault('instance', self.state.item.instance)
        return super(CRUDResource, self).get_form_kwargs(**kwargs)
