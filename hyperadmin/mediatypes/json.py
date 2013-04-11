from __future__ import absolute_import

from django import http

from datatap.datataps import JSONDataTap

from hyperadmin.mediatypes.datatap import DataTap


class JSON(DataTap):
    recognized_media_types = [
        'application/json'
    ]

    def __init__(self, api_request, **kwargs):
        kwargs.setdefault('datatap_class', JSONDataTap)
        super(JSON, self).__init__(api_request, **kwargs)

JSON.register_with_builtins()


class JSONP(JSON):
    recognized_media_types = [
        'text/javascript'
    ]

    def get_jsonp_callback(self):
        #TODO make configurable
        return self.api_request.params['callback']

    def serialize(self, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link, content_type)
        content = self.get_content(link, state)
        callback = self.get_jsonp_callback()
        return http.HttpResponse(u'%s(%s)' % (callback, content), content_type)

JSONP.register_with_builtins()

