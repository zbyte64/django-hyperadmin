from django.conf.urls.defaults import url, patterns, include
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.utils.datastructures import MultiValueDict

from hyperadmin.links import Link, LinkCollection, LinkCollectorMixin, LinkNotAvailable
from hyperadmin.app_settings import DEFAULT_API_REQUEST_CLASS
from hyperadmin.apirequests import InternalAPIRequest
from hyperadmin.hyperobjects import Item
from hyperadmin.states import EndpointState
from hyperadmin.views import EndpointViewMixin
from hyperadmin.signals import endpoint_event

import logging
import urlparse


class BaseEndpoint(LinkCollectorMixin, View):
    """
    Represents an API Endpoint
    """

    form_class = None
    '''The default form class for links created by this endpoint'''

    item_form_class = None
    '''The form class representing items from this endpoint.
    The form created is used for serialization of item.'''

    state_class = EndpointState

    resource_item_class = Item

    app_name = None
    '''The slug that identifies the application of this endpoint. Typically set by the site object.'''

    base_url_name_suffix = None
    '''The suffix to apply to the base url name when concating the base
    name from the parent'''

    base_url_name = None
    '''Set the base url name instead of getting it from the parent'''

    name_suffix = None
    '''The suffix to add to the generated url name. This also used by
    the parent endpoint to reference child endpoints'''

    url_name = None
    '''Set the url name of the endpoint instead of generating one'''

    global_state = None
    '''Dictionary for overiding particular values in the state'''

    endpoint_class = None
    '''A slug identifying the primary role of the endpoint'''

    endpoint_classes = []
    '''A list of slugs identifying the various roles or functions of the endpoint'''

    #generated items:
    api_request = None
    '''The api request responsible for the endpoint. Generated automatically.'''

    state = None
    '''The state responsible for the endpoint. Generated automatically.'''

    def __init__(self, **kwargs):
        self._init_kwargs = dict(kwargs)
        self.links = self.get_link_collector()
        super(BaseEndpoint, self).__init__(**kwargs)

        self._registered = False
        self.post_register()
        self._registered = True

    def post_register(self):
        assert not self._registered
        if self.api_request:
            self.api_request.record_endpoint(self)
        else:
            self._site.record_endpoint(self)
        self.register_link_prototypes()

    def get_logger(self):
        return self._site.get_logger()

    def get_site(self):
        if self._registered and self.api_request:
            return self.api_request.get_site()
        return self._site

    def set_site(self, site):
        self._site = site

    site = property(get_site, set_site)

    def get_parent(self):
        if getattr(self, '_parent', None) is None:
            return None
        if self._registered and self.api_request:
            return self.api_request.get_endpoint(self._parent.get_url_name())
        return self._parent

    def set_parent(self, parent):
        assert parent != self
        self._parent = parent

    parent = property(get_parent, set_parent)

    def get_endpoint_kwargs(self, **kwargs):
        '''
        Consult for creating child endpoints
        '''
        kwargs.setdefault('parent', self)
        kwargs.setdefault('site', self.site)
        kwargs.setdefault('api_request', self.api_request)
        #if self.parent:
        #    kwargs = self.parent.get_endpoint_kwargs(**kwargs)
        return kwargs

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

    def get_base_url_name_suffix(self):
        assert self.base_url_name_suffix is not None, '%s has not set base_url_name_suffix' % self
        return self.base_url_name_suffix

    def get_base_url_name_prefix(self):
        if self.parent:
            return self.parent.get_base_url_name()
        return ''

    def get_base_url_name(self):
        '''
        Returns the base url name to be used by our name and the name of
        our children endpoints
        Return self.base_url_name if set otherwise return the concat of
        self.get_base_url_name_prefix() and self.get_base_url_name_suffix()
        '''
        if self.base_url_name is not None:
            base = self.base_url_name
        else:
            base = self.get_base_url_name_prefix() + self.get_base_url_name_suffix()
        if base and not base.endswith('_'):
            base += '_'
        return base

    def get_name_suffix(self):
        return self.name_suffix

    def get_url_name(self):
        '''
        Returns the url name that will address this endpoint
        Return self.url_name is set otherwise return the result of
        concatting self.get_base_url_name() and self.get_name_suffx()
        '''
        if self.url_name is not None:
            return self.url_name
        assert self.get_base_url_name() != '_'
        return self.get_base_url_name() + self.get_name_suffix()

    def get_url(self, **kwargs):
        return self.reverse(self.get_url_name(), **kwargs)

    def get_url_suffix(self):
        return ''

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
        #if 'datatap' not in kwargs:
        #    kwargs['datatap'] = self.get_datatap()
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

    def get_form_class(self):
        return self.form_class

    def get_form_kwargs(self, **kwargs):
        return kwargs

    def get_item_form_class(self):
        return self.item_form_class or self.get_form_class()

    def get_item_form_kwargs(self, item=None, **kwargs):
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

    def get_item_url(self, item):
        raise NotImplementedError

    def get_item_link(self, item, **kwargs):
        link_kwargs = {'url':item.get_absolute_url(),
                       'endpoint':self,
                       'rel':'item',
                       'prompt':item.get_prompt(),}
        link_kwargs.update(kwargs)
        item_link = Link(**link_kwargs)
        return item_link

    def get_main_link_name(self):
        raise NotImplementedError

    def get_main_link_prototype(self):
        link_name = self.get_main_link_name()
        if link_name in self.link_prototypes:
            return self.link_prototypes[link_name]
        raise LinkNotAvailable, 'Link unavailable: %s' % link_name

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

    def api_permission_check(self, api_request, endpoint):
        return self.site.api_permission_check(api_request, endpoint)

    def generate_response(self, link):
        return self.api_request.generate_response(link=link, state=self.state)

    def generate_options_response(self, links):
        return self.api_request.generate_options_response(links=links, state=self.state)

    def create_internal_apirequest(self, **kwargs):
        return self.site.create_internal_apirequest(**kwargs)

    def create_apirequest(self, **kwargs):
        return self.site.create_apirequest(**kwargs)

    def expand_template_names(self, suffixes):
        return self.site.expand_template_names(suffixes)

    def get_context_data(self, **kwargs):
        return self.site.get_context_data(**kwargs)

    def generate_api_response(self, api_request):
        """
        :rtype: Link or HttpResponse
        """
        raise NotImplementedError

    def emit_event(self, event, item_list=None):
        """
        Fires of the `endpoint_event` signal
        """
        sender = '%s!%s' % (self.get_url_name(), event)
        if item_list is None:
            item_list = self.get_resource_items()
        return endpoint_event.send(sender=sender, endpoint=self, event=event, item_list=item_list)

    def get_datatap(self, instream=None, **kwargs):
        '''
        Returns a datatap that can serialize hypermedia items and deserialize to native instances

        :param instream: A list of resource items or a primitive datatap
        '''
        if instream is None:
            #open for read; give primitives
            return self.get_native_datatap(**kwargs)
        elif isinstance(instream, (list, tuple)):
            #list of resource items; give primitives
            native_instream = self.get_native_datatap_instream_from_items(instream)
            return self.get_native_datatap(instream=native_instream, **kwargs)
        else:
            #read primitives from instream, return deserialized objects
            return self.get_native_datatap(instream=instream, **kwargs)

    def get_native_datatap_instream_from_items(self, items):
        '''
        Makes an instream of item forms
        '''
        return [item.form for item in items]

    def get_native_datatap(self, instream=None, **kwargs):
        '''
        Returns a datatap that can serialize the forms belonging to hypermedia items.
        '''
        from hyperadmin.datataps import HypermediaFormDataTap
        #if there is no instream, read from the global resource items
        if instream is None:
            instream = self.get_resource_items()
        return HypermediaFormDataTap(instream, **kwargs)

