from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.defaults import patterns
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.functional import update_wrapper
from django.http import HttpResponse
from django.utils.encoding import iri_to_uri

from hyperadmin.resources.applications.site import SiteResource
from hyperadmin.resources.applications.application import ApplicationResource

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
            resources = list()
            for model in model_or_iterable:
                resources.append(self.register(model, admin_class, **options))
            return resources
        model = model_or_iterable
        resource = admin_class(resource_adaptor=model, site=self, **options)
        app_name = resource.app_name
        if app_name not in self.applications:
            self.applications[app_name] = self.application_resource_class(app_name, self)
        resource.parent = self.applications[app_name] #TODO clean up
        self.applications[app_name].register_resource(resource)
        self.registry[model] = resource
        return resource
    
    def register_media_type(self, media_type, media_type_handler):
        self.media_types[media_type] = media_type_handler
    
    def get_resource(self, resource_adaptor):
        return self.registry[resource_adaptor]
    
    def get_resource_item(self, instance, resource_adaptor=None):
        if resource_adaptor is None:
            resource_adaptor = type(instance)
        resource = self.get_resource(resource_adaptor)
        return resource.get_resource_item(instance)
    
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
        
        def permission_check(view):
            def wrapper(request, *args, **kwargs):
                response = self.api_permission_check(request)
                if response:
                    return response
                return view(request, *args, **kwargs)
            return update_wrapper(wrapper, view)
        
        return csrf_exempt(permission_check(view))
    
    def api_permission_check(self, request):
        if not request.user.is_staff:
            redirect_to = self.reverse('authentication')
            response = HttpResponse('Unauthorized', status=401)
            response['Location'] = iri_to_uri(redirect_to)
            return response
    
    def as_nonauthenticated_view(self, view, cacheable=False):
        if not cacheable:
            view = never_cache(view)
        return csrf_exempt(view)
    
    def get_related_resource_from_field(self, field):
        #TODO make more dynamic
        from django.forms import FileField
        from django.forms.models import ModelChoiceField
        form = field.form
        if hasattr(field, 'field'): #CONSIDER internally we use boundfield
            field = field.field
        if isinstance(field, ModelChoiceField):
            model = field.queryset.model
            if model in self.registry:
                return self.registry[model]
        if isinstance(field, FileField):
            return self.applications['-storages'].resource_adaptor['media']
        return None
    
    def get_html_type_from_field(self, field):
        #TODO fill this out, datetime, etc
        from django.forms import widgets
        widget = field.field.widget
        if isinstance(widget, widgets.Input):
            return widget.input_type
        if isinstance(widget, widgets.CheckboxInput):
            return 'checkbox'
        if isinstance(widget, widgets.Select):
            #if widget.allow_multiple_selected
            return 'select'
        print 'Uhandled:', type(widget)
        return 'text'
    
    def register_builtin_media_types(self):
        from mediatypes import BUILTIN_MEDIA_TYPES
        for key, value in BUILTIN_MEDIA_TYPES.iteritems():
            self.register_media_type(key, value)
    
    def reverse(self, name, *args, **kwargs):
        return reverse('%s:%s' % (self.name, name), args=args, kwargs=kwargs)#, current_app=self.app_name)
    
    def get_actions(self, request):
        return SortedDict()
    
    def generate_model_resource_from_admin_model(self, admin_model):
        from hyperadmin.resources.models.models import ModelResource
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
            list_display = list(admin_model.list_display)
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
        
        if 'action_checkbox' in GeneratedModelResource.list_display:
            GeneratedModelResource.list_display.remove('action_checkbox')
        
        if admin_model.form != forms.ModelForm:
            GeneratedModelResource.form_class = admin_model.form
        
        return GeneratedModelResource
    
    def install_models_from_site(self, site):
        from hyperadmin.resources.models.models import InlineModelResource
        from django.contrib.admin import ModelAdmin
        for model, admin_model in site._registry.iteritems():
            if model in self.registry:
                continue
            if not isinstance(admin_model, ModelAdmin):
                continue
            admin_class = self.generate_model_resource_from_admin_model(admin_model)
            resource = self.register(model, admin_class)
            for inline_cls in admin_model.inlines:
                class GeneratedInlineModelResource(InlineModelResource):
                    model = inline_cls.model
                    fields = inline_cls.fields
                    exclude = inline_cls.exclude
                try:
                    resource.register_inline(GeneratedInlineModelResource)
                except:
                    pass #too much customization for us to handle!
    
    def install_storage_resources(self):
        from hyperadmin.resources.storages.storages import StorageResource
        from django.core.files.storage import default_storage as media_storage
        try:
            from django.contrib.staticfiles.storage import staticfiles_storage as static_storage
        except ImportError:
            from django.conf import settings
            from django.core.files.storage import get_storage_class
            static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
        self.register(media_storage, StorageResource, resource_name='media')
        self.register(static_storage, StorageResource, resource_name='static')


site = ResourceSite()
site.register_builtin_media_types()

