from django import http
from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper

from views import ModelListResourceView, ModelDetailResourceView, ApplicationResourceView
from links import Link

class BaseResource(object):
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
    
    def get_media_type(self, view):
        content_type = view.get_content_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            #TODO raise the proper exception
            assert False, 'Unrecognized content type'
        return media_type_cls(view)
    
    def generate_response(self, view, instance=None, errors=None):
        media_type = self.get_media_type(view)
        return media_type.serialize(instance=instance, errors=errors)

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
        return self.site.applications.values()
    
    def get_instance_url(self, instance):
        if hasattr(instance, 'get_absolute_url'):
            return instance.get_absolute_url()

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
            site_link = Link(url=self.reverse('index'), rel='site')
            return [site_link]
    
    def get_instance_url(self, instance):
        if hasattr(instance, 'get_absolute_url'):
            return instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse(self.app_name)

class CRUDResource(BaseResource):
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
            url(r'^(?P<pk>.+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_detail' % (self.app_name, self.resource_name)),
        )
        return urlpatterns
    
    def get_instance_url(self, instance):
        return self.reverse('%s_%s_detail' % (self.app_name, self.resource_name), pk=instance.pk)
    
    def get_absolute_url(self):
        return self.reverse('%s_%s_list' % (self.app_name, self.resource_name))
    
    def generate_create_response(self, view, form_class):
        instance = None
        media_type = self.get_media_type(view)
        form = media_type.deserialize(form_class=form_class)
        if form.is_valid():
            instance = form.save()
            next_url = self.get_instance_url(instance)
            response = http.HttpResponse(next_url, status=303)
            response['Location'] = next_url
            return response
        return self.generate_response(view, instance=instance, errors=form.errors)
    
    def generate_update_response(self, view, instance, form_class):
        media_type = self.get_media_type(view)
        form = media_type.deserialize(instance=instance, form_class=form_class)
        if form.is_valid():
            instance = form.save()
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
            site_link = Link(url=self.reverse('index'), rel='site')
            app_link = Link(url=self.reverse(self.app_name), rel='application')
            resource_list = Link(url=self.get_absolute_url(), rel='resource-listing')
            return [site_link, app_link, resource_list]
    
    def get_templated_queries(self):
        #search and filter goes here
        return []
    
    #TODO find a better name
    def get_li_links(self, instance=None):
        if instance:
            delete_link = Link(url=self.get_instance_url(instance),
                               rel='delete',
                               method='DELETE')
            return [delete_link]
        return []

class ModelResource(CRUDResource):
    #TODO support the following:
    #raw_id_fields = ()
    #fields = None
    #exclude = []
    #fieldsets = None
    #filter_vertical = ()
    #filter_horizontal = ()
    #radio_fields = {}
    #prepopulated_fields = {}
    #formfield_overrides = {}
    #readonly_fields = ()
    #declared_fieldsets = None
    
    #save_as = False
    #save_on_top = False
    #paginator = Paginator
    inlines = []
    
    #list display options
    #list_display = ('__str__',)
    #list_display_links = ()
    #list_filter = ()
    #list_select_related = False
    #list_per_page = 100
    #list_max_show_all = 200
    #list_editable = ()
    #search_fields = ()
    #date_hierarchy = None
    #ordering = None
    
    list_view = ModelListResourceView
    detail_view = ModelDetailResourceView
    
    def __init__(self, *args, **kwargs):
        super(ModelResource, self).__init__(*args, **kwargs)
        self.inline_instances = list()
        for inline_cls in self.inlines:
            self.inline_instances.append(inline_cls(self))
    
    @property
    def opts(self):
        return self.resource_adaptor._meta
    
    def get_app_name(self):
        return self.opts.app_label
    app_name = property(get_app_name)
    
    def get_resource_name(self):
        return self.opts.module_name
    resource_name = property(get_resource_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        
        urlpatterns = super(ModelResource, self).get_urls()
        for inline in self.inline_instances:
            urlpatterns += patterns('',
                url(r'^(?P<pk>.+)/%s/$' % inline.rel_name,
                    include(inline.urls)),
            )
        return urlpatterns
    
    def get_view_kwargs(self):
        kwargs = super(ModelResource, self).get_view_kwargs()
        kwargs['model'] = self.resource_adaptor
        kwargs['form_class'] = self.form_class
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

class InlineModelResource(ModelResource):
    model = None
    #TODO going to need some custom views
    
    def __init__(self, parent_resource):
        self.resource_adaptor = self.model
        self.site = parent_resource.site
        self.prarent_resource = parent_resource
        self.rel_name = None #TODO
    
    def get_queryset(self, instance, request):
        queryset = self.resource_adaptor.objects.all()
        queryset.filter(**{self.rel_name:instance})
        if not self.has_change_permission(request):
            queryset = queryset.none()
        return queryset
    
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
                name='%s_%s_%s_list' % (self.parent_resource.app_name, self.parent_resource.resource_name, self.rel_name)),
            url(r'^(?P<inline_pk>.+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_%s_detail' % (self.parent_resource.app_name, self.parent_resource.resource_name, self.rel_name)),
        )
        return urlpatterns
    
