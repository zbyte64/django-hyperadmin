from django.conf.urls.defaults import patterns, url, include

from hyperadmin.hyperobjects import Link, ResourceItem
from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views

class ApplicationResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.ApplicationResourceView
    
    def __init__(self, app_name, site):
        self._app_name = app_name
        self.resource_adaptor = dict() #TODO OrderedDict
        self.site = site
    
    def get_app_name(self):
        return self._app_name
    app_name = property(get_app_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name=self.app_name),
        )
        for key, resource in self.resource_adaptor.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(resource.urls))
            )
        return urlpatterns
    
    def register_resource(self, resource):
        key = resource.get_resource_name()
        self.resource_adaptor[key] = resource
    
    def get_items(self, request):
        #TODO sort by name
        return self.resource_adaptor.values()
    
    def get_embedded_links(self, instance=None):
        #relationships go here
        return []
    
    def get_outbound_links(self, instance=None):
        if instance:
            return []
        else:
            site_link = Link(url=self.reverse('index'), rel='breadcrumb', prompt='root')
            app_link = Link(url=self.get_absolute_url(), rel='breadcrumb', prompt=self.app_name)
            return [site_link, app_link]
    
    def get_instance_url(self, instance):
        if hasattr(instance, 'get_absolute_url'):
            return instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse(self.app_name)
    
    def get_child_resource_links(self):
        links = list()
        for key, resource in self.resource_adaptor.iteritems():
            resource_link = Link(url=resource.get_absolute_url(), rel='child-resource', prompt=resource.resource_name)
            links.append(resource_link)
        return links
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

