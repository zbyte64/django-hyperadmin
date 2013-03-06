from copy import copy

from django.http import QueryDict
from django.template.loader import render_to_string


class Link(object):
    """
    A link in the broad hypermedia sense
    """
    def __init__(self, url, endpoint, method='GET', prompt=None, description=None,
                form=None, form_class=None, form_kwargs=None, on_submit=None, errors=None,
                link_factor=None, include_form_params_in_url=False,
                mimetype=None, descriptors=None, template_name='link.html',
                cu_headers=None, cr_headers=None, **cl_headers):
        """
        
        :param url: target url
        :param endpoint: the endpoint that generated this link
        :param method: the HTTP method of the link
        :param prompt: the link display
        :param description: text describing the link, could be help text
        
        :param form: a form instance
        :param form_class: the form class to be used to instantiate the form
        :param form_kwargs: keyword args to be passed into form class for instanting the form
        :param on_submit: a callback that is passed this link and submit_kwargs and returns a link representing the result
        :param mimetype: indicates the mimetype of the link. Useful for creating the proper embedded link tag.
        :param template_name: The name of the template to use for rendering
        """
        self._url = url
        self._method = str(method).upper() #CM
        self.endpoint = endpoint
        self._form = form
        self.form_class = form_class
        self.form_kwargs = form_kwargs
        self.link_factor = link_factor
        self.include_form_params_in_url = include_form_params_in_url
        self.mimetype = mimetype
        self.descriptors = descriptors #is this needed?
        self.cl_headers = cl_headers
        self.prompt = prompt
        self.description = description
        self.template_name = template_name
        self.cu_headers = cu_headers
        self.cr_headers = cr_headers
        self.on_submit = on_submit
        self._errors = errors
    
    @property
    def api_request(self):
        return self.endpoint.api_request
    
    @property
    def resource(self):
        return self.endpoint.resource
    
    @property
    def state(self):
        return self.endpoint.state
    
    @property
    def site(self):
        return self.endpoint.site
    
    @property
    def rel(self):
        return self.cl_headers.get('rel', None)
    
    @property
    def classes(self):
        if not 'classes' in self.cl_headers:
            if 'class' in self.cl_headers:
                self.cl_headers['classes'] = self.cl_headers['class'].split()
            else:
                self.cl_headers['classes'] = []
        return self.cl_headers['classes']
    
    def get_base_url(self):
        #include_form_params_in_url=False
        if self.get_link_factor() == 'LT' and self.include_form_params_in_url: #TODO absorb this in link._url
            if '?' in self._url:
                base_url, url_params = self._url.split('?', 1)
            else:
                base_url, url_params = self._url, ''
            params = QueryDict(url_params, mutable=True)
            form = self.get_form()
            #extract get params
            for field in form:
                val = field.value()
                if val is not None:
                    params[field.html_name] = val
            return '%s?%s' % (base_url, params.urlencode())
        return self._url
    
    def clone_into_links(self):
        assert self.get_link_factor() == 'LT'
        links = list()
        #TODO find a better way
        form = self.get_form()
        options = [(field, key) for key, field in form.fields.iteritems() if hasattr(field, 'choices')]
        for option_field, key in options:
            for val, label in option_field.choices:
                if not val:
                    continue
                form_kwargs = copy(self.form_kwargs)
                form_kwargs['initial'] = {key: val}
                option = self.clone(prompt=label, form_kwargs=form_kwargs, include_form_params_in_url=True)
                links.append(option)
        return links
    
    def get_absolute_url(self):
        """
        The url for this link
        """
        return self.state.get_link_url(self)
    
    def mimetype_is_audio(self):
        return self.mimetype and self.mimetype.startswith('audio')
    
    def mimetype_is_image(self):
        return self.mimetype and self.mimetype.startswith('image')
    
    def mimetype_is_video(self):
        return self.mimetype and self.mimetype.startswith('video')
    
    def get_link_factor(self):
        """
        Returns a two character representation of the link factor.
        
        * LI - Idempotent
        * LN - Non-Idempotent
        * LT - Templated link
        * LO - Outbound link
        * LI - Embedded link
        """
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
        """
        Returns True if this link is simply to be followed
        """
        if self.get_link_factor() in ('LO', 'LE'):
            return True
        return False
    
    @property
    def method(self):
        """
        The HTTP method of the link
        """
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
        """
        Returns the active form for the link. Returns None if there is no form.
        """
        if self._form is None and self.form_class and not self.is_simple_link:
            self._form = self.get_form()
        return self._form
    
    @property
    def errors(self):
        """
        Returns the validation errors belonging to the form
        """
        if self.is_simple_link:
            return self._errors
        if self.form_class:
            #TODO merge with self._errors
            return self.form.errors or self._errors
        return self._errors
    
    def submit(self, **kwargs):
        '''
        Returns a link representing the result of the action taken.
        The resource_item of the link may represent the updated/created object
        or in the case of a collection resource item you get access to the filter items
        '''
        on_submit = self.on_submit
        
        if on_submit is None:
            return self.follow()
        else:
            return on_submit(link=self, submit_kwargs=kwargs)
    
    def follow(self):
        '''
        Follows the link to the endpoint in a subrequest
        Returns a link representing the endpoint response
        '''
        params = {
            'url': self.get_absolute_url(),
        }
        endpoint = self.site.call_endpoint(**params)
        return endpoint.generate_api_response(endpoint.api_request)
    
    def clone(self, **kwargs):
        a_clone = copy(self)
        a_clone._form = kwargs.pop('form', self._form)
        for key, value in kwargs.iteritems():
            setattr(a_clone, key, value)
        return a_clone
    
    def __repr__(self):
        return '<%s LF:%s Prompt:"%s" %s>' % (type(self), self.get_link_factor(), self.prompt, self.get_absolute_url())
    
    def get_context_data(self, **kwargs):
        params = {
            'link': self,
        }
        params.update(kwargs)
        return self.endpoint.get_context_data(**params)
    
    def get_template_names(self):
        if isinstance(self.template_name, basestring):
            template_names = [self.template_name]
        else:
            template_names = self.template_name
        return self.expand_template_names(template_names)
    
    def expand_template_names(self, suffixes):
        return self.endpoint.expand_template_names(suffixes)
    
    def get_context_instance(self):
        #TODO request context?
        return None
    
    def render(self, **kwargs):
        context = self.get_context_data(**kwargs)
        template_name = self.get_template_names()
        return render_to_string(template_name,
                                context,
                                context_instance=self.get_context_instance())

