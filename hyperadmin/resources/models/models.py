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
    
    def get_instances(self, state):
        if 'paginator' in state:
            return state['paginator'].object_list
        return self.get_queryset(state['auth'])
    
    def get_changelist_kwargs(self, state):
        kwargs = super(ModelResource, self).get_changelist_kwargs(state)
        kwargs.update({'list_filter': self.list_filter,
                       'search_fields': self.search_fields,
                       'date_hierarchy': self.date_hierarchy,})
        return kwargs
    
    def get_templated_queries(self, state):
        links = super(ModelResource, self).get_templated_queries(state)
        if state and 'changelist' in state:
            links += self.get_changelist_links(state)
        return links
    
    def get_changelist_links(self, state):
        links = self.get_changelist_sort_links(state)
        links += self.get_changelist_filter_links(state)
        links += self.get_pagination_links(state)
        #links.append(self.get_search_link())
        return links
    
    def get_changelist_sort_links(self, state):
        links = list()
        changelist = state['changelist']
        from django.contrib.admin.templatetags.admin_list import result_headers
        for header in result_headers(changelist):
            if header.get("sortable", False):
                prompt = unicode(header["text"])
                classes = ["sortby"]
                if "url" in header:
                    links.append(self.get_resource_link(url=header["url"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                else:
                    if header["ascending"]:
                        classes.append("ascending")
                    if header["sorted"]:
                        classes.append("sorted")
                    links.append(self.get_resource_link(url=header["url_primary"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                    links.append(self.get_resource_link(url=header["url_remove"], prompt=prompt, classes=classes+["remove"], rel="sortby"))
                    links.append(self.get_resource_link(url=header["url_toggle"], prompt=prompt, classes=classes+["toggle"], rel="sortby"))
        return links
    
    def get_changelist_filter_links(self, state):
        links = list()
        changelist = state['changelist']
        for spec in changelist.filter_specs:
            choices = spec.choices(changelist)
            for choice in choices:
                classes = ["filter"]
                if choice['selected']:
                    classes.append("selected")
                title = spec.title
                if callable(title):
                    title = title()
                prompt = u"%s: %s" % (title, choice['display'])
                links.append(self.get_resource_link(url=choice['query_string'], prompt=prompt, classes=classes, rel="filter"))
        return links
    
    def get_search_link(self, state):
        pass
    
    def get_pagination_links(self, state):
        links = list()
        changelist = state['changelist']
        paginator, page_num = changelist.paginator, changelist.page_num
        from django.contrib.admin.templatetags.admin_list import pagination
        from django.contrib.admin.views.main import PAGE_VAR
        ctx = pagination(changelist)
        classes = ["pagination"]
        for page in ctx["page_range"]:
            if page == '.':
                continue
            url = changelist.get_query_string({PAGE_VAR: page})
            links.append(self.get_resource_link(url=url, prompt=u"%s" % page, classes=classes, rel="pagination"))
        if ctx["show_all_url"]:
            links.append(self.get_resource_link(url=ctx["show_all_url"], prompt="show all", classes=classes, rel="pagination"))
        return links
    
    def lookup_allowed(self, lookup, value):
        return True #TODO
    
    def get_queryset(self, user):
        queryset = self.resource_adaptor.objects.all()
        if not self.has_change_permission(user):
            queryset = queryset.none()
        return queryset
    
    def get_active_index(self, state, **kwargs):
        return self.get_queryset(user=state['auth'])

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
                        prompt='inlines: %s' % inline.get_prompt(),
                        rel='inline-%s' % inline.rel_name,)
            inline_links.append(link)
        return links + inline_links

class InlineModelResource(ModelResource):
    list_view = views.InlineModelListView
    add_view = views.InlineModelCreateView
    detail_view = views.InlineModelDetailView
    delete_view = views.InlineModelDeleteView
    
    model = None
    fk_name = None
    rel_name = None
    
    def __init__(self, parent):
        self.resource_adaptor = self.model
        self.site = parent.site
        self.parent = parent
        
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
    
    def get_active_index(self, state, **kwargs):
        return self.get_queryset(parent=state['parent'], user=state['auth'])
    
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
            return self.parent.get_absolute_url()
        return None

