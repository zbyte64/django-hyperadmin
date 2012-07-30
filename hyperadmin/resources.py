from django import http
from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper
from django.utils.datastructures import SortedDict
from django.core.paginator import Paginator
from django import forms

import inspect

import views
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
            raise ValueError('Unrecognized content type')
        return media_type_cls(view)
    
    def generate_response(self, view, instance=None, errors=None):
        try:
            media_type = self.get_media_type(view)
        except ValueError:
            raise #TODO raise Bad request...
        return media_type.serialize(instance=instance, errors=errors)

class SiteResource(BaseResource):
    list_view = views.SiteResourceView
    
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
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

class CRUDResource(BaseResource):
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
        try:
            media_type = self.get_media_type(view)
        except ValueError:
            raise #TODO raise Bad request
        form = media_type.deserialize(form_class=form_class)
        if form.is_valid():
            instance = form.save()
            next_url = self.get_instance_url(instance)
            response = http.HttpResponse(next_url, status=303)
            response['Location'] = next_url
            return response
        return self.generate_response(view, instance=instance, errors=form.errors)
    
    def generate_update_response(self, view, instance, form_class):
        try:
            media_type = self.get_media_type(view)
        except ValueError:
            raise #TODO raise Bad request
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

class ModelResource(CRUDResource):
    #TODO support the following:
    #raw_id_fields = ()
    fields = None
    exclude = []
    #fieldsets = None
    #filter_vertical = ()
    #filter_horizontal = ()
    #radio_fields = {}
    #prepopulated_fields = {}
    formfield_overrides = {}
    #readonly_fields = ()
    #declared_fieldsets = None
    
    #save_as = False
    #save_on_top = False
    paginator = Paginator
    inlines = []
    
    #list display options
    list_display = ('__str__',)
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    date_hierarchy = None
    ordering = None
    
    list_view = views.ModelListResourceView
    detail_view = views.ModelDetailResourceView
    
    def __init__(self, *args, **kwargs):
        super(ModelResource, self).__init__(*args, **kwargs)
        self.model = self.resource_adaptor
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
    
    def get_changelist(self, request):
        from django.contrib.admin.views.main  import ChangeList
        class MockAdminModel(object):
            ordering = self.ordering
            
            def queryset(_, request):
                return self.get_queryset(request)
            
            def get_paginator(_, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
                return self.get_paginator(request, queryset, per_page, orphans, allow_empty_first_page)
            
            def get_ordering(_, request):
                return self.get_ordering(request)
            
            def lookup_allowed(_, lookup, value):
                return self.lookup_allowed(lookup, value)
        
        
        admin_model = MockAdminModel()
    
        changelist_cls = ChangeList
        kwargs = {'request':request,
                  'model':self.resource_adaptor,
                  'list_display':self.list_display,
                  'list_display_links':self.list_display_links,
                  'list_filter':self.list_filter,
                  'date_hierarchy':self.date_hierarchy,
                  'search_fields':self.search_fields,
                  'list_select_related':self.list_select_related,
                  'list_per_page':self.list_per_page,
                  'list_max_show_all':self.list_max_show_all,
                  'list_editable':self.list_editable,
                  'model_admin':admin_model,}
        argspec = inspect.getargspec(changelist_cls.__init__)
        for key in kwargs.keys():
            if key not in argspec.args:
                del kwargs[key]
        return changelist_cls(**kwargs)
    
    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)
    
    def lookup_allowed(self, lookup, value):
        return True #TODO
    
    def get_ordering(self, request):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)
    
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
        if opts.auto_created and hasattr(self, 'parent_model'):
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
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        class AdminForm(forms.ModelForm):
            class Meta:
                model = self.model
                exclude = self.exclude
                #TODO formfield overides
                #TODO fields
        return AdminForm
    
    def get_embedded_links(self, instance=None):
        links = super(ModelResource, self).get_embedded_links(instance=instance)
        inline_links = list()
        if instance:
            for inline in self.inline_instances:
                url = self.reverse('%s_%s_%s_list' % (self.app_name, self.resource_name, inline.rel_name), pk=instance.pk)
                link = Link(url=url,
                            rel='inline-%s' % inline.rel_name,)
                inline_links.append(link)
        return links + inline_links

class InlineModelResource(ModelResource):
    list_view = views.InlineModelListResourceView
    detail_view = views.InlineModelDetailResourceView
    
    model = None
    fk_name = None
    rel_name = None
    
    def __init__(self, parent_resource):
        self.resource_adaptor = self.model
        self.site = parent_resource.site
        self.parent_resource = parent_resource
        
        from django.db.models.fields.related import RelatedObject
        from django.forms.models import _get_foreign_key
        self.fk = _get_foreign_key(self.parent_resource.resource_adaptor, self.model, self.fk_name, can_fail=False)
        if self.rel_name is None:
            self.rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
        self.inline_instances = []
    
    def get_queryset(self, request, instance):
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
    
    def get_instance_url(self, instance):
        return None #TODO
        pk = getattr(instance, self.rel_name).pk
        return self.reverse('%s_%s_%s_detail' % (self.parent_resource.app_name, self.parent_resource.resource_name, self.rel_name), inline_pk=instance.pk, pk=pk)
    
    def get_absolute_url(self, instance=None):
        if not instance:
            return self.parent_resource.get_absolute_url()
        return None

    
