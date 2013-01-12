from hyperadmin.resources import BaseResource
from hyperadmin.resources.auth.forms import AuthenticationResourceForm
from hyperadmin.resources.auth.endpoints import LoginEndpoint, LogoutEndpoint


class AuthResource(BaseResource):
    form_class = AuthenticationResourceForm
    
    def __init__(self, **kwargs):
        kwargs.setdefault('app_name', '-authentication')
        kwargs.setdefault('resource_name', 'authentication')
        kwargs.setdefault('resource_adaptor', None)
        super(AuthResource, self).__init__(**kwargs)
    
    def get_app_name(self):
        return self._app_name
    
    def set_app_name(self, name):
        self._app_name = name
    
    app_name = property(get_app_name, set_app_name)
    
    def get_resource_name(self):
        return self._resource_name
    
    def set_resource_name(self, name):
        self._resource_name = name
    
    resource_name = property(get_resource_name, set_resource_name)
    
    def get_prompt(self):
        return self.resource_name
    
    def get_view_endpoints(self):
        endpoints = super(AuthResource, self).get_view_endpoints()
        endpoints.extend([
            (LoginEndpoint, {}),
            (LogoutEndpoint, {}),
        ])
        return endpoints
    
    def api_permission_check(self, request):
        return None #resource is accessible to all
    
    def get_main_link_name(self):
        return 'login'
