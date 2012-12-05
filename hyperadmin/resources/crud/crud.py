from django.core.paginator import Paginator

from hyperadmin.resources.resources import BaseResource
from hyperadmin.resources.indexes import PrimaryIndex
from hyperadmin.resources.crud.changelist import ChangeList
from hyperadmin.resources.crud.hyperobjects import ListResourceItem
from hyperadmin.resources.crud.endpoints import ListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint


class CRUDResource(BaseResource):
    resource_class = 'crudresource'
    
    ordering = None
    list_display = ('__str__',) #TODO should list all field by default
    list_resource_item_class = ListResourceItem
    paginator_class = Paginator
    changelist_class = ChangeList
    
    #TODO support the following:
    actions = []
    
    list_view = None
    add_view = None
    detail_view = None
    delete_view = None
    form_class = None
    
    def get_resource_name(self):
        raise NotImplementedError
    resource_name = property(get_resource_name)
    
    def get_base_url_name(self):
        return '%s_%s_' % (self.app_name, self.resource_name)
    
    def get_prompt(self):
        return self.resource_name
    
    def get_view_endpoints(self):
        endpoints = super(CRUDResource, self).get_view_endpoints()
        endpoints.extend([
            ListEndpoint(resource=self),
            CreateEndpoint(resource=self),
            DetailEndpoint(resource=self),
            DeleteEndpoint(resource=self),
        ])
        return endpoints
    
    def get_absolute_url(self):
        return self.link_prototypes['list'].get_url()
    
    def get_item_url(self, item):
        return self.link_prototypes['update'].get_url(item=item)
    
    def has_add_permission(self):
        return True
    
    def has_change_permission(self, item=None):
        return True
    
    def has_delete_permission(self, item=None):
        return True
    
    def get_indexes(self, state):
        return {'primary':PrimaryIndex('primary', self, state, self.get_index_query(state, 'primary'))}
    
    def get_index_query(self, state, name):
        return self.get_primary_query(state)
    '''
    def get_index_queries(self):
        links = self.create_link_collection()
        if self.state.get('changelist', None):
            links += self.get_changelist_links()
        return links
    '''
    def get_item_breadcrumb(self, item):
        return self.get_item_link(item, rel='breadcrumb')
    
    def get_list_resource_item_class(self):
        return self.list_resource_item_class
    
    def get_list_resource_item(self, instance, **kwargs):
        return self.get_list_resource_item_class()(instance=instance, **kwargs)
    
    def get_instances(self, state):
        '''
        Returns a set of native objects for a given state
        '''
        if 'page' in state:
            return state['page'].object_list
        if state.has_view_class('change_form'):
            return []
        return self.get_primary_query(state)
    
    def get_resource_items(self, state):
        instances = self.get_instances(state)
        if state.has_view_class('change_list'):
            return [self.get_list_resource_item(instance) for instance in instances]
        return [self.get_resource_item(instance) for instance in instances]
    
    def get_primary_query(self, state, **kwargs):
        return self.resource_adaptor.objects.all()
    
    def get_ordering(self):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)
    '''
    def get_changelist_kwargs(self, **kwargs):
        params = {'resource': self,
                  'state':self.state,}
        params.update(kwargs)
        return params
    
    def get_changelist_class(self):
        return self.changelist_class
    
    def get_changelist(self, **kwargs):
        changelist_class = self.get_changelist_class()
        kwargs = self.get_changelist_kwargs(**kwargs)
        changelist = changelist_class(**kwargs)
        changelist.detect_sections()
        changelist.populate_state()
        return changelist
    
    def get_changelist_links(self):
        return self.state['changelist'].get_links()
    '''
    def get_paginator_class(self):
        return self.paginator_class
    
    def get_paginator(self, index, **kwargs):
        return self.get_paginator_class()(index, **kwargs)
    
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

