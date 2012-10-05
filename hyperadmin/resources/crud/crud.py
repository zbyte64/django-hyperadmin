from django.conf.urls.defaults import patterns, url
from django.core.paginator import Paginator

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.resources import BaseResource
from hyperadmin.resources.crud.changelist import ChangeList
from hyperadmin.resources.crud.hyperobjects import ListResourceItem


class CRUDResource(BaseResource):
    resource_class = 'crudresource'
    donot_copy = BaseResource.donot_copy + ['resource_adaptor']
    
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
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        base_name = self.get_base_url_name()
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='%slist' % base_name),
            url(r'^add/$',
                wrap(self.add_view.as_view(**init)),
                name='%sadd' % base_name),
            url(r'^(?P<pk>\w+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%sdetail' % base_name),
            url(r'^(?P<pk>\w+)/delete/$',
                wrap(self.delete_view.as_view(**init)),
                name='%sdelete' % base_name),
        )
        return urlpatterns
    
    def get_add_url(self):
        return self.reverse('%sadd' % self.get_base_url_name())
    
    def get_item_url(self, item):
        return self.reverse('%sdetail' % self.get_base_url_name(), pk=item.instance.pk)
    
    def get_delete_url(self, item):
        return self.reverse('%sdelete' % self.get_base_url_name(), pk=item.instance.pk)
    
    def get_absolute_url(self):
        return self.reverse('%slist' % self.get_base_url_name())
    
    #CRUD Methods are based off: (which backbone appears to agree with)
    #http://en.wikipedia.org/wiki/Create,_read,_update_and_delete
    
    def get_create_link(self, form_kwargs=None, **kwargs):
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.get_form_kwargs(**form_kwargs)
        
        link_kwargs = {'url':self.get_add_url(),
                       'resource':self,
                       'on_submit':self.handle_create_submission,
                       'method':'POST',
                       'form_kwargs':form_kwargs,
                       'form_class': self.get_form_class(),
                       'prompt':'create',
                       'rel':'create',}
        link_kwargs.update(kwargs)
        create_link = Link(**link_kwargs)
        return create_link
    
    def get_update_link(self, item, form_kwargs=None, **kwargs):
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.get_form_kwargs(item, **form_kwargs)
        link_kwargs = {'url':item.get_absolute_url(),
                       'resource':self,
                       'on_submit':self.handle_update_submission,
                       'method':'POST',
                       'form_class':item.get_form_class(),
                       'form_kwargs':form_kwargs,
                       'prompt':'update',
                       'rel':'update',}
        update_link = Link(**link_kwargs)
        return update_link
    
    def get_restful_update_link(self, **kwargs):
        kwargs['method'] = 'PUT'
        return self.get_update_link(**kwargs)
    
    def get_delete_link(self, item, **kwargs):
        link_kwargs = {'url':self.get_delete_url(item),
                       'resource':self,
                       'on_submit':self.handle_delete_submission,
                       'rel':'delete',
                       'prompt':'delete',
                       'method':'POST'}
        link_kwargs.update(kwargs)
        delete_link = Link(**link_kwargs)
        return delete_link
    
    def get_restful_delete_link(self, item, **kwargs):
        kwargs['url'] = item.get_absolute_url()
        kwargs['method'] = 'DELETE'
        return self.get_delete_link(item, **kwargs)
    
    def handle_create_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.get_resource_item(instance)
            return self.get_item_link(resource_item)
        return link.clone(form=form)
    
    def handle_update_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.get_resource_item(instance)
            #or send the update link?
            return self.get_item_link(resource_item)
        return link.clone(form=form)
    
    def handle_delete_submission(self, link, submit_kwargs):
        instance = self.state.item.instance
        instance.delete()
        return self.get_resource_link()
    
    def has_add_permission(self, user):
        return True
    
    def has_change_permission(self, user, obj=None):
        return True
    
    def has_delete_permission(self, user, obj=None):
        return True
    
    def get_templated_queries(self):
        links = super(CRUDResource, self).get_templated_queries()
        if 'changelist' in self.state:
            links += self.get_changelist_links()
        return links
    
    def get_outbound_links(self):
        links = super(CRUDResource, self).get_outbound_links()
        links.append(self.get_create_link(link_factor='LO'))
        return links
    
    def get_item_outbound_links(self, item):
        links = super(CRUDResource, self).get_item_outbound_links(item)
        links.append(self.get_delete_link(item=item, link_factor='LO'))
        return links
    
    def get_idempotent_links(self):
        links = super(CRUDResource, self).get_idempotent_links()
        if not self.state.item: #only display a create link if we are not viewing a specific item
            links.append(self.get_create_link())
        return links
    
    def get_item_ln_links(self, item):
        links = super(CRUDResource, self).get_item_ln_links(item)
        if self.state.get('view_class', None) != 'delete_confirmation':
            links.append(self.get_update_link(item=item))
        return links
    
    def get_item_idempotent_links(self, item):
        links = super(CRUDResource, self).get_item_idempotent_links(item)
        if self.state.get('view_class', None) == 'delete_confirmation':
            links.append(self.get_delete_link(item=item))
        else:
            links.append(self.get_restful_delete_link(item=item))
        return links
    
    def get_item_breadcrumb(self, item):
        return self.get_item_link(item, rel='breadcrumb')
    
    def get_breadcrumbs(self):
        breadcrumbs = super(CRUDResource, self).get_breadcrumbs()
        if self.state.item:
            breadcrumbs.append(self.get_item_breadcrumb(self.state.item))
        return breadcrumbs
    
    def get_list_resource_item_class(self):
        return self.list_resource_item_class
    
    def get_list_resource_item(self, instance, **kwargs):
        return self.get_list_resource_item_class()(resource=self, instance=instance, **kwargs)
    
    def get_instances(self):
        '''
        Returns a set of native objects for a given state
        '''
        if 'page' in self.state:
            return self.state['page'].object_list
        if self.state.get('view_class', None) == 'change_form':
            return []
        return self.get_active_index()
    
    def get_resource_items(self):
        instances = self.get_instances()
        if self.state.get('view_class', None) == 'change_list':
            return [self.get_list_resource_item(instance) for instance in instances]
        return [self.get_resource_item(instance) for instance in instances]
    
    def get_active_index(self, **kwargs):
        return self.resource_adaptor.objects.all()
    
    def get_ordering(self):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)
    
    def get_changelist_kwargs(self):
        return {'resource': self}
    
    def get_changelist_class(self):
        return self.changelist_class
    
    def get_changelist(self):
        changelist_class = self.get_changelist_class()
        kwargs = self.get_changelist_kwargs()
        changelist = changelist_class(**kwargs)
        changelist.detect_sections()
        changelist.populate_state(self.state)
        return changelist
    
    def get_changelist_links(self):
        return self.state['changelist'].get_links(self.state)
    
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

