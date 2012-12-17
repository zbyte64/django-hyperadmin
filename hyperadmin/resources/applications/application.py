from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views
from hyperadmin.resources.applications.forms import ViewResourceForm
from hyperadmin.resources.applications.endpoints import ListEndpoint


class ApplicationResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.ApplicationResourceView
    form_class = ViewResourceForm
    
    def __init__(self, **kwargs):
        kwargs.setdefault('resource_adaptor', dict())
        super(ApplicationResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        return self._app_name
    
    def set_app_name(self, name):
        self._app_name = name
    
    app_name = property(get_app_name, set_app_name)
    
    def get_view_endpoints(self):
        endpoints = super(ApplicationResource, self).get_view_endpoints()
        endpoints.append(ListEndpoint(resource=self, site=self.site))
        return endpoints
    
    def get_urls(self):
        urlpatterns = super(ApplicationResource, self).get_urls()
        for key, resource in self.resource_adaptor.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(resource.urls))
            )
        return urlpatterns
    
    def register_resource(self, resource):
        key = resource.get_resource_name()
        self.resource_adaptor[key] = resource
    
    def get_instances(self):
        #TODO sort by name
        return self.resource_adaptor.values()
    
    def get_item_prompt(self, item):
        return item.instance.get_prompt()
    
    def get_item_url(self, item):
        if hasattr(item.instance, 'get_absolute_url'):
            return item.instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.link_prototypes['list'].get_url()
    
    def get_item_outbound_links(self, item):
        return item.instance.links.get_outbound_links()
    
    def get_prompt(self):
        return self.app_name.replace('-',' ').replace('_', ' ')
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

