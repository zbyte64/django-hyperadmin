from django.utils.datastructures import SortedDict

from hyperadmin.endpoints import RootEndpoint
from hyperadmin.resources.directory import ResourceDirectory
from hyperadmin.resources.auth import AuthResource

import collections


class Registry(dict):
    def __init__(self, resource_site):
        self.resource_site = resource_site
    
    def __getitem__(self, key):
        item = super(Registry, self).__getitem__(key)
        if self.resource_site.api_request:
            return self.resource_site.api_request.get_endpoint(item.get_url_name())
        return item
    
    def items(self):
        items = super(Registry, self).items()
        if self.resource_site.api_request:
            items = [(key, self[key]) for key, val in items]
        return items

class BaseResourceSite(RootEndpoint):
    directory_resource_class = ResourceDirectory
    name = 'hyperadmin'
    
    def __init__(self, **kwargs):
        self.registry = dict()
        kwargs.setdefault('namespace', kwargs.get('name', self.name))
        super(BaseResourceSite, self).__init__(**kwargs)
    
    def post_register(self):
        super(BaseResourceSite, self).post_register()
        self.directory_resource = self.create_directory_resource()
    
    def get_directory_resource_kwargs(self, **kwargs):
        kwargs.setdefault('resource_name', self.name)
        return self.get_resource_kwargs(**kwargs)
    
    def create_directory_resource(self):
        return self.directory_resource_class(**self.get_directory_resource_kwargs())
    
    def get_urls(self):
        urlpatterns = self.get_extra_urls()
        urlpatterns += self.directory_resource.get_urls()
        return urlpatterns
    
    def get_link(self, **kwargs):
        return self.directory_resource.get_link(**kwargs)
    
    def get_resource_kwargs(self, **kwargs):
        params = {'site': self,
                  'api_request': self.api_request,}
        params.update(kwargs)
        return params
    
    def get_endpoint_kwargs(self, **kwargs):
        kwargs.setdefault('parent', self.directory_resource)
        params = self.get_resource_kwargs(**kwargs)
        return params
    
    def fork(self, **kwargs):
        ret = super(BaseResourceSite, self).fork(**kwargs)
        ret.registry.update(self.registry)
        ret.directory_resource.resource_adaptor.update(self.directory_resource.resource_adaptor)
        return ret
    
    def register_endpoint(self, klass, **options):
        kwargs = self.get_endpoint_kwargs(**options)
        endpoint = klass(**kwargs)
        if 'resource_adaptor' in kwargs:
            self.registry[kwargs['resource_adaptor']] = endpoint
        self.directory_resource.register_resource(endpoint)
        return endpoint
    
    #TODO review the following for inclusion into RootEndpoint
    def register_builtin_media_types(self):
        from mediatypes import BUILTIN_MEDIA_TYPES
        for key, value in BUILTIN_MEDIA_TYPES.iteritems():
            self.register_media_type(key, value)
    
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
        self.get_logger().warning('Unhandled widget type: %s' % type(widget))
        return 'text'
    
    def get_media_resource_urlname(self):
        return '-storages_media_resource'
    
    def get_media_resource(self):
        urlname = self.get_media_resource_urlname()
        return self.api_request.get_endpoint(urlname)
    
    def get_related_resource_from_field(self, field):
        #TODO make more dynamic
        from django.forms import FileField
        from django.forms.models import ModelChoiceField
        if hasattr(field, 'field'): #CONSIDER internally we use boundfield
            field = field.field
        if isinstance(field, ModelChoiceField):
            model = field.queryset.model
            if model in self.registry:
                resource = self.registry[model]
                return self.api_request.get_endpoint(resource.get_url_name())
        if isinstance(field, FileField):
            return self.get_media_resource().link_prototypes['upload'].get_url()
        return None

class ResourceSite(BaseResourceSite):
    auth_resource_class = AuthResource
    name = 'hyperadmin'
    
    def post_register(self):
        super(ResourceSite, self).post_register()
        self.auth_resource = self.register_endpoint(self.auth_resource_class)
    
    @property
    def applications(self):
        return self.directory_resource.resource_adaptor
    
    def register(self, model_or_iterable, admin_class, **options):
        if isinstance(model_or_iterable, collections.Iterable):
            resources = list()
            for model in model_or_iterable:
                resources.append(self.register(model, admin_class, **options))
            return resources
        model = model_or_iterable
        kwargs = self.get_resource_kwargs(resource_adaptor=model, **options)
        resource = admin_class(**kwargs)
        app_name = resource.app_name
        resource.parent = self.register_application(app_name)
        resource._init_kwargs['parent'] = resource.parent
        self.applications[app_name].register_resource(resource)
        self.registry[model] = resource
        return resource
    
    def register_application(self, app_name, app_class=None, **options):
        if app_name not in self.applications:
            if app_class is None:
                app_class = self.directory_resource_class
            app_resource = self.register_endpoint(app_class, app_name=self.name, resource_name=app_name)
            self.applications[app_name] = app_resource
        return self.applications[app_name]
    
    def get_login_link(self, api_request, **kwargs):
        auth_resource = api_request.get_endpoint(self.auth_resource.get_url_name())
        return auth_resource.get_link(**kwargs)
    
    def api_permission_check(self, api_request):
        user = api_request.user
        if not user.is_authenticated():
            return self.get_login_link(api_request, prompt='Login Required')
        if not user.is_staff:
            return self.get_login_link(api_request, prompt='Unauthorized', http_status=401)
    
    def get_actions(self, request):
        return SortedDict()
    
    def generate_model_resource_from_admin_model(self, admin_model):
        from hyperadmin.resources.models import ModelResource
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
            inlines = list()
            
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
        from hyperadmin.resources.models import InlineModelResource
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
                    self.get_logger.exception('Could not autoload inline: %s' % inline_cls)
                else:
                    resource.inlines.append(GeneratedInlineModelResource)
    
    def install_storage_resources(self, media_resource_class=None, static_resource_class=None):
        from hyperadmin.resources.storages import StorageResource
        from django.core.files.storage import default_storage as media_storage
        try:
            from django.contrib.staticfiles.storage import staticfiles_storage as static_storage
        except ImportError:
            from django.conf import settings
            from django.core.files.storage import get_storage_class
            static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
        if media_resource_class is None:
            media_resource_class = StorageResource
        if static_resource_class is None:
            static_resource_class = StorageResource
        self.register(media_storage, media_resource_class, resource_name='media')
        self.register(static_storage, static_resource_class, resource_name='static')


site = ResourceSite()
site.register_builtin_media_types()

