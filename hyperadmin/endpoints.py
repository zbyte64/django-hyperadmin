from django.conf.urls.defaults import url, patterns
from django.core.urlresolvers import reverse
from django.views.generic import View

from hyperadmin.links import Link, LinkCollection, LinkCollectorMixin
from hyperadmin.apirequests import HTTPAPIRequest
from hyperadmin.hyperobjects import Item
from hyperadmin.states import EndpointState
from hyperadmin.views import EndpointViewMixin

import logging


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
    resource_item_class = Item
    
    def __init__(self, **kwargs):
        self._init_kwargs = kwargs
        self.links = self.get_link_collector()
        super(BaseEndpoint, self).__init__(**kwargs)
        
        self.post_register()
    
    def post_register(self):
        if self.api_request:
            self.api_request.record_endpoint(self)
        else:
            self._site.record_endpoint(self)
        self.register_link_prototypes()
    
    def get_logger(self):
        return self._site.get_logger()
    
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
            return self.api_request.get_endpoint(self._parent.get_url_name())
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
        #TODO send params only if the api request was for this endpoint
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
        return self.api_request.reverse(*args, **kwargs)
    
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
    
    #TODO deprecate this, replace with api_request.api_permission_check()
    def api_permission_check(self, api_request):
        return self.site.api_permission_check(api_request)
    
    def generate_response(self, link):
        return self.api_request.generate_response(link=link, state=self.state)
    
    def generate_options_response(self, links):
        return self.api_request.generate_options_response(links=links, state=self.state)

class RootEndpoint(BaseEndpoint):
    """
    The top endpoint of a hypermedia aware site
    
    Child endpoints bind to this and this endpoint is used to mount in urls.py
    """
    namespace = None
    media_types = None
    apirequest_class = HTTPAPIRequest
    
    def __init__(self, **kwargs):
        kwargs.setdefault('media_types', dict())
        kwargs.setdefault('namespace', str(id(self)))
        self.endpoints_by_urlname = dict()
        super(RootEndpoint, self).__init__(**kwargs)
    
    def get_url_name(self):
        return None
    
    def get_logger(self):
        return logging.getLogger(__name__)
    
    def post_register(self):
        pass #we wrap other endpoints
    
    def get_site(self):
        if self.api_request:
            return self.api_request.get_site()
        return self
    
    site = property(get_site)
    
    def fork(self, **kwargs):
        ret = super(RootEndpoint, self).fork(**kwargs)
        ret.endpoints_by_urlname.update(self.endpoints_by_urlname)
        return ret
    
    def get_urls(self):
        #TODO this goes into standalone endpoint...
        urlpatterns = self.get_extra_urls()
        urlpatterns += patterns('', self.get_url_object())
        return urlpatterns
    
    @property
    def urlpatterns(self):
        return self.get_urls()
    
    def get_extra_urls(self):
        return patterns('',)
    
    def urls(self):
        return self, None, self.namespace
    urls = property(urls)
    
    def reverse(self, name, *args, **kwargs):
        return reverse('%s:%s' % (self.namespace, name), args=args, kwargs=kwargs)
    
    def register_media_type(self, media_type, media_type_handler):
        self.media_types[media_type] = media_type_handler
    
    def get_api_request_kwargs(self, **kwargs):
        params = {'site':self}
        params.update(kwargs)
        return params
    
    def create_apirequest(self, request, url_args, url_kwargs):
        kwargs = self.get_api_request_kwargs(request=request, url_args=url_args, url_kwargs=url_kwargs)
        api_request = self.apirequest_class(**kwargs)
        api_request.populate_session_data_from_request(request)
        if self.global_state is not None:
            api_request.session_state.update(self.global_state)
        return api_request
    
    def record_endpoint(self, endpoint, url_name=None):
        if url_name is None:
            url_name = endpoint.get_url_name()
        if url_name not in self.endpoints_by_urlname:
            self.endpoints_by_urlname[url_name] = endpoint
        else:
            original = self.endpoints_by_urlname[url_name]
            self.get_logger().debug('Double registration at site level on %s by %s, original: %s' % (url_name, endpoint, original))
    
    def get_endpoint_from_urlname(self, urlname):
        return self.endpoints_by_urlname[urlname]
    
    def api_permission_check(self, api_request):
        """
        Return a link describing the authentication failure or return None if the request has sufficient permissions
        """
        return None

class Endpoint(EndpointViewMixin, BaseEndpoint):
    """
    Endpoint class that contains link prototypes and maps HTTP requests to those links.
    """
    name_suffix = None
    url_suffix = None
    
    prototype_method_map = {}
    
    def get_link_prototype_for_method(self, method):
        """
        Return the link prototype representing the action for the method
        Consults prototype_method_map for the link name and returns the prototype from link_prototypes
        """
        name = self.prototype_method_map.get(method)
        return self.link_prototypes.get(name)
    
    def get_available_links(self):
        """
        Returns a dictionary mapping available HTTP methods to a link
        """
        methods = dict()
        for method, link_name in self.prototype_method_map.iteritems():
            proto = self.get_link_prototype_for_method(method)
            if proto and proto.show_link():
                kwargs = {'use_request_url':True}
                kwargs = self.get_link_kwargs(**kwargs)
                link = proto.get_link(**kwargs)
                methods[method] = link
        return methods
    
    def get_name_suffix(self):
        return self.name_suffix
    
    def get_url_name(self):
        return self.get_base_url_name() + self.get_name_suffix()
    
    def get_url_suffix(self):
        return self.url_suffix
    
    def get_view_kwargs(self):
        """
        :rtype: dict
        """
        return {}
    
    def get_view(self, **kwargs):
        """
        :rtype: view callable
        """
        params = self.get_view_kwargs()
        params.update(self._init_kwargs)
        params.update(kwargs)
        view = type(self).as_view(**params)
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

