from hyperadmin.resources import BaseResource
from hyperadmin.resources.auth.forms import AuthenticationResourceForm
from hyperadmin.resources.auth.endpoints import LoginEndpoint, LogoutEndpoint


class AuthResource(BaseResource):
    form_class = AuthenticationResourceForm
    login_endpoint_class = LoginEndpoint
    logout_endpoint_class = LogoutEndpoint
    
    def __init__(self, **kwargs):
        kwargs.setdefault('app_name', '-authentication')
        kwargs.setdefault('resource_name', 'authentication')
        kwargs.setdefault('resource_adaptor', None)
        super(AuthResource, self).__init__(**kwargs)
    
    def get_view_endpoints(self):
        endpoints = super(AuthResource, self).get_view_endpoints()
        endpoints.extend([
            (self.login_endpoint_class, {}),
            (self.logout_endpoint_class, {}),
        ])
        return endpoints
    
    def api_permission_check(self, api_request, endpoint):
        return None #resource is accessible to all
    
    def get_main_link_name(self):
        return 'login'
    
    def get_index_endpoint(self):
        return self.endpoints['login']
