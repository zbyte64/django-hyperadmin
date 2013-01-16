from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources import BaseResource
from hyperadmin.resources.directory.forms import ViewResourceForm
from hyperadmin.resources.directory.endpoints import ListEndpoint


#CONSIDER: is this really an EndpointDirectory?
class ResourceDirectory(BaseResource):
    resource_class = 'resourcelisting'
    form_class = ViewResourceForm
    
    def __init__(self, **kwargs):
        kwargs.setdefault('resource_adaptor', dict())
        super(ResourceDirectory, self).__init__(**kwargs)
    
    def get_app_name(self):
        return getattr(self, '_app_name', None)
    
    def set_app_name(self, name):
        self._app_name = name
    
    app_name = property(get_app_name, set_app_name)
    
    def get_resource_name(self):
        return self._resource_name
    
    def set_resource_name(self, name):
        self._resource_name = name
    
    resource_name = property(get_resource_name, set_resource_name)
    
    def get_view_endpoints(self):
        endpoints = super(ResourceDirectory, self).get_view_endpoints()
        endpoints.append((ListEndpoint, {}))
        return endpoints
    
    def get_urls(self):
        urlpatterns = super(ResourceDirectory, self).get_urls()
        for key, resource in self.resource_adaptor.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(resource.urls))
            )
        return urlpatterns
    
    def register_resource(self, resource, key=None):
        if key is None:
            key = resource.get_resource_name()
        self.resource_adaptor[key] = resource
    
    def fork(self, **kwargs):
        ret = super(ResourceDirectory, self).fork(**kwargs)
        ret.resource_adaptor.update(self.resource_adaptor)
        return ret
    
    def get_instances(self):
        applications = self.resource_adaptor.items()
        apps = [entry[1] for entry in sorted(applications, key=lambda x: x[0])]
        all_apps = list()
        for app in apps:
            app = self.api_request.get_endpoint(app.get_url_name())
            all_apps.append(app)
            if isinstance(app, ResourceDirectory):
                all_apps.extend(app.get_instances())
        return all_apps
    
    
    def get_item_prompt(self, item):
        return item.instance.get_prompt()
    
    def get_item_url(self, item):
        if hasattr(item.instance, 'get_absolute_url'):
            return item.instance.get_absolute_url()
    
    def get_item_outbound_links(self, item):
        return item.instance.links.get_outbound_links()
    
    def get_prompt(self):
        return self.resource_name
    
    def __unicode__(self):
        return u'Resource Directory: %s' % self.get_prompt()

