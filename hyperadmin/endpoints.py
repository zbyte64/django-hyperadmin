from django.conf.urls.defaults import url
from django.views.generic import View

from hyperadmin.hyperobjects import Link, LinkCollection, LinkCollectorMixin, ResourceItem
from hyperadmin.states import EndpointState
from hyperadmin.views import EndpointViewMixin


class LinkPrototype(object):
    """
    Incapsulates logic related to a link. This class is responsible for:
    
    * creating link
    * handling link submission
    * controlling link visibility
    """
    def __init__(self, endpoint, name, link_kwargs={}):
        self.endpoint = endpoint
        self.name = name
        self.link_kwargs = link_kwargs
    
    @property
    def resource(self):
        return self.endpoint.resource
    
    @property
    def state(self):
        return self.endpoint.state
    
    @property
    def common_state(self):
        return self.endpoint.common_state
    
    @property
    def api_request(self):
        return self.endpoint.api_request
    
    def show_link(self, **kwargs):
        """
        Checks the state and returns False if the link is not active.
        
        :rtype: boolean
        """
        return True
    
    def get_form_class(self):
        return self.endpoint.get_form_class()
    
    def get_form_kwargs(self, **kwargs):
        """
        :rtype: dict
        """
        return self.endpoint.get_form_kwargs(**kwargs)
    
    def get_link_kwargs(self, **kwargs):
        """
        :rtype: dict
        """
        kwargs.update(self.link_kwargs)
        kwargs['form_kwargs'] = self.get_form_kwargs(**kwargs.get('form_kwargs', {}))
        kwargs.setdefault('endpoint', self.endpoint)
        if kwargs.pop('use_request_url', False):
            kwargs['url'] = self.endpoint.api_request.get_full_path()
        assert self.endpoint.state, 'link creation must come from a dispatched endpoint'
        return kwargs
    
    def get_link(self, **link_kwargs):
        """
        Creates and returns the link
        
        :rtype: Link
        """
        link_kwargs = self.get_link_kwargs(**link_kwargs)
        link = Link(**link_kwargs)
        return link
    
    def handle_submission(self, link, submit_kwargs):
        """
        Called when the link is submitted. Returns a link representing the response.
        
        :rtype: Link
        """
        form = link.get_form(**submit_kwargs)
        if form.is_valid():
            instance = form.save()
            resource_item = self.endpoint.get_resource_item(instance)
            return self.on_success(resource_item)
        return link.clone(form=form)
    
    def on_success(self, item=None):
        """
        Returns a link for a successful submission
        
        :rtype: Link
        """
        if item is not None:
            return item.get_link()
        return self.endpoint.get_resource_link()
    
    def get_url(self, **kwargs):
        return self.endpoint.get_url(**kwargs)
    
    def get_url_name(self):
        return self.endpoint.get_url_name()