class VirtualEndpoint(BaseEndpoint):
    '''
    A type of endpoint that does not define any active endpoints itself
    but references other endpoints.
    '''
    name_suffix = 'virtual'

    def get_children_endpoints(self):
        return []

    def get_urls(self):
        urlpatterns = self.get_extra_urls()
        urls = [endpoint.get_url_object() for endpoint in self.get_children_endpoints()]
        urlpatterns += patterns('', *urls)
        return urlpatterns

    def get_extra_urls(self):
        return patterns('',)

    def urls(self):
        return self.get_urls(), self.app_name, None
    urls = property(urls)

    def dynamic_urls(self):
        return self, self.app_name, None

    @property
    def urlpatterns(self):
        return self.get_urls()

    def get_url_object(self):
        return url(self.get_url_suffix(), include(self.urls))

    def create_link_prototypes(self):
        '''
        Inludes the link prototypes created by the children endpoints
        '''
        link_prototypes = super(VirtualEndpoint, self).create_link_prototypes()

        for endpoint in self.get_children_endpoints():
            link_prototypes.update(endpoint.link_prototypes)

        return link_prototypes

    def get_index_endpoint(self):
        raise NotImplementedError

    def get_main_link_name(self):
        return self.get_index_endpoint().get_main_link_name()

    def get_url(self, **kwargs):
        return self.get_index_endpoint().get_url(**kwargs)

    def generate_api_response(self, api_request):
        """
        Calls the index endpoint and returns it's api response
        :rtype: Link or HttpResponse
        """
        endpoint = self.get_index_endpoint().fork(api_request=api_request)
        return endpoint.generate_api_response(api_request)

