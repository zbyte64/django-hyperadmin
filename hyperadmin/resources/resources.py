from django import http
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
    
    def __init__(self, resource_adaptor, site):
        self.resource_adaptor = resource_adaptor
        self.site = site
    
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
    
    def get_embedded_links(self, instance=None):
        return []
    
    def get_outbound_links(self, instance=None):
        return []
    
    def get_templated_queries(self):
        return []
    
    #TODO find a better name
    def get_ln_links(self, instance=None):
        return []
    
    #TODO find a better name
    def get_li_links(self, instance=None):
        return []
    
    def get_instance_url(self, instance):
        return None
    
    def get_form_class(self, instance=None):
        return self.form_class
    
    def get_form_kwargs(self, **kwargs):
        return kwargs
    
    def generate_response(self, media_type, content_type, instance=None, form_link=None, meta=None):
        #content_type = view.get_response_type()
        return media_type.serialize(content_type=content_type, instance=instance, form_link=form_link, meta=meta)
    
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
    
    def get_prompt(self, instance):
        return unicode(instance)

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
    
    def get_instance_url(self, instance):
        return self.reverse('%s_%s_detail' % (self.app_name, self.resource_name), pk=instance.pk)
    
    def get_delete_url(self, instance):
        return self.reverse('%s_%s_delete' % (self.app_name, self.resource_name), pk=instance.pk)
    
    def get_absolute_url(self):
        return self.reverse('%s_%s_list' % (self.app_name, self.resource_name))
    
    def form_valid(self, form):
        instance = form.save()
        next_url = self.get_instance_url(instance)
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response
    
    def generate_create_response(self, media_type, content_type, form_link, meta=None):
        instance = None
        if form_link.form.is_valid():
            #TODO media type should have a protocol for redirects and instances
            return self.form_valid(form_link.form)
        return self.generate_response(media_type, content_type, instance=instance, form_link=form_link, meta=meta)
    
    def generate_update_response(self, media_type, content_type, instance, form_link, meta=None):
        if form_link.form.is_valid():
            return self.form_valid(form_link.form)
        return self.generate_response(media_type, content_type, instance=instance, form_link=form_link, meta=meta)
    
    def generate_delete_response(self, media_type, content_type):
        next_url = self.get_absolute_url()
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def get_embedded_links(self, instance=None):
        if instance:
            delete_link = Link(url=self.get_delete_url(instance), rel='delete', prompt='Delete')
            return [delete_link]
        add_link = Link(url=self.get_add_url(), rel='add', prompt='Add')
        return [add_link]
    
    def get_outbound_links(self, instance=None):
        if instance:
            return []
        else:
            site_link = Link(url=self.reverse('index'), rel='breadcrumb', prompt='root')
            app_link = Link(url=self.reverse(self.app_name), rel='breadcrumb', prompt=self.app_name)
            resource_list = Link(url=self.get_absolute_url(), rel='breadcrumb', prompt=self.resource_name)
            return [site_link, app_link, resource_list]
    
    def get_templated_queries(self):
        #search and filter goes here
        return []
    
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

