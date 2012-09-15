from django import forms
from django.conf.urls.defaults import patterns, url

from hyperadmin.hyperobjects import Link, ResourceItem


class EmptyForm(forms.Form):
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(EmptyForm, self).__init__(**kwargs)

class BaseResource(object):
    resource_class = '' #hint to the client how this resource is used
    resource_item_class = ResourceItem
    form_class = EmptyForm
    
    def __init__(self, resource_adaptor, site, parent_resource=None):
        self.resource_adaptor = resource_adaptor
        self.site = site
        self.parent = parent_resource
    
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
        return self.site.reverse(name, *args, **kwargs)
    
    def as_view(self, view, cacheable=False):
        return self.site.as_view(view, cacheable)
    
    def as_nonauthenticated_view(self, view, cacheable=False):
        return self.site.as_nonauthenticated_view(view, cacheable)
    
    def get_view_kwargs(self):
        return {'resource':self,
                'resource_site':self.site,}
    
    def get_embedded_links(self, state):
        return []
    
    def get_item_embedded_links(self, item):
        return []
    
    def get_outbound_links(self, state):
        return self.get_breadcrumbs(state)
    
    def get_item_outbound_links(self, item):
        return []
    
    def get_templated_queries(self, state):
        return []
    
    def get_item_templated_queries(self, item):
        return []
    
    #TODO find a better name
    def get_ln_links(self, state):
        return []
    
    #TODO find a better name
    def get_item_ln_links(self, item):
        return []
    
    #TODO find a better name
    def get_idempotent_links(self, state):
        return []
    
    #TODO find a better name
    def get_item_idempotent_links(self, item):
        return []
    
    def get_item_url(self, item):
        return None
    
    def get_form_class(self):
        return self.form_class
    
    def get_form_kwargs(self, item=None, **kwargs):
        if item is not None:
            kwargs.setdefault('instance', item.instance)
        return kwargs
    
    def generate_response(self, media_type, content_type, link, state):
        return media_type.serialize(content_type=content_type, link=link, state=state)
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)
    
    def get_child_resource_links(self):
        return []
    
    def get_absolute_url(self):
        raise NotImplementedError
    
    def get_resource_item(self, instance):
        return self.resource_item_class(resource=self, instance=instance)
    
    def get_resource_items(self, state):
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
    
    def get_breadcrumbs(self, state):
        breadcrumbs = []
        if self.parent:
            breadcrumbs = self.parent.get_breadcrumbs(state=None)
        breadcrumbs.append(self.get_breadcrumb())
        return breadcrumbs
    
    def get_prompt(self):
        return unicode(self)
    
    def get_item_prompt(self, item):
        return unicode(item.instance)
    
    def get_item_link(self, item):
        item_link = Link(url=item.get_absolute_url(),
                         resource=self,
                         rel='item',
                         prompt=item.get_prompt(),)
        return item_link

class CRUDResource(BaseResource):
    resource_class = 'crudresource'
    
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
        return self.get_create_link(form_kwargs=link.form_kwargs, form=form)
    
    def handle_update_submission(self, state, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.get_resource_item(instance)
            return self.get_item_link(resource_item)
        return self.get_update_link(state.item, form_kwargs=link.form_kwargs, form=form)
    
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

