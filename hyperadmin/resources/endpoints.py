from django.conf.urls.defaults import url

class EndpointLink(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint
    
    @property
    def resource(self):
        return self.endpoint.resource
    
    def show_link(self):
        return True
    
    def get_link(self, **link_kwargs):
        raise NotImplementedError
    
    def handle_submission(self, link, submit_kwargs):
        raise NotImplementedError
    
    def on_success(self):
        return self.resource.get_resource_link()
    
    def get_url(self, **kwargs):
        return self.resource.reverse(self.endpoint.get_url_name(), **kwargs)

class Endpoint(object):
    """
    Represents an API endpoint
    """
    name_suffix = None
    view_class = None
    url_suffix = None
    
    def __init__(self, resource):
        self.resource = resource
    
    def get_view(self):
        init = self.resource.get_view_kwargs()
        return self.view_class.as_view(**init)
    
    def get_url_name(self):
        base_name = self.resource.get_base_url_name()
        return base_name + self.name_suffix
    
    def get_url(self):
        return self.url_suffix
    
    def get_url_object(self):
        return url(self.get_url(), self.get_view(), name=self.get_url_name(),),
    
    #TODO do we define links here?
    def get_links(self):
        """
        return a dictionary of endpoint links
        """
        return {}
    
    #TODO??? endpoints define related links to show; on update show delete link, on list show add link, etc


