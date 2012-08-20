from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django import http

from hyperadmin.resources import BaseResource

from common import MediaType, BUILTIN_MEDIA_TYPES

class JSON(MediaType):
    def convert_field(self, field, name=None):
        return field.initial
    
    def convert_resource(self, resource):
        return {}
    
    def convert_instance(self, instance):
        #instance may be: ApplicationResource or CRUDResource
        result = dict()
        if isinstance(instance, BaseResource):
            result.update(self.convert_resource(instance))
        return result
    
    def convert_form(self, form):
        data = dict()
        for name, field in form.fields.iteritems():
            entry = self.convert_field(field, name)
            if form.instance:
                entry = form[name].value()
            data[name] = entry
        return data
    
    def convert_item_form(self, form):
        return self.convert_form(form)
    
    def serialize(self, content_type, instance=None, errors=None):
        #CONSIDER a better inferface
        if hasattr(self.view, 'get_items_forms'):
            items = [self.convert_item_form(form) for form in self.view.get_items_forms()]
        else:
            items = [self.convert_instance(item) for item in self.view.get_items()]
        content = json.dumps(items, cls=DjangoJSONEncoder)
        return http.HttpResponse(content, content_type)
    
    def deserialize(self, form_class, instance=None):
        #TODO this needs more thinking
        if hasattr(self.request, 'body'):
            payload = self.request.body
        else:
            payload = self.request.raw_post_data
        data = json.loads(payload)
        kwargs = self.view.get_form_kwargs()
        kwargs.update({'instance':instance,
                       'data':data,
                       'files':self.request.FILES,})
        form = form_class(**kwargs)
        return form

BUILTIN_MEDIA_TYPES['application/json'] = JSON