#CONSIDER: should we sublcass: django.core.urlresolvers.NoReverseMatch
class LinkNotAvailable(Exception):
    pass

class LinkCollection(list):
    def __init__(self, endpoint):
        self.endpoint = endpoint
    
    @property
    def link_prototypes(self):
        return self.endpoint.link_prototypes
    
    def add_link(self, link_name, **kwargs):
        """
        Adds the specified link from the resource.
        This will only add the link if it exists and the person is allowed to view it.
        """
        from hyperadmin.endpoints import BaseEndpoint
        if isinstance(link_name, BaseEndpoint):
            try:
                link_name = link_name.get_main_link_name()
            except LinkNotAvailable:
                return False
        if link_name not in self.link_prototypes:
            return False
        endpoint_link = self.link_prototypes[link_name]
        if not endpoint_link.show_link(**kwargs):
            return False
        link = endpoint_link.get_link(**kwargs)
        self.append(link)
        return link

class ChainedLinkCollectionProvider(object):
    def __init__(self, call_chain, default_kwargs={}):
        self.call_chain = call_chain
        self.default_kwargs = default_kwargs
        
    def __call__(self, *args, **kwargs):
        links = None
        kwargs.update(self.default_kwargs)
        for subcall in self.call_chain:
            if links is None:
                links = subcall(*args, **kwargs)
            else:
                links.extend(subcall(*args, **kwargs))
        return links

class LinkCollectionProvider(object):
    def __init__(self, container, parent=None):
        self.container = container #resource, endpoint, state
        self.parent = parent #parent container links
    
    def _get_link_functions(self, attr):
        functions = list()
        if self.parent:
            functions.append( getattr(self.parent, attr) )
        else:
            functions.append( lambda *args, **kwargs: self.container.create_link_collection() )
        if hasattr(self.container, attr):
            functions.append( getattr(self.container, attr) )
        return functions
    
    def _get_link_kwargs(self):
        return {}
    
    def __getattribute__(self, attr):
        if not attr.startswith('get_'):
            return object.__getattribute__(self, attr)
        
        functions = self._get_link_functions(attr)
        default_kwargs = self._get_link_kwargs()
        return ChainedLinkCollectionProvider(functions, default_kwargs)

class ItemLinkCollectionProvider(LinkCollectionProvider):
    def __init__(self, container, parent=None):
        self.container = container
    
    @property
    def parent(self):
        return self.container.endpoint.links
    
    def _get_link_kwargs(self):
        return {'item':self.container}

class LinkCollectorMixin(object):
    link_collector_class = LinkCollectionProvider
    
    def get_link_collector_kwargs(self, **kwargs):
        params = {'container':self}
        params.update(kwargs)
        return params
    
    def get_link_collector(self, **kwargs):
        return self.link_collector_class(**self.get_link_collector_kwargs(**kwargs))

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
    
    def get_link_description(self):
        return self.__doc__
    
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
        assert self.endpoint.state, 'link creation must come from a dispatched endpoint'
        params = dict(self.link_kwargs)
        params.setdefault('description', self.get_link_description())
        params.update(kwargs)
        if params.pop('use_request_url', False):
            params['url'] = self.api_request.get_full_path()
        params['form_kwargs'] = self.get_form_kwargs(**params.get('form_kwargs', {}))
        return self.endpoint.get_link_kwargs(**params)
    
    def get_link_class(self):
        return Link
    
    def get_link(self, **link_kwargs):
        """
        Creates and returns the link
        
        :rtype: Link
        """
        link_kwargs = self.get_link_kwargs(**link_kwargs)
        link_class = self.get_link_class()
        link = link_class(**link_kwargs)
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
