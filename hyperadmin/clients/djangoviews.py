from django.conf.urls.defaults import patterns, url

from hyperadmin.clients.common import Client
#from hyperadmin.hyperobjects import patch_global_state


class BaseDjangoViewsClient(Client):
    """
    Host a set of django views that proxy to an api endpoint.
    
    Under the hood we create a new api with our own set of endpoints.
    """
    
    #set to False is we should respect the api endpoint's auth requirements
    public = True
    
    def __init__(self, api_endpoint, name='hyper-client', app_name='client'):
        super(BaseDjangoViewsClient, self).__init__(api_endpoint, name=name, app_name=app_name)
    
    def get_view_kwargs(self, **kwargs):
        params = {'client_site':self,}
        params.update(kwargs)
        return params
    
    def get_view_endpoints(self):
        """
        Returns a list of dictionaries containing the following elements:
        
        * url: relative regex url
        * view: the view object
        * name: name for urlresolver
        """
        return []
    
    def get_urls(self):
        urlpatterns = patterns('',)
        for endpoint in self.get_view_endpoints():
            urlpatterns += patterns('',
                url(endpoint['url'],
                    endpoint['view'],
                    name=endpoint['name'],),
            )
        return urlpatterns
    
    def api_permission_check(self, request):
        if not self.public:
            return self.api_endpoint.api_permission_check(request)
    
    def get_related_resource_from_field(self, field):
        return self.api_endpoint.get_related_resource_from_field(field)
    
    def get_html_type_from_field(self, field):
        return self.api_endpoint.get_html_type_from_field(field)
    
    @property
    def state(self):
        return self.api_endpoint.state
    
    @property
    def media_types(self):
        return self.api_endpoint.media_types

class DjangoViewsClient(BaseDjangoViewsClient):
    """
    view_endpoint_defs = [
        {'url':r'/path/',
         'view_class':ListView,
         'resource':site.get_resource(MyModel),
         'endpoint_name':'app_resource_list', #consider, can we detect this?
         'name':'myview_list' or None,}
    ]
    """
    view_endpoint_defs = []
    
    def __init__(self, *args, **kwargs):
        super(DjangoViewsClient, self).__init__(*args, **kwargs)
        self.view_endpoints = list()
    
    def register_view_endpoint(self, url, view_class, resource, endpoint_name, name=None, options={}):
        view_kwargs = self.get_view_kwargs(resource=resource, url_name=endpoint_name, **options)
        
        self.view_endpoints.append({
            'url': url,
            'view': view_class.as_view(**view_kwargs),
            'name': name or endpoint_name,
        })
    
    def get_view_endpoints(self):
        endpoints = super(DjangoViewsClient, self).get_view_endpoints()
        for entry in self.view_endpoint_defs:
            view_class = entry['view_class']
            view_kwargs = self.get_view_kwargs(resource=entry['resource'], url_name=entry['endpoint_name'])
            
            endpoints.append({
                'url': entry['url'],
                'view': view_class.as_view(**view_kwargs),
                'name': entry.get('name', entry['endpoint_name']),
            })
        endpoints.extend(self.view_endpoints)
        return endpoints

