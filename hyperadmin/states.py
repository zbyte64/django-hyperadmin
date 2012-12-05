from copy import copy
import threading

from django.utils.http import urlencode
from django.utils.datastructures import MergeDict
from django.http import QueryDict

from hyperadmin.hyperobjects import LinkCollectionProvider


def assert_ids(merge_dict, ids=None):
    if ids is None:
        ids = set([id(merge_dict)])
    for sdict in merge_dict.dicts:
        did = id(sdict)
        assert did not in ids
        ids.add(did)
        if isinstance(sdict, (MergeDict, GlobalState)):
            assert_ids(sdict, ids)
    return ids

class GlobalState(object):
    def __init__(self):
        self.thread_states = threading.local()
    
    def get_stack(self):
        if not hasattr(self.thread_states, 'stack'):
            self.thread_states.stack = MergeDict()
            self.thread_states.stack.dicts = list(self.thread_states.stack.dicts)
        return self.thread_states.stack
    
    @property
    def dicts(self):
        return self.get_stack().dicts
    
    def __getitem__(self, key):
        stack = self.get_stack()
        assert_ids(stack)
        return stack[key]
    
    def push_stack(self, kwargs):
        stack = self.get_stack()
        stack.dicts.insert(0, kwargs)
        assert_ids(stack)
        return kwargs
    
    def pop_stack(self):
        stack = self.get_stack()
        return stack.dicts.pop(0)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def iteritems(self):
        stack = self.get_stack()
        return stack.iteritems()

    def iterkeys(self):
        for k, v in self.iteritems():
            yield k

    def itervalues(self):
        for k, v in self.iteritems():
            yield v

    def items(self):
        return list(self.iteritems())

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def has_key(self, key):
        stack = self.get_stack()
        return stack.has_key(key)

    __contains__ = has_key
    __iter__ = iterkeys

    def __str__(self):
        stack = self.get_stack()
        return str(stack)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

class GlobalStatePatch(object):
    def __init__(self, global_state, state_params):
        self.global_state = global_state
        self.state_params = state_params
    
    def __enter__(self):
        return self.global_state.push_stack(self.state_params)
    
    def __exit__(self, type, value, traceback):
        self.global_state.pop_stack()

class SessionState(GlobalState):
    @property
    def active_dictionary(self):
        stack = self.get_stack()
        if not len(stack.dicts):
            stack.dicts.append(dict())
        return stack.dicts[0]
    
    def __setitem__(self, key, value):
        self.active_dictionary[key] = value
    
    def __delitem__(self, key):
        del self.active_dictionary[key]
    
    def pop(self, key, default=None):
        return self.active_dictionary.pop(key, default)
    
    def update(self, other_dict):
        self.active_dictionary.update(other_dict)
    
    #context functions
    def patch_state(self, **kwargs):
        return GlobalStatePatch(self, kwargs)
    
    def push_state(self, state):
        return GlobalStatePatch(self, state)

SESSION_STATE = SessionState()
SESSION_STATE.__doc__ = '''
Variables that should be accessible to all resources and endpoints go here.
Typically put in "auth" which is the user object making the requests
'''

def push_session(state):
    return SESSION_STATE.push_state(state)

def patch_session(**kwargs):
    return SESSION_STATE.patch_state(**kwargs)

class State(MergeDict):
    def __init__(self, substates=[], data={}):
        self.active_dictionary = dict()
        self.substates = substates
        self.session = self.get_session()
        self.global_state = GlobalState() #TODO minimize the need for this as much as possible
        dictionaries = self.get_dictionaries()
        super(State, self).__init__(*dictionaries)
        self.update(data)
    
    def get_session(self):
        return SESSION_STATE
    
    def get_dictionaries(self):
        return [self.session, self.global_state, self.active_dictionary] + self.substates
    
    def __copy__(self):
        substates = self.global_state.dicts + [self.active_dictionary] + list(self.substates)
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
    
    #context functions
    def patch_state(self, **kwargs):
        return GlobalStatePatch(self.global_state, kwargs)
    
    def push_state(self, state):
        return GlobalStatePatch(self.global_state, state)
    
    def patch_session(self, **kwargs):
        return self.session.patch_state(**kwargs)
    
    def push_session(self, state):
        return self.session.push_state(state)

class SiteState(State):
    pass

class ResourceBoundMixin(object):
    #contianer = resource or endpoint
    
    @property
    def site(self):
        return self.resource.site
    
    #@property
    #def endpoint(self):
    #    return self.get('endpoint')
    
    def reverse(self, name, *args, **kwargs):
        if 'reverse' in self:
            return self['reverse'](name, *args, **kwargs)
        return self.site.reverse(name, *args, **kwargs)
    
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
        if self.endpoint:
            return self.endpoint.get_resource_items()
        return self.resource.get_resource_items()
    
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
        return self.resource.get_namespaces()

#TODO deprecate ResourceState
class ResourceState(ResourceBoundMixin, State):
    """
    Used by resources to determine what links and items are available in the response.
    """
    def __init__(self, site_state, substates=[], data={}):
        self.site_state = site_state
        super(ResourceState, self).__init__(substates=substates, data=data)
    
    def get_dictionaries(self):
        return [self.session, self.global_state, self.active_dictionary, self.site_state] + self.substates
    
    def __copy__(self):
        substates = self.global_state.dicts + [self.active_dictionary] + list(self.substates)
        ret = self.__class__(self.site_state, substates=substates)
        return ret
    
    @property
    def resource(self):
        return self['resource']
    
    @property
    def container(self):
        return self.resource
    
    @property
    def namespace(self):
        return self.get('namespace', None)
    
    @property
    def links(self):
        return self.resource.links

class EndpointStateLinkCollectionProvider(LinkCollectionProvider):
    def _get_link_functions(self, attr):
        functions = super(EndpointStateLinkCollectionProvider, self)._get_link_functions(attr)
        key_name = attr[len('get_'):]
        functions.append(lambda *args, **kwargs: self.container['links'].get(key_name, []))
        return functions
    
    def add_link(self, key, link):
        self.container['links'].setdefault(key, list())
        self.container['links'][key].append(link)

class EndpointState(ResourceBoundMixin, State):
    """
    Used by resources to determine what links and items are available in the response.
    """
    def __init__(self, resource, endpoint, meta, substates=[], data={}):
        self.resource = resource
        self.endpoint = endpoint
        super(EndpointState, self).__init__(substates=substates, data=data)
        self.meta = meta
        self.links = EndpointStateLinkCollectionProvider(self, self.endpoint.links)
        
        #nuke previous state links
        self.update({'links': {},
                     'extra_get_params':{},})
    
    def __setitem__(self, key, value):
        if key == 'links':
            assert isinstance(value, dict)
        return super(EndpointState, self).__setitem__(key, value)
    
    #@property
    #def resource(self):
    #    return self.resource_state['resource']
    
    @property
    def container(self):
        return self.endpoint
    
    def get_dictionaries(self):
        return [self.session, self.global_state, self.active_dictionary] + self.substates
    
    def __copy__(self):
        substates = self.global_state.dicts + [self.active_dictionary] + list(self.substates)
        ret = self.__class__(self.resource, self.endpoint, copy(self.meta), substates=substates)
        return ret

