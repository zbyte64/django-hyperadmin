from django.conf.urls.defaults import patterns, url
from django.utils.encoding import force_unicode
from django.core.paginator import Paginator
from django import forms

from hyperadmin.hyperobjects import Link, ResourceItem
from hyperadmin.resources.resources import BaseResource


class ListForm(forms.Form):
    '''
    hyperadmin knows how to serialize forms, not models.
    So for the list display we need a form
    '''
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.resource = kwargs.pop('resource')
        super(ListForm, self).__init__(**kwargs)
        if self.resource.list_display:
            for display in self.resource.list_display:
                label = display
                if label == '__str__':
                    label = self.resource.resource_name
                self.fields[display] = forms.CharField(label=label)
                if self.instance:
                    val = getattr(self.instance, display)
                    if callable(val):
                        val = val()
                    self.initial[display] = force_unicode(val)
        else:
            pass
            #TODO support all field listing as default

class ListResourceItem(ResourceItem):
    form_class = ListForm
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(ListResourceItem, self).get_form_kwargs(**kwargs)
        form_kwargs = {'instance':kwargs.get('instance', None),
                       'resource':self.resource}
        return form_kwargs

class CRUDResource(BaseResource):
    resource_class = 'crudresource'
    
    ordering = None
    list_display = ('__str__',) #TODO should list all field by default
    list_resource_item_class = ListResourceItem
    paginator_class = Paginator
    
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
    
    def get_prompt(self):
        return self.resource_name
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='%s_%s_list' % (self.app_name, self.resource_name)),
            url(r'^add/$',
                wrap(self.add_view.as_view(**init)),
                name='%s_%s_add' % (self.app_name, self.resource_name)),
            url(r'^(?P<pk>\w+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_detail' % (self.app_name, self.resource_name)),
            url(r'^(?P<pk>\w+)/delete/$',
                wrap(self.delete_view.as_view(**init)),
                name='%s_%s_delete' % (self.app_name, self.resource_name)),
        )
        return urlpatterns
    
    def get_add_url(self):
        return self.reverse('%s_%s_add' % (self.app_name, self.resource_name))
    
    def get_item_url(self, item):
        return self.reverse('%s_%s_detail' % (self.app_name, self.resource_name), pk=item.instance.pk)
    
    def get_delete_url(self, item):
        return self.reverse('%s_%s_delete' % (self.app_name, self.resource_name), pk=item.instance.pk)
    
    def get_absolute_url(self):
        return self.reverse('%s_%s_list' % (self.app_name, self.resource_name))
    
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
    
    def get_restful_create_link(self, **kwargs):
        kwargs['url'] = self.get_absolute_url()
        return self.get_create_link(**kwargs)
    
    def get_update_link(self, item, form_kwargs=None, **kwargs):
        if form_kwargs is None:
            form_kwargs = {}
        form_kwargs = self.get_form_kwargs(item, **form_kwargs)
        link_kwargs = {'url':item.get_absolute_url(),
                       'resource':self,
                       'on_submit':self.handle_update_submission,
                       'method':'POST',
                       'form_class':self.get_form_class(),
                       'form_kwargs':form_kwargs,
                       'prompt':'update',
                       'rel':'update',}
        update_link = Link(**link_kwargs)
        return update_link
    
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
    
    def handle_create_submission(self, state, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.get_resource_item(instance)
            return self.get_item_link(resource_item)
        return link.clone(form=form)
    
    def handle_update_submission(self, state, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.get_resource_item(instance)
            #or send the update link?
            return self.get_item_link(resource_item)
        return link.clone(form=form)
    
    def handle_delete_submission(self, state, link, submit_kwargs):
        instance = state.item.instance
        instance.delete()
        return self.get_resource_link()
    
    def has_add_permission(self, user):
        return True
    
    def has_change_permission(self, user, obj=None):
        return True
    
    def has_delete_permission(self, user, obj=None):
        return True
    
    def get_embedded_links(self, state):
        create_link = self.get_create_link()
        return [create_link]
    
    def get_item_embedded_links(self, item):
        delete_link = self.get_delete_link(item=item)
        return [delete_link]
    
    def get_ln_links(self, state):
        create_link = self.get_restful_create_link()
        return [create_link]
    
    def get_item_ln_links(self, item):
        update_link = self.get_update_link(item=item)
        return [update_link]
    
    def get_item_idempotent_links(self, item):
        delete_link = self.get_restful_delete_link(item=item)
        return [delete_link]
    
    def get_list_resource_item_class(self):
        return self.list_resource_item_class
    
    def get_list_resource_item(self, instance):
        return self.get_list_resource_item_class()(resource=self, instance=instance)
    
    def get_instances(self, state):
        '''
        Returns a set of native objects for a given state
        '''
        return self.resource_adaptor.objects.all()
    
    def get_resource_items(self, state):
        instances = self.get_instances(state)
        if state.get('view_class', None) == 'change_list':
            return [self.get_list_resource_item(instance) for instance in instances]
        return [self.get_resource_item(instance) for instance in instances]
    
    def get_ordering(self):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)
    
    def get_paginator_class(self):
        return self.paginator_class
    
    def get_paginator(self, index, per_page, orphans=0, allow_empty_first_page=True):
        return self.get_paginator_class()(index, per_page, orphans, allow_empty_first_page)
    
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

