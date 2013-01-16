from django.conf.urls.defaults import patterns, url, include
from django import forms

from hyperadmin.apirequests import Namespace
from hyperadmin.resources.crud import CRUDResource
from hyperadmin.resources.models.indexes import ModelIndex, InlineIndex
from hyperadmin.resources.models.endpoints import InlineListEndpoint, InlineCreateEndpoint, InlineDetailEndpoint, InlineDeleteEndpoint


class BaseModelResource(CRUDResource):
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
    #changelist_class = ModelChangeList
    inlines = []
    
    #list display options
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    date_hierarchy = None
    
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
    
    def get_primary_query(self, **kwargs):
        return self.get_queryset()
    
    def get_indexes(self):
        #from hyperadmin.resources.indexes import Index
        from hyperadmin.resources.models.filters import FieldFilter, SearchFilter

        from django.db import models
        from django.contrib.admin.util import get_fields_from_path
        try:
            from django.contrib.admin.util import lookup_needs_distinct
        except ImportError:
            from hyperadmin.resources.models.util import lookup_needs_distinct
        
        indexes = super(BaseModelResource, self).get_indexes()
        
        index = ModelIndex('filter', self)
        indexes['filter'] = index
        
        if self.list_filter:
            for list_filter in self.list_filter:
                use_distinct = False
                if callable(list_filter):
                    # This is simply a custom list filter class.
                    spec = list_filter(index=index)
                else:
                    field_path = None
                    if isinstance(list_filter, (tuple, list)):
                        # This is a custom FieldListFilter class for a given field.
                        field, field_list_filter_class = list_filter
                    else:
                        # This is simply a field name, so use the default
                        # FieldListFilter class that has been registered for
                        # the type of the given field.
                        field, field_list_filter_class = list_filter, FieldFilter.create
                    if not isinstance(field, models.Field):
                        field_path = field
                        field = get_fields_from_path(self.model, field_path)[-1]
                    spec = field_list_filter_class(field, field_path=field_path, index=index)
                    # Check if we need to use distinct()
                    use_distinct = (use_distinct or
                                    lookup_needs_distinct(self.opts,
                                                          field_path))
                if spec:
                    index.filters.append(spec)
        
        if self.search_fields:
            index.register_filter(SearchFilter, search_fields=self.search_fields)
        '''
        date_section = self.register_section('date', FilterSection)
        if self.date_hierarchy:
            pass
        '''
        return indexes
    
    def lookup_allowed(self, lookup, value):
        return True #TODO
    
    def get_queryset(self):
        queryset = self.resource_adaptor.objects.all()
        if not self.has_change_permission():
            queryset = queryset.none()
        return queryset
    
    def has_add_permission(self):
        user = self.api_request.user
        if self.opts.auto_created:
            # We're checking the rights to an auto-created intermediate model,
            # which doesn't have its own individual permissions. The user needs
            # to have the change permission for the related model in order to
            # be able to do anything with the intermediate model.
            return self.has_change_permission()
        return user.has_perm(
            self.opts.app_label + '.' + self.opts.get_add_permission())

    def has_change_permission(self, item=None):
        user = self.api_request.user
        
        if item:
            obj = item.instance
        else:
            obj = None
        opts = self.opts
        if opts.auto_created and hasattr(self, 'parent_model'):
            # The model was auto-created as intermediary for a
            # ManyToMany-relationship, find the target model
            for field in opts.fields:
                if field.rel and field.rel.to != self.parent_model:
                    opts = field.rel.to._meta
                    break
        return user.has_perm(
            opts.app_label + '.' + opts.get_change_permission(), obj)

    def has_delete_permission(self, item=None):
        user = self.api_request.user
        #obj = item.instance
        if self.opts.auto_created:
            # We're checking the rights to an auto-created intermediate model,
            # which doesn't have its own individual permissions. The user needs
            # to have the change permission for the related model in order to
            # be able to do anything with the intermediate model.
            return self.has_change_permission(item)
        return user.has_perm(
            self.opts.app_label + '.' + self.opts.get_delete_permission())
        
    def get_exclude(self):
        return self.exclude or []
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        class AdminForm(forms.ModelForm):
            class Meta:
                model = self.model
                exclude = self.get_exclude()
                #TODO formfield overides
                #TODO fields
        return AdminForm

