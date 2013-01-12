from hyperadmin.endpoints import Endpoint
from hyperadmin.links import LinkCollection


class ResourceEndpoint(Endpoint):
    @property
    def resource(self):
        return self.parent
    
    def create_link_collection(self):
        return LinkCollection(endpoint=self.resource)
    
    def get_view_kwargs(self):
        return self.resource.get_view_kwargs()
    
    def get_base_url_name(self):
        return self._parent.get_base_url_name()
    
    def get_resource_item(self, instance, **kwargs):
        kwargs.setdefault('endpoint', self)
        return self.resource.get_resource_item(instance, **kwargs)
    
    def get_instances(self):
        return self.resource.get_instances()
    
    def get_common_state(self):
        return self.resource.state
    common_state = property(get_common_state)
    
    def get_resource_link(self, **kwargs):
        return self.resource.get_link(**kwargs)
    
    def get_item_url(self, item):
        return self.resource.get_item_url(item)
    
    def get_item_prompt(self, item):
        return self.resource.get_item_prompt(item)
    
    def get_form_class(self):
        return self.form_class or self.resource.get_form_class()
    
    def get_form_kwargs(self, **kwargs):
        if self.common_state.item:
            kwargs['item'] = self.common_state.item
        return self.resource.get_form_kwargs(**kwargs)
    
    def get_link_kwargs(self, **kwargs):
        form_kwargs = kwargs.get('form_kwargs', None) or {}
        form_kwargs = self.get_form_kwargs(**form_kwargs)
        kwargs['form_kwargs'] = form_kwargs
        if self.common_state.item:
            kwargs['item'] = self.common_state.item
        return kwargs
    
    def get_namespaces(self):
        return self.resource.get_namespaces()
    
    def get_item_namespaces(self, item):
        return self.resource.get_item_namespaces(item=item)
    
    def get_item_link(self, item):
        return self.resource.get_item_link(item=item)
    
    def get_breadcrumbs(self):
        breadcrumbs = self.resource.get_breadcrumbs()
        breadcrumbs.endpoint = self
        return breadcrumbs
    
    def api_permission_check(self, api_request):
        return self.resource.api_permission_check(api_request)

