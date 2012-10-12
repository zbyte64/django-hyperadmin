from django.conf.urls.defaults import patterns, url, include

from hyperadmin.resources import BaseResource
from hyperadmin.resources.applications import views

class SiteResource(BaseResource):
    resource_class = 'resourcelisting'
    list_view = views.SiteResourceView
    
    def __init__(self, site, auth_resource=None):
        super(SiteResource, self).__init__(resource_adaptor=dict(), site=site)
        if auth_resource is None:
            from hyperadmin.resources.auth.auth import AuthResource
            auth_resource = AuthResource
        self.auth_resource = auth_resource(site=site)
    
    def get_prompt(self):
        return self.site.name
    
    def get_app_name(self):
        return self.site.name
    app_name = property(get_app_name)
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            return self.as_view(view, cacheable)
        
        init = self.get_view_kwargs()
        
        # Admin-site-wide views.
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('',
            url(r'^$',
                wrap(self.list_view.as_view(**init)),
                name='index'),
            url(r'^-authentication/',
                include(self.auth_resource.urls)),
        )
        for key, app in self.applications.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % key, include(app.urls))
            )
        return urlpatterns
    
    def get_item_prompt(self, item):
        return item.instance.get_prompt()
    
    def get_items(self):
        applications = self.applications.items()
        apps = [entry[1] for entry in sorted(applications, key=lambda x: x[0])]
        all_apps = list()
        for app in apps:
            all_apps.append(app)
            all_apps.extend(app.get_items())
        all_apps.append(self.auth_resource)
        return all_apps
    
    def get_resource_items(self):
        return [self.get_resource_item(item) for item in self.get_items()]
    
    def get_item_url(self, item):
        if hasattr(item.instance, 'get_absolute_url'):
            return item.instance.get_absolute_url()
    
    def get_item_embedded_links(self, item):
        #relationships go here
        if hasattr(item.instance, 'get_child_resource_links'): #AKA application resource
            return item.instance.get_child_resource_links()
        return []
    
    def get_absolute_url(self):
        return self.reverse('index')
    
    @property
    def applications(self):
        return self.site.applications

