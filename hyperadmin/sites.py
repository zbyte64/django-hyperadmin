from django.utils.datastructures import SortedDict

from hyperadmin.endpoints import RootEndpoint
from hyperadmin.resources.directory import ResourceDirectory
from hyperadmin.resources.auth import AuthResource
from hyperadmin.throttle import Throttle

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
    throttle = Throttle(throttle_at=1200)
    name = 'hyperadmin'
    
    def __init__(self, **kwargs):
        self.registry = dict()
        kwargs.setdefault('namespace', kwargs.get('name', self.name))
        super(BaseResourceSite, self).__init__(**kwargs)
    
    def post_register(self):
        super(BaseResourceSite, self).post_register()
        self.directory_resource = self.create_directory_resource(base_url_name_suffix=self.base_url_name_suffix)
    
    def get_directory_resource_kwargs(self, **kwargs):
        kwargs.setdefault('resource_name', self.name)
        #kwargs.setdefault('parent', self)
        return self.get_resource_kwargs(**kwargs)
    
    def create_directory_resource(self, **kwargs):
        params = self.get_directory_resource_kwargs(**kwargs)
        return self.directory_resource_class(**params)
    
    def get_children_endpoints(self):
        return [self.directory_resource]
    
    def get_index_endpoint(self):
        return self.directory_resource
    
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
        from django.forms import FileField
        if hasattr(field, 'field'): #CONSIDER internally we use boundfield
            field = field.field
        widget = field.widget
        if isinstance(widget, widgets.Input):
            return widget.input_type
        if isinstance(widget, widgets.CheckboxInput):
            return 'checkbox'
        if isinstance(widget, widgets.Select):
            #if widget.allow_multiple_selected
            return 'select'
        if isinstance(field, FileField):
            return 'file'
        self.get_logger().warning('Unhandled widget type: %s' % type(widget))
        return 'text'
    
    def get_media_resource_urlname(self):
        return '%s_-storages_media_resource' % self.base_url_name_suffix
    
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
    
    def api_permission_check(self, api_request, endpoint):
        response = self.throttle.throttle_check(api_request, endpoint)
        if response:
            return response
        return super(BaseResourceSite, self).api_permission_check(api_request, endpoint)

class ResourceSite(BaseResourceSite):
    '''
    A Resource Site that is suited for administrative purposes. By 
    default the user must be a staff user.
    '''
    auth_resource_class = AuthResource
    name = 'hyperadmin'
    base_url_name_suffix = 'admin'
    
    def post_register(self):
        super(ResourceSite, self).post_register()
        self.auth_resource = self.register_endpoint(self.auth_resource_class)
    
    @property
    def applications(self):
        return self.directory_resource.resource_adaptor
    
    def register(self, model_or_iterable, admin_class, **options):
        if isinstance(model_or_iterable, collections.Iterable) and not isinstance(model_or_iterable, basestring):
            resources = list()
            for model in model_or_iterable:
                resources.append(self.register(model, admin_class, **options))
            return resources
        model = model_or_iterable
        app_name = options.pop('app_name')
        app_resource = self.register_application(app_name)
        options.setdefault('parent', app_resource)
        kwargs = self.get_resource_kwargs(resource_adaptor=model, **options)
        resource = admin_class(**kwargs)
        self.applications[app_name].register_resource(resource)
        self.registry[model] = resource
        return resource
    
    def register_application(self, app_name, app_class=None, **options):
        if app_name not in self.applications:
            if app_class is None:
                app_class = self.directory_resource_class
            app_resource = self.register_endpoint(app_class, app_name=self.name, resource_name=app_name)
            assert app_name in self.applications
        return self.applications[app_name]
    
    def get_login_link(self, api_request, **kwargs):
        auth_resource = api_request.get_endpoint(self.auth_resource.get_url_name())
        return auth_resource.get_link(**kwargs)
    
    def api_permission_check(self, api_request, endpoint):
        user = api_request.user
        if not user.is_authenticated():
            return self.get_login_link(api_request, prompt='Login Required')
        if not user.is_staff:
            return self.get_login_link(api_request, prompt='Unauthorized', http_status=401)
        return super(ResourceSite, self).api_permission_check(api_request, endpoint)
    
    def get_actions(self, request):
        return SortedDict()
    
    def install_models_from_site(self, site):
        from hyperadmin.resources.models.autoload import DEFAULT_LOADER
        
        loader = DEFAULT_LOADER(root_endpoint=self, admin_site=site)
        loader.register_resources()
    
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
        app_name = '-storages'
        self.register(media_storage, media_resource_class, resource_name='media', app_name=app_name)
        self.register(static_storage, static_resource_class, resource_name='static', app_name=app_name)

class GlobalSite(BaseResourceSite):
    '''
    A Resource Site that is meant for globally registering endpoints 
    without needing to explicitly create a Resource Site.
    '''
    name = 'apisite'
    
    def get_resolver(self):
        from django.core.urlresolvers import get_resolver
        return get_resolver(None)

site = ResourceSite()
site.register_builtin_media_types()

global_site = GlobalSite()
global_site.register_builtin_media_types()
