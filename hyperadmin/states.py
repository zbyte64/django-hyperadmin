from copy import copy

from django.utils.http import urlencode
from django.utils.datastructures import MergeDict
from django.http import QueryDict

from hyperadmin.links import LinkCollectionProvider, LinkCollectorMixin


class State(MergeDict):
    def __init__(self, substates=[], data={}):
        self.active_dictionary = dict()
        self.substates = substates
        dictionaries = self.get_dictionaries()
        super(State, self).__init__(*dictionaries)
        self.update(data)
    
    def get_dictionaries(self):
        return [self.active_dictionary] + self.substates
    
    def __copy__(self):
        substates = self.get_dictionaries()
        ret = self.__class__(substates=substates)
        return ret
    
    def __setitem__(self, key, value):
        self.active_dictionary[key] = value
    
    def __delitem__(self, key):
        del self.active_dictionary[key]
    
    def pop(self, key, default=None):
        return self.active_dictionary.pop(key, default)
    
    def update(self, other_dict):
        self.active_dictionary.update(other_dict)

class EndpointStateLinkCollectionProvider(LinkCollectionProvider):
    def _get_link_functions(self, attr):
        functions = super(EndpointStateLinkCollectionProvider, self)._get_link_functions(attr)
        key_name = attr[len('get_'):]
        functions.append(lambda *args, **kwargs: self.container['state_links'].get(key_name, []))
        return functions
    
    def add_link(self, key, link):
        self.container['state_links'].setdefault(key, list())
        self.container['state_links'][key].append(link)

class EndpointState(LinkCollectorMixin, State):
    """
    Used by resources to determine what links and items are available in the response.
    """
    link_collector_class = EndpointStateLinkCollectionProvider
    
    def __init__(self, endpoint, meta, substates=[], data={}):
        self.endpoint = endpoint
        super(EndpointState, self).__init__(substates=substates, data=data)
        self.meta = meta
        self.links = self.get_link_collector()
        
        #nuke previous state links
        self.update({'state_links': {},
                     'extra_get_params':{},
                     'endpoint': self.endpoint,})
    
    @property
    def api_request(self):
        return self.endpoint.api_request
    
    def get_link_collector_kwargs(self, **kwargs):
        params = super(EndpointState, self).get_link_collector_kwargs(**kwargs)
        params['parent'] = self.endpoint.links
        return params
    
    def get_dictionaries(self):
        return [self.active_dictionary] + self.substates + [self.endpoint.api_request.session_state]
    
    @property
    def resource(self):
        return getattr(self.endpoint, 'resource', self.endpoint)
    
    @property
    def site(self):
        return self.get('site', self.endpoint.site)
    
    def reverse(self, name, *args, **kwargs):
        return self.api_request.reverse(name, *args, **kwargs)
    
    def _set_item(self, val):
        self['item'] = val
    
    def _get_item(self):
        return self.get('item', None)
    
    item = property(_get_item, _set_item)
    
    def _set_meta(self, val):
        self['meta'] = val
    
    def _get_meta(self):
        return self.get('meta', {})
    
    meta = property(_get_meta, _set_meta)
    
    def get_link_url(self, link):
        url = link.get_base_url()
        params = self.get('extra_get_params', None) or QueryDict('', mutable=True)
        if params:
            params = copy(params)
            if '?' in url:
                url, get_string = url.split('?', 1)
                url_args = QueryDict(get_string)
                if hasattr(params, 'setlist'):
                    for key, value in url_args.iterlists():
                        params.setlist(key, value)
                else:
                    params.update(url_args)
            if hasattr(params, 'urlencode'):
                params = params.urlencode()
            else:
                params = urlencode(params)
            url += '?' + params
        return url
    
    def has_view_class(self, cls):
        view_classes = self.get('view_classes', [])
        return cls in view_classes
    
    @property
    def params(self):
        """
        The filter and pagination parameters
        """
        if 'params' in self:
            return self['params']
        if 'request' in self:
            return self['request'].GET
        return {}
    
    @property
    def namespace(self):
        return self.get('namespace', None)
    
    def get_resource_items(self):
        """
        Returns resource items that are associated with this state.
        """
        if self.item is not None:
            return self.item.get_resource_items()
        return self.endpoint.get_resource_items()
    
    def get_query_string(self, new_params=None, remove=None):
        if new_params is None: new_params = {}
        if remove is None: remove = []
        p = copy(self.params)
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        if hasattr(p, 'urlencode'):
            return '?%s' % p.urlencode()
        return '?%s' % urlencode(p)
    
    def get_namespaces(self):
        return self.endpoint.get_namespaces()
    
    def __copy__(self):
        substates = self.get_dictionaries()
        ret = self.__class__(self.endpoint, copy(self.meta), substates=substates)
        return ret

