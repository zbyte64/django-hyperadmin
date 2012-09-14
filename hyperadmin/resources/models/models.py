from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper
from django.utils.encoding import force_unicode
from django.core.paginator import Paginator
from django import forms

from hyperadmin.hyperobjects import Link, ResourceItem
from hyperadmin.resources import CRUDResource
from hyperadmin.resources.models import views
from hyperadmin.resources.models.changelist import ChangeList

class ListForm(forms.Form):
    '''
    hyperadmin knows how to serialize forms, not models.
    So for the list display we need a form
    '''
    
    def __init__(self, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.resource = kwargs.pop('resource')
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
                self.initial[display] = force_unicode(val)

class ListResourceItem(ResourceItem):
    form_class = ListForm
    
    def get_form_kwargs(self, **kwargs):
        kwargs = super(ListResourceItem, self).get_form_kwargs(**kwargs)
        kwargs['resource'] = self.resource
        return kwargs

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
    changelist = ChangeList
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
    add_view = views.ModelCreateResourceView
    detail_view = views.ModelDetailResourceView
    delete_view = views.ModelDeleteResourceView
    
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
    
    def get_prompt(self):
        return self.resource_name
    
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
        return kwargs
    
    def get_changelist(self, user, filter_params=None):
        changelist_cls = self.changelist
        kwargs = {'model':self.resource_adaptor,
                  'root_query_set': self.get_queryset(user),
                  'user':user,
                  'filter_params':filter_params or dict(),
                  'list_display':self.list_display,
                  'list_display_links':self.list_display_links,
                  'list_filter':self.list_filter,
                  'date_hierarchy':self.date_hierarchy,
                  'search_fields':self.search_fields,
                  'list_select_related':self.list_select_related,
                  'list_per_page':self.list_per_page,
                  'list_max_show_all':self.list_max_show_all,
                  'list_editable':self.list_editable,
                  'resource':self,}
        return changelist_cls(**kwargs)
    
    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)
    
    def lookup_allowed(self, lookup, value):
        return True #TODO
    
    def get_ordering(self):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)
    
    def get_queryset(self, user):
        queryset = self.resource_adaptor.objects.all()
        if not self.has_change_permission(user):
            queryset = queryset.none()
        return queryset

    def has_add_permission(self, user):
        if self.opts.auto_created:
            # We're checking the rights to an auto-created intermediate model,
            # which doesn't have its own individual permissions. The user needs
            # to have the change permission for the related model in order to
            # be able to do anything with the intermediate model.
            return self.has_change_permission(user)
        return user.has_perm(
            self.opts.app_label + '.' + self.opts.get_add_permission())

    def has_change_permission(self, user, obj=None):
        opts = self.opts
        if opts.auto_created and hasattr(self, 'parent_model'):
            # The model was auto-created as intermediary for a
            # ManyToMany-relationship, find the target model
            for field in opts.fields:
                if field.rel and field.rel.to != self.parent_model:
                    opts = field.rel.to._meta
                    break
        return user.has_perm(
            opts.app_label + '.' + opts.get_change_permission())

    def has_delete_permission(self, user, obj=None):
        if self.opts.auto_created:
            # We're checking the rights to an auto-created intermediate model,
            # which doesn't have its own individual permissions. The user needs
            # to have the change permission for the related model in order to
            # be able to do anything with the intermediate model.
            return self.has_change_permission(user, obj)
        return user.has_perm(
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
    
    def get_item_embedded_links(self, item):
        links = super(ModelResource, self).get_item_embedded_links(item=item)
        inline_links = list()
        for inline in self.inline_instances:
            #TODO why doesn't this resolve?
            #url = self.reverse('%s_%s_%s_list' % (self.app_name, self.resource_name, inline.rel_name), pk=instance.pk)
            url = self.get_item_url(item) + inline.rel_name + '/'
            link = Link(url=url,
                        resource=inline,
                        item=inline.get_resource_link_item(),
                        prompt='inlines: %s' % inline.rel_name,
                        rel='inline-%s' % inline.rel_name,)
            inline_links.append(link)
        return links + inline_links
    
    def get_resource_item(self, instance, from_list=False):
        if from_list:
            return ListResourceItem(resource=self, instance=instance)
        return super(ModelResource, self).get_resource_item(instance)

class InlineModelResource(ModelResource):
    list_view = views.InlineModelListResourceView
    add_view = views.InlineModelCreateResourceView
    detail_view = views.InlineModelDetailResourceView
    delete_view = views.InlineModelDeleteResourceView
    
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
    
    def get_queryset(self, parent, user, filter_params):
        queryset = self.resource_adaptor.objects.all()
        queryset = queryset.filter(**{self.fk.name:parent})
        if not self.has_change_permission(user):
            queryset = queryset.none()
        return queryset
    
    def get_base_url_name(self):
        return '%s_%s_%s_' % (self.parent_resource.app_name, self.parent_resource.resource_name, self.rel_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.as_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        
        init = self.get_view_kwargs()
        base_name = self.get_base_url_name()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='%slist' % (base_name)),
            url(r'^add/$',
                wrap(self.add_view.as_view(**init)),
                name='%sadd' % (base_name)),
            url(r'^(?P<inline_pk>\w+)/$',
                wrap(self.detail_view.as_view(**init)),
                name='%sdetail' % (base_name)),
            url(r'^(?P<inline_pk>\w+)/delete/$',
                wrap(self.detail_view.as_view(**init)),
                name='%sdelete' % (base_name)),
        )
        return urlpatterns
    
    def get_add_url(self):
        #TODO i need parent resource in order to work
        return './add/'
    
    def get_delete_url(self, item):
        instance = item.instance
        pk = getattr(instance, self.fk.name).pk
        return self.reverse('%sdelete' % self.get_base_url_name(), pk=pk, inline_pk=instance.pk)
    
    def get_instance_url(self, item):
        instance = item.instance
        pk = getattr(instance, self.fk.name).pk
        return self.reverse('%sdetail' % self.get_base_url_name(), pk=pk, inline_pk=instance.pk)
    
    def get_absolute_url(self, instance=None):
        if not instance:
            return self.parent_resource.get_absolute_url()
        return None
    
    def get_changelist(self, parent, user, filter_params=None):
        changelist_cls = self.changelist
        kwargs = {'model':self.resource_adaptor,
                  'root_query_set': self.get_queryset(parent, user, filter_params or dict()),
                  'user':user,
                  'filter_params':filter_params or dict(),
                  'list_display':self.list_display,
                  'list_display_links':self.list_display_links,
                  'list_filter':self.list_filter,
                  'date_hierarchy':self.date_hierarchy,
                  'search_fields':self.search_fields,
                  'list_select_related':self.list_select_related,
                  'list_per_page':self.list_per_page,
                  'list_max_show_all':self.list_max_show_all,
                  'list_editable':self.list_editable,
                  'resource':self,}
        return changelist_cls(**kwargs)