class GlobalSiteMixin(object):
    '''
    Endpoints inheriting this class will default to the global site if
    no site is passed in.
    '''
    global_endpoint = False

    def __init__(self, **kwargs):
        if 'site' not in kwargs:
            from hyperadmin.sites import global_site
            kwargs.setdefault('site', global_site)
            self.global_endpoint = True
        super(GlobalSiteMixin, self).__init__(**kwargs)

    def urls(self):
        if self.global_endpoint:
            return self.get_urls(), self.app_name, self.site.namespace
        return self.get_urls(), self.app_name, None
    urls = property(urls)

class APIRequestBuilder(object):
    apirequest_class = DEFAULT_API_REQUEST_CLASS
    '''The api request class to use for incomming django requests'''

    internal_apirequest_class = InternalAPIRequest
    '''The api request class to use for internal api calls'''

    def get_api_request_kwargs(self, **kwargs):
        params = {
            'site': self.site,
            'global_state': self.global_state, }
        params.update(kwargs)
        return params

    def create_apirequest(self, request, url_args, url_kwargs):
        kwargs = self.get_api_request_kwargs(request=request, url_args=url_args, url_kwargs=url_kwargs)
        return self.apirequest_class(**kwargs)

    def get_internal_api_user(self):
        '''
        Returns an authenticated anonymous user with superuser powers
        '''
        from django.contrib.auth.models import AnonymousUser
        class SuperAnonymousUser(AnonymousUser):
            is_staff = True
            is_superuser = True

            def has_perm(self, perm, obj=None):
                return True

            def is_authenticated(self):
                return True

        return SuperAnonymousUser()

    def create_internal_apirequest(self, **kwargs):
        #kwargs.setdefault('request', MockedRequest)
        kwargs.setdefault('user', self.get_internal_api_user())
        kwargs = self.get_api_request_kwargs(**kwargs)
        api_request = self.internal_apirequest_class(**kwargs)
        if self.global_state is not None:
            api_request.session_state.update(self.global_state)
        return api_request

