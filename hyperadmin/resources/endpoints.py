from django.conf.urls.defaults import url
from django.views.generic import View

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
    
    def get_form_kwargs(self, **kwargs):
        form_kwargs = kwargs.get('form_kwargs', None) or {}
        form_kwargs['item'] = kwargs.get('item', None)
        return self.resource.get_form_kwargs(**form_kwargs)
    
    def get_link_kwargs(self, **kwargs):
        kwargs.update(self.link_kwargs)
        kwargs['form_kwargs'] = self.get_form_kwargs(**kwargs)
        kwargs.setdefault('endpoint', self.endpoint)
        assert self.endpoint.state, 'link creation must come from a dispatched endpoint'
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

class Endpoint(View):
    """
    Represents an API endpoint
    
    Behaves like a class based view
    Initialized originally without a state; should endpoint be a class based view that pumps to another?
    """
    name_suffix = None
    view_class = None
    url_suffix = None
    resource = None
    state = None
    
    def __init__(self, **kwargs):
        self._init_kwargs = kwargs
        super(Endpoint, self).__init__(**kwargs)
        self.links = LinkCollectionProvider(self, self.resource.links)
    
    @property
    def link_prototypes(self):
        if not hasattr(self, '_link_prototypes'):
            self._link_prototypes = dict()
            for endpoint in self.resource.endpoints.itervalues():
                self._link_prototypes.update(endpoint.get_links())
            for link_prototype in self._link_prototypes.itervalues():
                link_prototype.endpoint = self
        return self._link_prototypes
    
    def dispatch(self, request, *args, **kwargs):
        """
        Endpoint simply dispatches to a defined class based view
        """
        #CONSIDER does it make sense to proxy? perhaps we should just merge
        #can we get the view state?
        handler = self.get_view()
        return handler(request, *args, **kwargs)
    
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
        view = type(self).as_view(**self._init_kwargs)
        return url(self.get_url_suffix(), view, name=self.get_url_name(),)
    
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
    
    def get_resource_item(self, instance):
        return self.resource.get_resource_item(instance, endpoint=self)
    
    def get_instances(self):
        return self.resource.get_instances()
    
    def get_resource_items(self):
        instances = self.get_instances()
        return [self.get_resource_item(instance) for instance in instances]
