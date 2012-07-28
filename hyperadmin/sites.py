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
        return reverse('%s:%s' % (self.site.name, name), args=args, kwargs=kwargs, current_app=self.app_name)
    
    def get_actions(self, request):
        return SortedDict()


site = ResourceSite()
site.register_builtin_media_types()

