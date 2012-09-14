from django.conf.urls.defaults import patterns, url, include

from hyperadmin.hyperobjects import Link, ResourceItem, CollectionResourceItem
from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views

class ApplicationResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.ApplicationResourceView
    
    def __init__(self, app_name, site):
        self._app_name = app_name
        self.resource_adaptor = dict() #TODO OrderedDict
        self.site = site
        self.parent = site.site_resource
    
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
    
    def get_items(self, user):
        #TODO sort by name
        return self.resource_adaptor.values()
    
    def get_embedded_links(self, instance=None):
        #relationships go here
        return []
    
    def get_instance_url(self, instance):
        if hasattr(instance, 'get_absolute_url'):
            return instance.get_absolute_url()
    
    def get_absolute_url(self):
        return self.reverse(self.app_name)
    
    def get_resource_items(self, user, filter_params=None):
        return [self.get_resource_item(item) for item in self.get_items(user)]
    
    def get_resource_link_item(self, filter_params=None):
        resource_item = CollectionResourceItem(self, None, filter_params=filter_params)
        return resource_item
    
    def get_child_resource_links(self):
        links = list()
        for key, resource in self.resource_adaptor.iteritems():
            resource_link = Link(url=resource.get_absolute_url(), resource=resource, resource_item=self.get_resource_item(resource), rel='child-resource', prompt=resource.resource_name)
            links.append(resource_link)
        return links
    
    def prompt(self):
        return self.app_name
    
    def __unicode__(self):
        return u'App Resource: %s' % self.app_name

