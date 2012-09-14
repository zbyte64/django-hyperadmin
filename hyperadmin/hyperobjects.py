from copy import copy

class Link(object):
    def __init__(self, url, resource, method='GET', state=None, item=None, form=None, form_class=None, form_kwargs=None,
                 classes=[], descriptors=None, rel=None, prompt=None, cu_headers=None, cr_headers=None, on_submit=None):
        '''
        fields = dictionary of django fields describing the accepted data
        descriptors = dictionary of data describing the link
        
        '''
        self.url = url
        self.method = str(method).upper() #CM
        self.resource = resource
        self.state = state
        self.item = item
        self._form = form
        self.form_class = form_class
        self.form_kwargs = form_kwargs
        self.classes = classes
        self.descriptors = descriptors
        self.rel = rel #CL
        self.prompt = prompt
        self.cu_headers = cu_headers
        self.cr_headers = cr_headers
        self.on_submit = on_submit
    
    def get_link_factor(self):
        if self.method in ('PUT', 'DELETE'):
            return 'LI'
        if self.method == 'POST':
            return 'LN'
        if self.method == 'GET':
            if self.form_class:
                return 'LT'
            #TODO how do we determine which to return?
            return 'LO'
            return 'LE'
        return 'L?'
    
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
        if self._form is None and self.form_class:
            self._form = self.get_form()
        return self._form
    
    @property
    def errors(self):
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
    
    def get_embedded_links(self):
        if self.state:
            return self.state.get_embedded_links()
        return self.resource.get_embedded_links(self.state)
    
    def get_outbound_links(self):
        if self.state:
            return self.state.get_outbound_links()
        return self.resource.get_outbound_links(self.state)
    
    def get_templated_queries(self):
        if self.state:
            return self.state.get_templated_queries()
        return self.resource.get_templated_queries(self.state)
    
    def get_ln_links(self):
        if self.state:
            return self.state.get_ln_links()
        return self.resource.get_ln_links(self.state)
    
    def get_idempotent_links(self):
        if self.state:
            return self.state.get_idempotant_links()
        return self.resource.get_idempotant_links(self.state)
    
    def get_resource_items(self):
        if self.item is not None:
            return self.item.get_resource_items()
        return []

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
        return self.resource.get_item_idempotant_links(self)
    
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
    
    def get_prompt(self):
        return self.resource.get_item_prompt(self)
    
    def get_resource_items(self):
        return [self]

class CollectionResourceItem(ResourceItem):
    def __init__(self, resource, instance, filter_params=None):
        super(CollectionResourceItem, self).__init__(resource, instance)
        self.filter_params = filter_params #oject constructed by the resource that instructs how to filter
    
    def get_resource_items(self):
        #TODO this seems to require some state
        return self.resource.get_resource_items(user=None, filter_params=self.filter_params)

