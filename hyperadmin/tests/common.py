from django.test.client import RequestFactory
from django.core.urlresolvers import RegexURLResolver

from hyperadmin.apirequests import NamespaceAPIRequest
from hyperadmin.endpoints import RootEndpoint


class MockSession(dict):
    def flush(self):
        pass

class SuperUserRequestFactory(RequestFactory):
    def __init__(self, **kwargs):
        self.user = kwargs.pop('user', None)
        super(SuperUserRequestFactory, self).__init__(**kwargs)
    
    def request(self, **request):
        ret = super(SuperUserRequestFactory, self).request(**request)
        ret.user = self.user
        ret.session = MockSession()
        ret.csrf_processing_done = True #lets not worry about csrf
        return ret

class GenericURLResolver(RegexURLResolver):
    def __init__(self, regex, url_patterns, default_kwargs=None, app_name=None, namespace=None):
        # regex is a string representing a regular expression.
        # urlconf_name is a string representing the module containing URLconfs.
        super(GenericURLResolver, self).__init__(regex, urlconf_name=None, default_kwargs=default_kwargs, app_name=app_name, namespace=namespace)
        self._url_patterns = url_patterns
    
    def _get_url_patterns(self):
        return self._url_patterns
    url_patterns = property(_get_url_patterns)
    
    def __repr__(self):
        return '<%s (%s:%s) %s>' % (self.__class__.__name__, self.app_name, self.namespace, self.regex.pattern)

class URLReverseMixin(object):
    def patch_reverse(self, resolver):
        def cls_reverse(slf, name, *args, **kwargs):
            return resolver.reverse(name, *args, **kwargs)
        
        self._orignal_request_reverse = NamespaceAPIRequest.reverse
        self._orignal_root_reverse = RootEndpoint.reverse
        NamespaceAPIRequest.reverse = cls_reverse
        RootEndpoint.reverse = cls_reverse
    
    def unpatch_reverse(self):
        NamespaceAPIRequest.reverse = self._orignal_request_reverse
        RootEndpoint.reverse = self._orignal_root_reverse
