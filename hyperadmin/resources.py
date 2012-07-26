from django import http
from django.conf.urls.defaults import patterns, url, include
from django.core.urlresolvers import get_urlconf, get_resolver, reverse
from django.utils.functional import update_wrapper

from views import ModelListResourceView, ModelDetailResourceView, ApplicationResourceView

class Link(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

class TemplatedLink(Link):
    pass

class BaseResource(object):
    form_class = None
    
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
        #TODO...
        urlconf = get_urlconf()
        resolver = get_resolver(urlconf)
        app_list = resolver.app_dict['admin']
        return reverse('%s:%s' % (self.site.name, name), args=args, kwargs=kwargs, current_app=self.app_name)
    
    def as_view(self, view, cacheable=False):
        return self.site.as_view(view, cacheable)
    
    def get_view_kwargs(self):
        return {'resource':self,
                'resource_site':self.site,
                'form_class':self.form_class,}
    
    def get_embedded_links(self, instance=None):
        return []
    
    def get_outbound_links(self, instance=None):
        #TODO return breadcrumb links
        return []
    
    def get_templated_queries(self):
        return []
    
    def get_instance_url(self, instance):
        return None
    
    def get_form_class(self, instance=None):
        return self.form_class
    
    def generate_response(self, view, instance=None, errors=None):
        content_type = view.get_content_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            pass
        media_type = media_type_cls(view)
        return media_type.serialize(view, instance=instance, errors=errors)

class SiteResource(BaseResource):
    list_view = ApplicationResourceView
    
    def __init__(self, site):
        self.site = site
    
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
        )
        for key, app in self.site.applications.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(app.urls))
            )
        return urlpatterns
    
    def get_items(self, request):
        #TODO sort by name
        return self.site.application.values()

class ApplicationResource(BaseResource):
    list_view = ApplicationResourceView
    
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
            url(r'^$' % self.app_name,
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

class CRUDResource(BaseResource):
    list_view = None
    detail_view = None
    
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
            url(r'^(?P<pk>.+)/$',
                wrap(self.detail_view.as_view(**init)),
                name=self.app_name+'_detail'),
        )
        return urlpatterns
    
    def get_instance_url(self, instance):
        return self.reverse(self.app_name+'_detail', pk=instance.pk)
    
    def generate_create_response(self, view, instance):
        next_url = self.get_instance_url(instance)
        response = http.HttpResponse(next_url, status=303)
        response['Location'] = next_url
        return response
    
    def generate_delete_response(self, view):
        next_url = self.reverse(self.app_name+'_list')
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
            site_link = Link(url=self.reverse('index'), rel='site')
            app_link = Link(url=self.reverse(self.app_name), rel='application')
            resource_list = Link(url=self.reverse(self.app_name+'_list'), rel='resource-listing')
            return [site_link, app_link, resource_list]
    
    def get_templated_queries(self):
        #search and filter goes here
        return []

class ModelResource(CRUDResource):
    list_view = ModelListResourceView
    detail_view = ModelDetailResourceView
    
    @property
    def opts(self):
        return self.resource_adaptor._meta
    
    def get_app_name(self):
        return self.opts.app_label
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        return self.opts.module_name
    resource_name = property(get_resource_name)
    
    def get_view_kwargs(self):
        kwargs = super(ModelResource, self).get_view_kwargs()
        kwargs['model'] = self.resource_adaptor
        return kwargs
    
    def get_queryset(self, request):
        queryset = self.resource_adaptor.objects.all()
        if not self.has_change_permission(request):
            queryset = queryset.none()
        return queryset

    def has_add_permission(self, request):
        if self.opts.auto_created:
            # We're checking the rights to an auto-created intermediate model,
            # which doesn't have its own individual permissions. The user needs
            # to have the change permission for the related model in order to
            # be able to do anything with the intermediate model.
            return self.has_change_permission(request)
        return request.user.has_perm(
            self.opts.app_label + '.' + self.opts.get_add_permission())

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        if opts.auto_created:
            # The model was auto-created as intermediary for a
            # ManyToMany-relationship, find the target model
            for field in opts.fields:
                if field.rel and field.rel.to != self.parent_model:
                    opts = field.rel.to._meta
                    break
        return request.user.has_perm(
            opts.app_label + '.' + opts.get_change_permission())

    def has_delete_permission(self, request, obj=None):
        if self.opts.auto_created:
            # We're checking the rights to an auto-created intermediate model,
            # which doesn't have its own individual permissions. The user needs
            # to have the change permission for the related model in order to
            # be able to do anything with the intermediate model.
            return self.has_change_permission(request, obj)
        return request.user.has_perm(
            self.opts.app_label + '.' + self.opts.get_delete_permission())


