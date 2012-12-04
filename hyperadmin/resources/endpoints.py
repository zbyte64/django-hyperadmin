from django.conf.urls.defaults import url

from hyperadmin.hyperobjects import Link, LinkCollectionProvider


class LinkPrototype(object):
    def __init__(self, endpoint, link_kwargs={}):
        self.endpoint = endpoint
        self.link_kwargs = link_kwargs
    
    @property
    def resource(self):
        return self.endpoint.resource
    
    @property
    def state(self):
        return self.endpoint.state
    
    def show_link(self, **kwargs):
        return True
    
    def get_link_kwargs(self, **kwargs):
        kwargs.update(self.link_kwargs)
        return kwargs
    
    def get_link(self, **link_kwargs):
        link_kwargs = self.get_link_kwargs(**link_kwargs)
        link = Link(**link_kwargs)
        return link
    
    def handle_submission(self, link, submit_kwargs):
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.resource.get_resource_item(instance)
            return self.on_success(resource_item)
        return link.clone(form=form)
    
    def on_success(self, item=None):
        if item is not None:
            return item.get_item_link()
        return self.resource.get_resource_link()
    
    def get_url(self, **kwargs):
        return self.endpoint.get_url(**kwargs)

class Endpoint(object):
    """
    Represents an API endpoint
    """
    name_suffix = None
    view_class = None
    url_suffix = None
    
    def __init__(self, resource):
        self.resource_state = resource.state
        #TODO this does not allow for resource overide
        self.links = LinkCollectionProvider(self, resource.links)
    
    @property
    def state(self):
        return self.resource_state.get('endpoint_state', self.resource_state)
    
    @property
    def resource(self):
        return self.state.resource
    
    def get_view_kwargs(self):
        kwargs = self.resource.get_view_kwargs()
        kwargs['endpoint'] = self
        return kwargs
    
    def get_view_class(self):
        return self.view_class
    
    def get_view(self):
        init = self.get_view_kwargs()
        klass = self.get_view_class()
        assert klass
        return klass.as_view(**init)
    
    def get_url_name(self):
        base_name = self.resource.get_base_url_name()
        return base_name + self.name_suffix
    
    def get_url_suffix(self):
        return self.url_suffix
    
    def get_url_object(self):
        return url(self.get_url_suffix(), self.get_view(), name=self.get_url_name(),)
    
    def get_url(self, **kwargs):
        return self.resource.reverse(self.get_url_name(), **kwargs)
    
    #TODO better name => get_internal_links?
    def get_links(self):
        """
        return a dictionary of endpoint links
        """
        return {}
    
    def create_link_collection(self):
        return self.resource.create_link_collection()
    
    #TODO??? endpoints define related links to show; on update show delete link, on list show add link, etc
