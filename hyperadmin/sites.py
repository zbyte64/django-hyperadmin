from django.views.decorators.cache import never_cache
from django.conf.urls.defaults import patterns
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict

from resources import SiteResource, ApplicationResource

import collections

class ResourceSite(object):
    site_resource_class = SiteResource
    application_resource_class = ApplicationResource
    
    def __init__(self, name='hyperadmin'):
        self.name = name
        self.media_types = dict()
        self.applications = dict()
        self.registry = dict()
        self.site_resource = self.site_resource_class(self)
    
    def register(self, model_or_iterable, admin_class, **options):
        if isinstance(model_or_iterable, collections.Iterable):
            for model in model_or_iterable:
                self.register(model, admin_class, **options)
            return
        model = model_or_iterable
        resource = admin_class(model, self)
        app_name = resource.app_name
        if app_name not in self.applications:
            self.applications[app_name] = self.application_resource_class(app_name, self)
        self.applications[app_name].register_resource(resource)
        self.registry[model] = resource
    
    def register_media_type(self, media_type, media_type_handler):
        self.media_types[media_type] = media_type_handler
    
    def get_urls(self):
        urlpatterns = self.get_extra_urls()
        urlpatterns += self.site_resource.get_urls()
        return urlpatterns
    
    def get_extra_urls(self):
        return patterns('',)
    
    def urls(self):
        return self.get_urls(), None, self.name
    urls = property(urls)
    
    def get_view_kwargs(self):
        return {'resource_site':self,}
    
    def as_view(self, view, cacheable=False):
        if not cacheable:
            view = never_cache(view)
        return view
    
    def register_builtin_media_types(self):
        from mediatypes import BUILTIN_MEDIA_TYPES
        for key, value in BUILTIN_MEDIA_TYPES.iteritems():
            self.register_media_type(key, value)
    
    def reverse(self, name, *args, **kwargs):
        return reverse('%s:%s' % (self.name, name), args=args, kwargs=kwargs)#, current_app=self.app_name)
    
    def get_actions(self, request):
        return SortedDict()
    
    def generate_model_resource_from_admin_model(self, admin_model):
        from resources import ModelResource
        from django import forms
        class GeneratedModelResource(ModelResource):
            #raw_id_fields = ()
            fields = admin_model.fields
            exclude = admin_model.exclude
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
            paginator = admin_model.paginator
            #inlines = []
            
            #list display options
            list_display = admin_model.list_display
            #list_display_links = ()
            list_filter = admin_model.list_filter
            list_select_related = admin_model.list_select_related
            list_per_page = admin_model.list_per_page
            list_max_show_all = getattr(admin_model, 'list_max_show_all', 200)
            list_editable = admin_model.list_editable
            search_fields = admin_model.search_fields
            date_hierarchy = admin_model.date_hierarchy
            ordering = admin_model.ordering
            form_class = getattr(admin_model, 'form_class', None)
        
        if admin_model.form != forms.ModelForm:
            GeneratedModelResource.form_class = admin_model.form
        
        return GeneratedModelResource
    
    def install_models_from_site(self, site):
        for model, admin_model in site._registry.iteritems():
            if model in self.registry:
                continue
            admin_class = self.generate_model_resource_from_admin_model(admin_model)
            self.register(model, admin_class)


site = ResourceSite()
site.register_builtin_media_types()