class RootEndpoint(APIRequestBuilder, VirtualEndpoint):
    """
    The top endpoint of a hypermedia aware site

    Child endpoints bind to this and this endpoint is used to mount in urls.py
    """
    namespace = None
    '''The namespace of this endpoint, will be autogenerated if none is supplied'''

    media_types = None
    '''Dictionary of supported media types'''

    template_paths = None
    '''List of template paths to use for template name resolution'''

    base_url_name = ''
    name_suffix = 'virtualroot'

    def __init__(self, **kwargs):
        kwargs.setdefault('media_types', dict())
        kwargs.setdefault('namespace', str(id(self)))
        self.endpoints_by_urlname = dict()
        super(RootEndpoint, self).__init__(**kwargs)

    @property
    def link_prototypes(self):
        return self.get_index_endpoint().link_prototypes

    @property
    def parent(self):
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

    def urls(self):
        return self, None, self.namespace
    urls = property(urls)

    def reverse(self, name, *args, **kwargs):
        return reverse('%s:%s' % (self.namespace, name), args=args, kwargs=kwargs)

    def get_resolver(self):
        from django.core.urlresolvers import RegexURLResolver
        #get our root url
        starter = self.get_link().get_absolute_url()
        return RegexURLResolver(r'^%s' % starter, self.urlpatterns)

    def call_endpoint(self, url, **request_params):
        '''
        Looks up the endpoint as an internal api request
        :rtype: Bound Endpoint
        '''
        url_parts = urlparse.urlparse(url)
        path = url_parts.path
        from django.core.urlresolvers import Resolver404
        from hyperadmin.apirequests import NamespaceAPIRequest
        try:
            match = self.get_resolver().resolve(path)
        except Resolver404 as notfound:
            self.get_logger().exception('Could not resolve %s' % url)
            assert False, str(notfound)
        params = {
            'api_request': self.api_request,
            'path': path,
            'full_path': url,
            'url_kwargs': match.kwargs,
            'url_args': match.args,
            'params': MultiValueDict(urlparse.parse_qs(url_parts.query)),
        }
        params.update(request_params)
        api_request = NamespaceAPIRequest(**params)

        return match.func.endpoint.fork(api_request=api_request)

    def register_media_type(self, media_type, media_type_handler):
        self.media_types[media_type] = media_type_handler

    def record_endpoint(self, endpoint, url_name=None):
        if url_name is None:
            url_name = endpoint.get_url_name()
        if url_name not in self.endpoints_by_urlname:
            self.endpoints_by_urlname[url_name] = endpoint
        else:
            original = self.endpoints_by_urlname[url_name]
            #self.get_logger().debug('Double registration at site level on %s by %s, original: %s' % (url_name, endpoint, original))

    def get_endpoint_from_urlname(self, urlname):
        return self.endpoints_by_urlname[urlname]

    def api_permission_check(self, api_request, endpoint):
        """
        Return a link describing the authentication failure or return None if the request has sufficient permissions
        """
        return None

    def get_template_paths(self):
        if self.template_paths:
            return self.template_paths
        return [self.namespace]

    def expand_template_names(self, suffixes):
        '''
        Maps a list of template names to the template paths belonging to
        the site
        :param suffixes: List of strings
        :rtype: List of strings
        '''
        template_names = list()
        for path in self.get_template_paths():
            for template_name in suffixes:
                template_names.append('/'.join([path, template_name]))
        template_names.extend(suffixes)
        return template_names

    def get_context_data(self, **kwargs):
        return kwargs

class Endpoint(GlobalSiteMixin, EndpointViewMixin, BaseEndpoint):
    """
    Endpoint class that contains link prototypes and maps HTTP requests to those links.
    """
    url_suffix = None
    base_url_name_suffix = ''

    prototype_method_map = {}

    def get_available_methods(self):
        return self.prototype_method_map.keys()

    def get_link_prototype_for_method(self, method):
        """
        Return the link prototype representing the action for the method
        Consults prototype_method_map for the link name and returns the prototype from link_prototypes
        """
        name = self.prototype_method_map.get(method)
        return self.link_prototypes.get(name)

    def get_link_kwargs(self, **kwargs):
        kwargs.setdefault('endpoint', self)
        if 'item' not in kwargs and self.state.item:
            kwargs['item'] = self.state.item
        return kwargs

    def get_available_links(self):
        """
        Returns a dictionary mapping available HTTP methods to a link
        """
        methods = dict()
        for method in self.get_available_methods():
            proto = self.get_link_prototype_for_method(method)
            if proto and proto.show_link():
                kwargs = {'use_request_url':True}
                kwargs = self.get_link_kwargs(**kwargs)
                link = proto.get_link(**kwargs)
                methods[method] = link
        return methods

    def get_url_suffix(self):
        return self.url_suffix

    def get_view_kwargs(self, **kwargs):
        """
        :rtype: dict
        """
        params = dict(self._init_kwargs)
        params.update(kwargs)
        return params

    def get_view(self, **kwargs):
        """
        :rtype: view callable
        """
        #TODO should this be get_endpoint_kwargs?
        params = self.get_view_kwargs(**kwargs)
        view = type(self).as_view(**params)
        #allow for retreiving the endpoint from url patterns
        view.endpoint = self
        #thus allowing us to do: myview.endpoint.get_view(**some_new_kwargs)
        return view

    def get_url_object(self):
        view = self.get_view()
        return url(self.get_url_suffix(), view, name=self.get_url_name(),)

    def get_main_link_name(self):
        return self.get_link_prototype_for_method('GET').name

