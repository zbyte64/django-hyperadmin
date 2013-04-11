from hyperadmin.endpoints import Endpoint
from hyperadmin.links import LinkCollection


class ResourceEndpoint(Endpoint):
    @property
    def resource(self):
        return self.parent

    def create_link_collection(self):
        return LinkCollection(endpoint=self.resource)

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
        return self.resource.get_form_kwargs(**kwargs)

    def get_item_form_class(self):
        return self.item_form_class or self.resource.get_item_form_class()

    def get_item_form_kwargs(self, **kwargs):
        return self.resource.get_item_form_kwargs(**kwargs)

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

    def api_permission_check(self, api_request, endpoint):
        return self.resource.api_permission_check(api_request, endpoint)

    def create_apirequest(self, **kwargs):
        return self.resource.create_apirequest(**kwargs)

    def expand_template_names(self, suffixes):
        return self.resource.expand_template_names(suffixes)

    def get_context_data(self, **kwargs):
        return self.resource.get_context_data(**kwargs)

    def get_datatap(self, **kwargs):
        return self.resource.get_datatap(**kwargs)
