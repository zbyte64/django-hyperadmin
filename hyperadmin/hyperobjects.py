from copy import copy
from django.utils.http import urlencode


class Link(object):
    def __init__(self, url, resource, method='GET', form=None, form_class=None, form_kwargs=None, link_factor=None,
                 classes=[], descriptors=None, rel=None, prompt=None, cu_headers=None, cr_headers=None, on_submit=None):
        '''
        fields = dictionary of django fields describing the accepted data
        descriptors = dictionary of data describing the link
        
        '''
        self.url = url
        self._method = str(method).upper() #CM
        self.resource = resource
        self._form = form
        self.form_class = form_class
        self.form_kwargs = form_kwargs
        self.link_factor = link_factor
        self.classes = classes
        self.descriptors = descriptors
        self.rel = rel #CL #CONSIDER they may be other cls, this should be a dictionary, classes is also a CL
        self.prompt = prompt
        self.cu_headers = cu_headers
        self.cr_headers = cr_headers
        self.on_submit = on_submit
    
    def get_link_factor(self):
        if self.link_factor:
            return self.link_factor
        if self._method in ('PUT', 'DELETE'):
            return 'LI'
        if self._method == 'POST':
            return 'LN'
        if self._method == 'GET':
            if self.form_class:
                return 'LT'
            #TODO how do we determine which to return?
            return 'LO' #link out to this content
            return 'LE' #embed this content
        return 'L?'
    
    @property
    def is_simple_link(self):
        if self.get_link_factor() in ('LO', 'LE'):
            return True
        return False
    
    @property
    def method(self):
        if self.is_simple_link:
            return 'GET'
        return self._method
    
    def class_attr(self):
        return u' '.join(self.classes)
    
    def get_form_kwargs(self, **form_kwargs):
        if self.form_kwargs:
            kwargs = copy(self.form_kwargs)
        else:
            kwargs = dict()
        kwargs.update(form_kwargs)
        return kwargs
    
    def get_form(self, **form_kwargs):
        kwargs = self.get_form_kwargs(**form_kwargs)
        form = self.form_class(**kwargs)
        return form
    
    @property
    def form(self):
        if self._form is None and self.form_class and not self.is_simple_link:
            self._form = self.get_form()
        return self._form
    
    @property
    def errors(self):
        if self.is_simple_link:
            return None
        if self.form_class:
            return self.form.errors
        return None
    
    def submit(self, **kwargs):
        '''
        Returns a link representing the action
        The resource_item of the link may represent the updated/created object
        or in the case of a collection resource item you get access to the filter items
        '''
        on_submit = self.on_submit
        
        return on_submit(link=self, submit_kwargs=kwargs)
    
    def clone(self, **kwargs):
        a_clone = copy(self)
        a_clone._form = kwargs.pop('form', self._form)
        for key, value in kwargs.iteritems():
            setattr(a_clone, key, value)
        return a_clone

class State(dict):
    def __init__(self, resource, meta, *args, **kwargs):
        self.resource = resource
        self.meta = meta
        super(State, self).__init__(*args, **kwargs)
        
        #nuke previous state links
        self.update({'embedded_links': [],
                     'outbound_links': [],
                     'templated_queries': [],
                     'ln_links': [],
                     'idempotent_links': [],})
    
    def get_embedded_links(self):
        return self.resource.get_embedded_links() + self['embedded_links']
    
    def add_embedded_link(self, link):
        self['embedded_links'].append(link)
    
    def get_outbound_links(self):
        return self.resource.get_outbound_links() + self['outbound_links']
    
    def add_outbound_link(self, link):
        self['outbound_links'].append(link)
    
    def get_templated_queries(self):
        return self.resource.get_templated_queries() + self['templated_queries']
    
    def add_templated_query(self, link):
        self['templated_queries'].append(link)
    
    def get_ln_links(self):
        return self.resource.get_ln_links() + self['ln_links']
    
    def add_ln_link(self, link):
        self['ln_links'].append(link)
    
    def get_idempotent_links(self):
        return self.resource.get_idempotent_links() + self['idempotent_links']
    
    def add_idempotent_link(self, link):
        self['idemptotent_links'].append(link)
    
    def set_item(self, val):
        self['item'] = val
    
    def get_item(self):
        return self.get('item', None)
    
    item = property(get_item, set_item)
    
    @property
    def params(self):
        if 'params' in self:
            return self['params']
        if 'request' in self:
            return self['request'].GET
        return {}
    
    @property
    def namespace(self):
        return self.get('namespace', None)
    
    def get_resource_items(self):
        if self.item is not None:
            return self.item.get_resource_items()
        return self.resource.get_resource_items()
    
    def get_query_string(self, new_params=None, remove=None):
        if new_params is None: new_params = {}
        if remove is None: remove = []
        p = self.params.copy()
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

class Namespace(object):
    def __init__(self, name, link, state):
        self.name = name
        self.link = link
        self.state = state
    
    def get_namespaces(self):
        return dict()

class ResourceItem(object):
    '''
    Represents an instance that is bound to a resource
    '''
    form_class = None
    
    def __init__(self, resource, instance):
        self.resource = resource
        self.instance = instance
    
    def get_embedded_links(self):
        return self.resource.get_item_embedded_links(self)
    
    def get_outbound_links(self):
        return self.resource.get_item_outbound_links(self)
    
    def get_templated_queries(self):
        return self.resource.get_item_templated_queries(self)
    
    def get_ln_links(self):
        return self.resource.get_item_ln_links(self)
    
    def get_idempotent_links(self):
        return self.resource.get_item_idempotent_links(self)
    
    def get_absolute_url(self):
        return self.resource.get_item_url(self)
    
    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class
        return self.resource.get_form_class()
    
    def get_form_kwargs(self, **kwargs):
        kwargs = self.resource.get_form_kwargs(**kwargs)
        kwargs['instance'] = self.instance
        return kwargs
    
    def get_form(self, **form_kwargs):
        '''
        Used for serialization
        '''
        form_cls = self.get_form_class()
        kwargs = self.get_form_kwargs(**form_kwargs)
        form = form_cls(**kwargs)
        return form
    
    @property
    def form(self):
        if not hasattr(self, '_form'):
            self._form = self.get_form()
        return self._form
    
    def get_prompt(self):
        return self.resource.get_item_prompt(self)
    
    def get_resource_items(self):
        return [self]
    
    def get_namespaces(self):
        return self.resource.get_item_namespaces(self)

