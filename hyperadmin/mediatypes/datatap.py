# -*- coding: utf-8 -*-
from __future__ import absolute_import

import io

from django import http

from datatap.datataps import StreamDataTap

from hyperadmin.mediatypes.common import MediaType


class DataTap(MediaType):
    def __init__(self, api_request, datatap_class, **kwargs):
        self.datatap_class = datatap_class
        super(DataTap, self).__init__(api_request, **kwargs)

    def get_content(self, form_link, state):
        instream = state.get_resource_items()
        datatap = state.endpoint.get_datatap(instream=instream)
        serialized_dt = self.datatap_class(instream=datatap)
        payload = io.BytesIO()
        serialized_dt.send(payload)
        return payload.getvalue()

    def serialize(self, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link, content_type)
        content = self.get_content(link, state)
        response = http.HttpResponse(content, content_type)
        #TODO response['X-Next-Page'] = state.links(group='pagination', rel='next')[0]
        #TODO response['X-Previous-Page'] = state.links(group='pagination', rel='previous')[0]
        return response

    def get_datatap(self, request):
        if hasattr(request, 'body'):
            payload = request.body
        else:
            payload = request.raw_post_data
        return self.datatap_class(StreamDataTap(io.BytesIO(payload)))

    def deserialize(self, request):
        #CONSIDER: does using a datatap mean you must post as a list?
        datatap = self.get_datatap(request)
        data = list(datatap)[0]
        return {'data': data,
                'files': request.FILES, }