class BaseEndpoint(LinkCollectorMixin, View):
    """
    Represents an API Endpoint
    """
    api_request = None
    
    state = None #for this particular endpoint
    #TODO find a better name for "common_state"
    #common_state = None #shared by endpoints of the same resource
    
    global_state = None #for overiding the global state while processing
    
    state_class = EndpointState
    
    endpoint_class = None #descriptor of the endpoint
    endpoint_classes = []
    
    form_class = None
    resource_item_class = ResourceItem
    
    def __init__(self, **kwargs):
        self._init_kwargs = kwargs
        self.links = self.get_link_collector()
        super(BaseEndpoint, self).__init__(**kwargs)
        
        self.post_register()
    
    def post_register(self):
        self.register_link_prototypes()
    
    def get_site(self):
        if self.api_request:
            return self.api_request.get_site()
        return self._site
    
    def set_site(self, site):
        self._site = site
    
    site = property(get_site, set_site)
    
    def get_parent(self):
        if getattr(self, '_parent', None) is None:
            return None
        if self.api_request:
            return self.api_request.get_resource(self._parent.get_url_name())
        return self._parent
    
    def set_parent(self, parent):
        self._parent = parent
    
    parent = property(get_parent, set_parent)
    
    def get_common_state(self):
        return None
    common_state = property(get_common_state)
    
    def get_state(self):
        if not hasattr(self, '_state'):
            assert self.api_request, "Endpoints without an api request are not allowed to have a state"
            self.initialize_state()
        return self._state
    
    def set_state(self, state):
        self._state = state
    
    state = property(get_state, set_state)
    
    def get_meta(self):
        """
        :rtype: dict
        """
        return {}
    
    def get_endpoint_classes(self):
        """
        Returns a list of functional identifiers
        
        :rtype: list of strings
        """
        res_classes = list(self.endpoint_classes)
        res_classes.append(self.endpoint_class)
        return res_classes
    
    def get_state_data(self):
        """
        :rtype: dict
        """
        data = {'endpoint_class':self.endpoint_class,
                'endpoint_classes':self.get_endpoint_classes(),
                'params':self.api_request.params,}
        return data
    
    def get_state_kwargs(self):
        """
        :rtype: dict
        """
        kwargs = {
            'endpoint': self,
            'data':self.get_state_data(),
            'meta':{},
        }
        if self.common_state is not None:
            kwargs['substates'] = [self.common_state]
        return kwargs
    
    def get_state_class(self):
        return self.state_class
    
    def initialize_state(self, **data):
        kwargs = self.get_state_kwargs()
        kwargs['data'].update(data)
        self.state = self.get_state_class()(**kwargs)
        self.state.meta = self.get_meta()
        return self.state
    
    def reverse(self, *args, **kwargs):
        """
        URL Reverse the given arguments
        
        :rtype: string
        """
        return self.state.reverse(*args, **kwargs)
    
    #urls
    
    def get_base_url_name(self):
        raise NotImplementedError
    
    def get_url_name(self):
        raise NotImplementedError
    
    def get_url(self, **kwargs):
        return self.reverse(self.get_url_name(), **kwargs)
    
    def create_link_collection(self):
        """
        Returns an instantiated LinkCollection object
        
        :rtype: LinkCollection
        """
        return LinkCollection(endpoint=self)
    
    #link_prototypes
    def get_link_prototypes(self):
        """
        return a list of tuples containing link prototype class and kwargs
        """
        return []
    
    def register_link_prototypes(self):
        if self.api_request:
            self.link_prototypes = self.api_request.get_link_prototypes(self)
        else:
            self.link_prototypes = self.create_link_prototypes()
    
    def create_link_prototypes(self):
        """
        Instantiates the link prototypes from get_link_prototypes
        
        :rtype: list of link prototypes
        """
        link_prototypes = dict()
        for proto_klass, kwargs in self.get_link_prototypes():
            proto = self.create_link_prototype(proto_klass, **kwargs)
            link_prototypes[proto.name] = proto
        return link_prototypes
    
    def get_link_prototype_kwargs(self, **kwargs):
        """
        :rtype: dict
        """
        params = {'endpoint':self}
        params.update(kwargs)
        return params
    
    def create_link_prototype(self, klass, **kwargs):
        kwargs = self.get_link_prototype_kwargs(**kwargs)
        proto = klass(**kwargs)
        return proto
    
    def fork(self, **kwargs):
        """
        :rtype: endpoint
        """
        params = dict(self._init_kwargs)
        params.update(kwargs)
        return type(self)(**params)
    
    def fork_state(self, **kwargs):
        """
        :rtype: endpoint
        """
        new_endpoint = self.fork()
        new_endpoint.state.update(kwargs)
        return new_endpoint
    
    def get_resource_item_class(self):
        return self.resource_item_class
    
    def get_resource_item(self, instance, **kwargs):
        """
        Wraps an object in a resource item
        
        :rtype: resource item
        """
        kwargs.setdefault('endpoint', self)
        return self.get_resource_item_class()(instance=instance, **kwargs)
    
    def get_instances(self):
        """
        Returns the list of active objects available for this request
        
        :rtype: list of objects
        """
        return []
    
    def get_resource_items(self):
        """
        Returns a list of resource items available for this request. Calls get_instances for the objects the items represent.
        
        :rtype: list of resource items
        """
        instances = self.get_instances()
        return [self.get_resource_item(instance) for instance in instances]
    
    def get_item_url(self, item):
        raise NotImplementedError
    
    def get_form_class(self):
        return self.form_class
    
    def get_form_kwargs(self, item=None, **kwargs):
        """
        :rtype: dict
        """
        if item is not None:
            kwargs.setdefault('instance', item.instance)
        return kwargs
    
    def get_view_kwargs(self):
        """
        :rtype: dict
        """
        return {}
    
    def get_namespaces(self):
        """
        :rtype: dictionary of namespaces
        """
        return {}
    
    def get_item_namespaces(self, item):
        """
        :param item: resource item
        :rtype: dictionary of namespaces
        """
        return {}
    
    #TODO review if this is needed anymore
    def get_item_link(self, item, **kwargs):
        link_kwargs = {'url':item.get_absolute_url(),
                       'endpoint':self,
                       'rel':'item',
                       'prompt':item.get_prompt(),}
        link_kwargs.update(kwargs)
        item_link = Link(**link_kwargs)
        return item_link
    
    #TODO review if this is needed anymore
    def get_main_link_name(self):
        raise NotImplementedError
    
    #TODO review if this is needed anymore
    def get_main_link_prototype(self):
        return self.link_prototypes[self.get_main_link_name()]
    
    def get_link(self, **kwargs):
        link_kwargs = {'rel':'self',
                       'endpoint': self,
                       'prompt':self.get_prompt(),}
        link_kwargs.update(kwargs)
        return self.get_main_link_prototype().get_link(**link_kwargs)
    
    def get_item_prompt(self, item):
        """
        Returns a string representing the resource item
        """
        return unicode(item.instance)
    
    def get_prompt(self):
        """
        Returns a string representing this endpoint
        """
        return unicode(self)
    
    def api_permission_check(self, api_request):
        return self.site.api_permission_check(api_request)
    
    def generate_response(self, link):
        return self.api_request.generate_response(link=link, state=self.state)

