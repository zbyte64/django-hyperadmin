from django import http
from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper

from hyperadmin import views
from links import Link

class BaseResource(object):
    resource_class = '' #hint to the client how this resource is used
    
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
    
    def get_request_media_type(self, view):
        content_type = view.get_request_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized content type')
        return media_type_cls(view)
    
    def get_response_media_type(self, view):
        content_type = view.get_response_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized content type')
        return media_type_cls(view)
    
    def generate_response(self, view, instance=None, errors=None):
        try:
            media_type = self.get_response_media_type(view)
        except ValueError:
            raise #TODO raise Bad request...
        content_type = view.get_response_type()
        return media_type.serialize(content_type=content_type, instance=instance, errors=errors)
    
    def get_related_resource_from_field(self, field):
        return self.site.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.site.get_html_type_from_field(field)
    
    def get_child_resource_links(self):
        return []

class SiteResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.SiteResourceView
    
    def __init__(self, site, auth_resource=None):
        self.site = site
        if auth_resource is None:
            from auth import AuthResource
            auth_resource = AuthResource
        self.auth_resource = auth_resource(site=site)
    
    def get_app_name(self):
        return self.site.name
    app_name = property(get_app_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='index'),
            url(r'^_authentication/',
                include(self.auth_resource.urls)),
        )
        for key, app in self.site.applications.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(app.urls))
            )
        return urlpatterns
    
    def get_items(self, request):
        #TODO sort by name
        return self.site.applications.values() + [self.auth_resource]
    
    def get_instance_url(self, instance):
        if hasattr(instance, 'get_absolute_url'):
            return instance.get_absolute_url()
    
    def get_embedded_links(self, instance=None):
        #relationships go here
        if instance and hasattr(instance, 'get_child_resource_links'): #AKA application resource
            return instance.get_child_resource_links()
        return []

class ApplicationResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.ApplicationResourceView
    
    def __init__(self, app_name, site):
        self._app_name = app_name
        self.resource_adaptor = dict() #TODO OrderedDict
        self.site = site
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name=self.app_name),
        )
        for key, resource in self.resource_adaptor.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(resource.urls))
            )
        return urlpatterns
    
    def register_resource(self, resource):
        key = resource.get_resource_name()
        self.resource_adaptor[key] = resource
    
    def get_items(self, request):
        #TODO sort by name
        return self.resource_adaptor.values()
    
    def get_embedded_links(self, instance=None):
        #relationships go here
        return []
    
    def get_outbound_links(self, instance=None):
        if instance:
            return []
        else:
            site_link = Link(url=self.reverse('index'), rel='breadcrumb', prompt='root')
            return [site_link]
    
    def get_instance_url(self, instance):
        if hasattr(instance, 'get_absolute_url'):
            return instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse(self.app_name)
    
    def get_child_resource_links(self):
        links = list()
        for key, resource in self.resource_adaptor.iteritems():
            resource_link = Link(url=resource.get_absolute_url(), rel='child-resource', prompt=resource.resource_name)
            links.append(resource_link)
        return links
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

class CRUDResource(BaseResource):
    resource_class = 'crudresource'
    
    #TODO support the following:
    actions = []
    
    list_view = None
    detail_view = None
    form_class = None
    
    def get_resource_name(self):
        raise NotImplementedError
    resource_name = property(get_resource_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='%s_%s_list' % (self.app_name, self.resource_name)),
            url(r'^(?P<pk>\w+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_detail' % (self.app_name, self.resource_name)),
        )
        return urlpatterns
    
    def get_instance_url(self, instance):
        return self.reverse('%s_%s_detail' % (self.app_name, self.resource_name), pk=instance.pk)
    
    def get_absolute_url(self):
        return self.reverse('%s_%s_list' % (self.app_name, self.resource_name))
    
    def form_valid(self, form):
        instance = form.save()
        next_url = self.get_instance_url(instance)
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response
    
    def generate_create_response(self, view, form_class):
        instance = None
        try:
            media_type = self.get_request_media_type(view)
        except ValueError:
            raise #TODO raise Bad request
        form = media_type.deserialize(form_class=form_class)
        if form.is_valid():
            return self.form_valid(form)
        return self.generate_response(view, instance=instance, errors=form.errors)
    
    def generate_update_response(self, view, instance, form_class):
        try:
            media_type = self.get_request_media_type(view)
        except ValueError:
            raise #TODO raise Bad request
        form = media_type.deserialize(instance=instance, form_class=form_class)
        if form.is_valid():
            return self.form_valid(form)
        return self.generate_response(view, instance=instance, errors=form.errors)
    
    def generate_delete_response(self, view):
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
        #relationships go here
        return []
    
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
    
    #TODO find a better name
    def get_li_links(self, instance=None):
        if instance:
            delete_link = Link(url=self.get_instance_url(instance),
                               rel='delete',
                               prompt='delete',
                               method='DELETE')
            return [delete_link]
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

