import inspect

from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper
from django.core.paginator import Paginator
from django import forms

from hyperadmin import views

from resources import CRUDResource
from links import Link

class MockAdminModel(object):
    def __init__(self, resource, model_admin=None):
        self.resource = resource
        if model_admin is None:
            from django.contrib.admin.options import ModelAdmin
            model_admin = ModelAdmin(resource.resource_adaptor, resource.site)
        self.model_admin = model_admin
    
    def __getattr__(self, attr):
        dct = object.__getattribute__(self, '__dict__')
        if attr in dct:
            return object.__getattribute__(self, attr)
        model_admin = object.__getattribute__(self, 'model_admin')
        resource = object.__getattribute__(self, 'resource')
        if hasattr(resource, attr):
            return getattr(resource, attr)
        return getattr(model_admin, attr)
    
    def queryset(self, request):
        return self.resource.get_queryset(request)

class ListForm(forms.Form):
    '''
    hyperadmin knows how to serialize forms, not models.
    So for the list display we need a form
    '''
    
    resource = None
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(ListForm, self).__init__(**kwargs)
        for display in self.resource.list_display:
            label = display
            if label == '__str__':
                label = self.resource.resource_name
            self.fields[display] = forms.CharField(label=label)
            if self.instance:
                val = getattr(self.instance, display)
                if callable(val):
                    val = val()
                self.initial[display] = str(val)

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
            self.register_inline(inline_cls)
    
    def register_inline(self, inline_cls):
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
                url(r'^(?P<pk>\w+)/%s/' % inline.rel_name,
                    include(inline.urls),),
            )
        return urlpatterns
    
    def get_view_kwargs(self):
        kwargs = super(ModelResource, self).get_view_kwargs()
        kwargs['model'] = self.resource_adaptor
        kwargs['form_class'] = self.form_class
        return kwargs
    
    def get_changelist(self, request):
        from django.contrib.admin.views.main  import ChangeList
        
        admin_model = MockAdminModel(self)
        
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
    
    def get_list_form_class(self):
        #TODO improve this
        class AdminListForm(ListForm):
            resource = self
        return AdminListForm
    
    def get_embedded_links(self, instance=None):
        links = super(ModelResource, self).get_embedded_links(instance=instance)
        inline_links = list()
        if instance:
            for inline in self.inline_instances:
                #TODO why doesn't this resolve?
                #url = self.reverse('%s_%s_%s_list' % (self.app_name, self.resource_name, inline.rel_name), pk=instance.pk)
                url = self.get_instance_url(instance) + inline.rel_name + '/'
                link = Link(url=url,
                            prompt='inlines: %s' % inline.rel_name,
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
        self.fk = _get_foreign_key(self.parent_resource.resource_adaptor, self.model, self.fk_name)
        if self.rel_name is None:
            self.rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
        self.inline_instances = []
    
    def get_queryset(self, request, instance):
        queryset = self.resource_adaptor.objects.all()
        queryset = queryset.filter(**{self.fk.name:instance})
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
            url(r'^(?P<inline_pk>\w+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%s_%s_%s_detail' % (self.parent_resource.app_name, self.parent_resource.resource_name, self.rel_name)),
        )
        return urlpatterns
    
    def get_instance_url(self, instance):
        url = self.parent_resource.get_instance_url(instance)
        pk = getattr(instance, self.fk.name).pk
        return '%s%s/%s/' % (url, self.rel_name, pk)
        #return self.reverse('%s_%s_%s_detail' % (self.parent_resource.app_name, self.parent_resource.resource_name, self.rel_name), inline_pk=instance.pk, pk=pk)
    
    def get_absolute_url(self, instance=None):
        if not instance:
            return self.parent_resource.get_absolute_url()
        return None