class Endpoint(EndpointViewMixin, BaseEndpoint):
    """
    Endpoint class that contains link prototypes and maps HTTP requests to those links.
    """
    name_suffix = None
    url_suffix = None
    
    prototype_method_map = {}
    
    def post_register(self):
        if self.api_request:
            self.api_request.record_endpoint(self)
        super(Endpoint, self).post_register()
    
    def get_link_prototype_for_method(self, method):
        """
        Return the link prototype representing the action for the method
        Consults prototype_method_map for the link name and returns the prototype from link_prototypes
        """
        name = self.prototype_method_map.get(method)
        return self.link_prototypes.get(name)
    
    def get_name_suffix(self):
        return self.name_suffix
    
    def get_url_name(self):
        return self.get_base_url_name() + self.get_name_suffix()
    
    def get_url_suffix(self):
        return self.url_suffix
    
    def get_view(self, **kwargs):
        """
        :rtype: view callable
        """
        kwargs.update(self._init_kwargs)
        kwargs.update(self.get_view_kwargs())
        view = type(self).as_view(**kwargs)
        #allow for retreiving the endpoint from url patterns
        view.endpoint = self
        #thus allowing us to do: myview.endpoint.get_view(**some_new_kwargs)
        return view
    
    def get_url_object(self):
        view = self.get_view()
        return url(self.get_url_suffix(), view, name=self.get_url_name(),)
    
    #TODO review if this is needed anymore
    def get_main_link_name(self):
        return self.get_link_prototypes_for_method('GET').name

