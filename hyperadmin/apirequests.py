import mimeparse


class APIRequest(object):
    def __init__(self, site, path, url_args, url_kwargs):
        self.site = site
        self.path = path
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        #self.payload = payload
        #self.method = method
        #self.user = user
        #self.params = params
        #self.META = meta
        from hyperadmin.states import State
        self.session_state = State()
        self.endpoint_state = State()
        self.endpoint_state['resources'] = dict()
        self.endpoint_state['endpoints'] = dict()
        super(APIRequest, self).__init__()
    
    @property
    def META(self):
        return self.session_state['meta']
    
    def get_response_type(self):
        val = self.META.get('HTTP_ACCEPT', '')
        media_types = self.site.media_types.keys()
        if not media_types:
            return val
        return mimeparse.best_match(media_types, val) or val
    
    def get_request_type(self):
        val = self.META.get('CONTENT_TYPE', self.META.get('HTTP_ACCEPT', ''))
        media_types = self.site.media_types.keys()
        if not media_types:
            return val
        return mimeparse.best_match(media_types, val) or val
    
    def get_request_media_type(self):
        content_type = self.get_request_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized request content type "%s". Choices are: %s' % (content_type, self.site.media_types.keys()))
        return media_type_cls(self)
    
    def get_response_media_type(self):
        content_type = self.get_response_type()
        media_type_cls = self.site.media_types.get(content_type, None)
        if media_type_cls is None:
            raise ValueError('Unrecognized request content type "%s". Choices are: %s' % (content_type, self.site.media_types.keys()))
        return media_type_cls(self)
    
    def get_resource(self, urlname):
        if urlname not in self.endpoint_state['resources']:
            resource = self.site.get_resource_from_urlname(urlname)
            self.endpoint_state['resources'][urlname] = resource.fork(api_request=self)
        return self.endpoint_state['resources'][urlname]
    
    def get_endpoint(self, urlname):
        if urlname not in self.endpoint_state['endpoints']:
            endpoint = self.site.get_endpoint_from_urlname(urlname)
            self.endpoint_state['endpoints'][urlname] = endpoint.fork(api_request=self)
        return self.endpoint_state['endpoints'][urlname]
    
    def get_site(self):
        if 'site' not in self.endpoint_state:
            self.endpoint_state['site'] = self.site.fork(api_request=self)
        return self.endpoint_state['site']
    
    def generate_response(self, link, state):
        media_type = self.get_response_media_type()
        content_type = self.get_request_type()
        return state.generate_response(media_type, content_type, link)

class InternalAPIRequest(APIRequest):
    """
    An Internal API Request
    """
    def __init__(self, site, path='/', url_args=[], url_kwargs={}, **kwargs):
        super(InternalAPIRequest, self).__init__(site, path, url_args, url_kwargs)
        kwargs.setdefault('method', 'GET')
        kwargs.setdefault('params', {})
        kwargs.setdefault('payload', {})
        for key, val in kwargs.iteritems():
            setattr(self, key, val)
    
    def get_full_path(self):
        return self.path

class HTTPAPIRequest(APIRequest):
    """
    Represents an API Request spawned from a Django HTTP Request
    """
    
    get_to_meta_map = {
        '_HTTP_ACCEPT':'HTTP_ACCEPT',
        '_CONTENT_TYPE':'CONTENT_TYPE',
    }
    
    def __init__(self, site, request, url_args, url_kwargs):
        self.request = request
        path = request.path
        super(HTTPAPIRequest, self).__init__(site=site, path=path, url_args=url_args, url_kwargs=url_kwargs)
    
    @property
    def payload(self):
        if not hasattr(self, '_payload'):
            media_type = self.get_request_media_type()
            self._payload = media_type.deserialize(self.request)
        return self._payload
    
    @property
    def method(self):
        return self.request.method
    
    def get_full_path(self):
        return self.request.get_full_path()
    
    @property
    def user(self):
        return self.session_state['auth']
    
    @property
    def params(self):
        if not hasattr(self, '_params'):
            self._params = self.request.GET.copy()
        return self._params
    
    def populate_session_data_from_request(self, request):
        #TODO consult site object
        data = {'endpoints': {},
                'resources': {},
                'request': request,
                'meta': self.patched_meta(request),
                'extra_get_params': self.get_passthrough_params(request),}
        if hasattr(request, 'user'):
            data['auth'] = request.user
        self.session_state.update(data)
        #TODO set response type & request type
        return data
    
    def patched_meta(self, request):
        meta = dict(request.META)
        for src, dst in self.get_to_meta_map.iteritems():
            if src in request.GET:
                meta[dst] = request.GET[src]
        return meta
    
    def get_passthrough_params(self, request):
        pass_through_params = dict()
        for src, dst in self.get_to_meta_map.iteritems():
            if src in request.GET:
                pass_through_params[src] = request.GET[src]
        return pass_through_params

class NamespaceAPIRequest(InternalAPIRequest):
    def __init__(self, api_request, path='/', url_args=[], url_kwargs={}, **kwargs):
        self.original_api_request = api_request
        super(NamespaceAPIRequest, self).__init__(api_request.site, path, url_args, url_kwargs, **kwargs)
        self.session_state.update(api_request.session_state)
    
    def get_full_path(self):
        #TODO
        return self.original_api_request.get_full_path()
    
    @property
    def user(self):
        return self.original_api_request.user

class Namespace(object):
    """
    Represents alternative data associated with the current api request
    
    Namespaced data is provided by another resource through an internal api request
    """
    def __init__(self, name, endpoint, state_data={}):
        self.name = name
        self.api_request = NamespaceAPIRequest(endpoint.api_request)
        self.state_data = state_data
        self.endpoint = endpoint.fork(api_request=self.api_request)
        self.endpoint.state.update(state_data)
        #self.api_request.session_state['endpoints'][self.endpoint.get_url_name()] = self.endpoint
        self.api_request.endpoint_state['resources'][self.endpoint.get_url_name()] = self.endpoint
    
    def get_namespaces(self):
        return dict()
    
    def get_prompt(self):
        return self.endpoint.get_prompt()
    
    @property
    def link(self):
        if not hasattr(self, '_link'):
            self._link = self.endpoint.get_link()
        return self._link
    
    @property
    def state(self):
        return self.endpoint.state
