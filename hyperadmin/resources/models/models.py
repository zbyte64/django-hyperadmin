from django.conf.urls.defaults import patterns, url, include
from django.utils.functional import update_wrapper
from django import forms

from hyperadmin.hyperobjects import Link
from hyperadmin.resources.crud.crud import CRUDResource
from hyperadmin.resources.models import views
from hyperadmin.resources.models.changelist import ModelChangeList


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
    changelist_class = ModelChangeList
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
    
    list_view = views.ModelListView
    add_view = views.ModelCreateView
    detail_view = views.ModelDetailView
    delete_view = views.ModelDeleteView
    
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
        kwargs['model'] = self.model
        return kwargs
    
    def get_active_index(self, **kwargs):
        return self.get_queryset(user=self.state['auth'])
    
    def get_changelist_kwargs(self):
        kwargs = super(ModelResource, self).get_changelist_kwargs()
        kwargs.update({'list_filter': self.list_filter,
                       'search_fields': self.search_fields,
                       'date_hierarchy': self.date_hierarchy,})
        return kwargs
    
    def lookup_allowed(self, lookup, value):
        return True #TODO
    
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
    
    def get_item_embedded_links(self, item):
        links = super(ModelResource, self).get_item_embedded_links(item=item)
        inline_links = list()
        for inline in self.inline_instances:
            inline = inline.fork_state(parent=item.instance, auth=self.state['auth'])
            url = inline.get_absolute_url()
            link = Link(url=url,
                        resource=inline,
                        prompt='inlines: %s' % inline.get_prompt(),
                        rel='inline-%s' % inline.rel_name,)
            inline_links.append(link)
        return links + inline_links
    
    def get_namespaces(self):
        namespaces = super(ModelResource, self).get_namespaces()
        if self.state.item is not None and self.state.get('view_class', None) == 'change_form':
            from hyperadmin.hyperobjects import Namespace
            
            for inline in self.inline_instances:
                name = 'inline-%s' % inline.rel_name
                inline = inline.fork_state(parent=self.state.item.instance, auth=self.state['auth'], namespace=name)
                link = inline.get_resource_link()
                namespace = Namespace(name=name, link=link, state=inline.state)
                namespaces[name] = namespace
        return namespaces
    
    def get_item_namespaces(self, item):
        namespaces = super(ModelResource, self).get_item_namespaces(item)
        from hyperadmin.hyperobjects import Namespace
        
        for inline in self.inline_instances:
            name = 'inline-%s' % inline.rel_name
            inline = inline.fork_state(parent=item.instance, auth=self.state['auth'], namespace=name)
            link = inline.get_resource_link()
            namespace = Namespace(name=name, link=link, state=inline.state)
            namespaces[name] = namespace
        return namespaces

class InlineModelResource(ModelResource):
    list_view = views.InlineModelListView
    add_view = views.InlineModelCreateView
    detail_view = views.InlineModelDetailView
    delete_view = views.InlineModelDeleteView
    
    model = None
    fk_name = None
    rel_name = None
    
    def __init__(self, parent):
        super(InlineModelResource, self).__init__(resource_adaptor=self.model, site=parent.site, parent_resource=parent)
        
        from django.db.models.fields.related import RelatedObject
        from django.forms.models import _get_foreign_key
        self.fk = _get_foreign_key(self.parent.resource_adaptor, self.model, self.fk_name)
        if self.rel_name is None:
            self.rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
        self.inline_instances = []
    
    def get_queryset(self, parent, user):
        queryset = self.resource_adaptor.objects.all()
        queryset = queryset.filter(**{self.fk.name:parent})
        if not self.has_change_permission(user):
            queryset = queryset.none()
        return queryset
    
    def get_active_index(self, **kwargs):
        return self.get_queryset(parent=self.state['parent'], user=self.state['auth'])
    
    def get_base_url_name(self):
        return '%s_%s_%s_' % (self.parent.app_name, self.parent.resource_name, self.rel_name)
    
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
        pk = self.state['parent'].pk
        return self.reverse('%sadd' % self.get_base_url_name(), pk=pk)
    
    def get_delete_url(self, item):
        instance = item.instance
        pk = getattr(instance, self.fk.name).pk
        return self.reverse('%sdelete' % self.get_base_url_name(), pk=pk, inline_pk=instance.pk)
    
    def get_item_url(self, item):
        instance = item.instance
        pk = getattr(instance, self.fk.name).pk
        return self.reverse('%sdetail' % self.get_base_url_name(), pk=pk, inline_pk=instance.pk)
    
    def get_absolute_url(self):
        pk = self.state['parent'].pk
        return self.reverse('%slist' % self.get_base_url_name(), pk=pk)
    
    def get_breadcrumbs(self):
        breadcrumbs = self.parent.get_breadcrumbs()
        parent_item = self.parent.get_resource_item(self.state['parent'])
        breadcrumbs.append(self.parent.get_item_breadcrumb(parent_item))
        breadcrumbs.append(self.get_breadcrumb())
        if self.state.item:
            breadcrumbs.append(self.get_item_breadcrumb(self.state.item))
        return breadcrumbs
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        class AdminForm(forms.ModelForm):
            state = self.state
            
            def save(self, commit=True):
                instance = super(AdminForm, self).save(commit=False)
                setattr(instance, self.state['resource'].fk.name, self.state['parent'])
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
        links = super(InlineModelResource, self).get_ln_links()
        if self.state.namespace:
            for item in self.get_resource_items():
                links.append(self.get_update_link(item))
        return links
    
    def get_idempotent_links(self):
        links = super(InlineModelResource, self).get_idempotent_links()
        if self.state.namespace:
            for item in self.get_resource_items():
                links.append(self.get_delete_link(item))
        return links