class ModelResource(BaseModelResource):
    def post_register(self):
        super(ModelResource, self).post_register()
        self.initialize_inlines()
    
    @property
    def model(self):
        return self.resource_adaptor
    
    def initialize_inlines(self):
        self.inline_instances = list()
        for inline_cls in self.inlines:
            self.register_inline(inline_cls)
    
    def register_inline(self, inline_cls):
        self.inline_instances.append(inline_cls(parent=self, api_request=self.api_request))
    
    def get_view_endpoints(self):
        from hyperadmin.resources.models.endpoints import ListEndpoint, CreateEndpoint, DetailEndpoint, DeleteEndpoint
        endpoints = super(CRUDResource, self).get_view_endpoints()
        endpoints.extend([
            (ListEndpoint, {'index_name':'filter'}),
            (CreateEndpoint, {}),
            (DetailEndpoint, {}),
            (DeleteEndpoint, {}),
        ])
        return endpoints
    
    def get_urls(self):
        urlpatterns = super(ModelResource, self).get_urls()
        for inline in self.inline_instances:
            urlpatterns += patterns('',
                url('', include(inline.urls))
            )
        return urlpatterns
    
    def get_item_namespaces(self, item):
        assert self.api_request
        namespaces = super(ModelResource, self).get_item_namespaces(item)
        for inline in self.inline_instances:
            #new api request, perhaps wrap in namespace?
            name = 'inline-%s' % inline.rel_name
            
            assert inline.api_request
            
            namespace = Namespace(name=name, endpoint=inline, state_data={'parent':item})
            assert 'parent' in namespace.endpoint.state
            namespace.link
            namespaces[name] = namespace
        return namespaces

class InlineModelResource(BaseModelResource):
    model = None
    fk_name = None
    rel_name = None
    
    def __init__(self, parent, **kwargs):
        kwargs['site'] = parent.site
        kwargs['resource_adaptor'] = self.model
        kwargs['parent'] = parent
        super(InlineModelResource, self).__init__(**kwargs)
    
    def post_register(self):
        from django.db.models.fields.related import RelatedObject
        from django.forms.models import _get_foreign_key
        self.fk = _get_foreign_key(self._parent.resource_adaptor, self.model, self.fk_name)
        if self.rel_name is None:
            #TODO invert this
            self.rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
        super(InlineModelResource, self).post_register()
    
    def get_queryset(self, parent):
        queryset = self.resource_adaptor.objects.all()
        queryset = queryset.filter(**{self.fk.name:parent})
        if not self.has_change_permission():
            queryset = queryset.none()
        return queryset
    
    def get_primary_query(self, **kwargs):
        return self.get_queryset(parent=self.state['parent'].instance)
    
    def get_indexes(self):
        return {'primary':InlineIndex('primary', self)}
    
    def get_base_url_name(self):
        return '%s%s' % (self._parent.get_base_url_name(), self.rel_name)
    
    def get_view_endpoints(self):
        endpoints = super(CRUDResource, self).get_view_endpoints()
        endpoints.extend([
            (InlineListEndpoint, {}),
            (InlineCreateEndpoint, {}),
            (InlineDetailEndpoint, {}),
            (InlineDeleteEndpoint, {}),
        ])
        return endpoints
    
    def get_item_url(self, item):
        return self.link_prototypes['update'].get_url(item=item)
    
    def get_absolute_url(self):
        return self.link_prototypes['list'].get_url()
    
    def get_breadcrumbs(self):
        breadcrumbs = self.parent.get_breadcrumbs()
        parent_item = self.state['parent']
        breadcrumbs.append(self.parent.get_item_breadcrumb(parent_item))
        breadcrumbs.append(self.get_breadcrumb())
        if self.state.item:
            breadcrumbs.append(self.get_item_breadcrumb(self.state.item))
        return breadcrumbs
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        
        resource = self
        
        class AdminForm(forms.ModelForm):
            state = self.state
            
            def save(self, commit=True):
                instance = super(AdminForm, self).save(commit=False)
                setattr(instance, resource.fk.name, self.state['parent'].instance)
                if commit:
                    instance.save()
                return instance
            
            class Meta:
                model = self.model
                exclude = self.get_exclude() + [self.fk.name]
                #TODO formfield overides
                #TODO fields
        return AdminForm
    
    def get_ln_links(self):
        links = self.create_link_collection()
        if self.state.namespace:
            for item in self.get_resource_items():
                links.append(self.link_prototypes['update'].get_link(item=item))
        return links
    
    def get_idempotent_links(self):
        links = self.create_link_collection()
        if self.state.namespace:
            for item in self.get_resource_items():
                links.append(self.link_prototypes['delete'].get_link(item=item))
        return links

