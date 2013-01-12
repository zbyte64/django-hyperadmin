from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django import http

from hyperadmin.mediatypes.common import MediaType
from hyperadmin.links import Link


class JSON(MediaType):
    recognized_media_types = [
        'application/json'
    ]
    
    def prepare_field_value(self, val):
        val = super(JSON, self).prepare_field_value(val)
        if isinstance(val, Link):
            val = Link.get_absolute_url()
        return val
    
    def convert_item(self, item):
        return self.get_form_instance_values(item.form)
    
    def get_payload(self, form_link, state):
        items = [self.convert_item(item) for item in state.get_resource_items()]
        return items
    
    def serialize(self, request, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link)
        data = self.get_payload(link, state)
        content = json.dumps(data, cls=DjangoJSONEncoder)
        return http.HttpResponse(content, content_type)
    
    def deserialize(self, request):
        if hasattr(request, 'body'):
            payload = request.body
        else:
            payload = request.raw_post_data
        data = json.loads(payload)
        return {'data':data,
                'files':request.FILES,}

JSON.register_with_builtins()

class JSONP(JSON):
    recognized_media_types = [
        'text/javascript'
    ]
    
    def get_jsonp_callback(self):
        #TODO make configurable
        return self.api_request.params['callback']
    
    def serialize(self, request, content_type, link, state):
        data = self.get_payload(link, state)
        content = json.dumps(data, cls=DjangoJSONEncoder)
        callback = self.get_jsonp_callback()
        return http.HttpResponse(u'%s(%s)' % (callback, content), content_type)

JSONP.register_with_builtins()

