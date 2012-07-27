from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django import http

from resources import BaseResource

BUILTIN_MEDIA_TYPES = dict()

class MediaType(object):
    def __init__(self, view):
        self.view = view
        self.request = view.request
    
    def get_content_type(self):
        return self.view.get_content_type()
    
    def serialize(self, instance=None, errors=None):
        raise NotImplementedError
    
    def deserialize(self, form_class, instance=None):
        raise NotImplementedError

class CollectionJSON(MediaType):
    def construct_template(self, instance=None):
        #TODO view should return LN/LI links
        form_class = self.view.get_form_class(instance=instance)
        if form_class is None:
            return None
        form = form_class(instance=instance)
        result = {'data':self.convert_form(form)}
        return result
    
    def convert_field(self, field, name=None):
        entry = {"name": unicode(name),
                 "value": field.initial,
                 "prompt": unicode(field.label)}
        return entry
    
    def convert_resource(self, resource):
        return {}
    
    def convert_instance(self, instance):
        """
        Given a model instance, generate the code that is expected by the 'items' list objects,
        and the 'template' object for Collection+JSON.
        """
        #instance may be: ApplicationResource or CRUDResource
        if isinstance(instance, BaseResource):
            result = self.convert_resource(instance)
        else:
            result = self.construct_template(instance) or {}
        if instance:
            links = list()
            links.extend(self.view.get_embedded_links(instance))
            links.extend(self.view.get_outbound_links(instance))
            result["links"] = [self.convert_link(link) for link in links]
            result["href"] = self.view.get_instance_url(instance)
        return result
    
    def convert_form(self, form):
        data = list()
        for name, field in form.fields.iteritems():
            entry = self.convert_field(field, name)
            if form.instance:
                entry['value'] = form[name].value()
            data.append(entry)
        return data
    
    def convert_link(self, link):
        link_r = {"href":link.url,
                  "rel":link.rel,
                  }
        if link.descriptors:
            link_r['prompt'] = link.descriptors['label']
        if link.form:
            link_r['data'] = self.convert_form(link.form)
        return link_r
    
    def convert_errors(self, errors):
        error_r = {'title':'An error occurred',
                   'code':'00',
                   'message':str(errors),}
        return error_r
    
    def serialize(self, instance=None, errors=None):
        #CONSIDER a better inferface
        if hasattr(self.view, 'get_items_forms'):
            items = [self.convert_form(form) for form in self.view.get_items_forms()]
        else:
            items = [self.convert_instance(item) for item in self.view.get_items()]
        
        #the following maps hfactor to this media type
        links = list()
        links.extend(self.view.get_embedded_links())
        links.extend(self.view.get_outbound_links())
        queries = self.view.get_templated_queries()
        
        data = {
            "links": [self.convert_link(link) for link in links],
            "items": items,
            "queries": [self.convert_link(query) for query in queries],
            "template": self.construct_template(), #idempotent update
            #"error": {},
        }
        if errors:
            data['error'] = self.convert_errors(errors)
        
        ln_links = self.view.get_ln_links()
        
        #get_non_idempotent_updates
        #get_idempotent_updates
        
        if len(ln_links):
            data['template'] = self.convert_link(ln_links[0])
        
        data.update(href=self.request.build_absolute_uri(), version="1.0")
        content = json.dumps({"collection":data}, cls=DjangoJSONEncoder)
        content_type = self.get_content_type()
        return http.HttpResponse(content, content_type)
    
    def deserialize(self, form_class, instance=None):
        #TODO this needs more thinking
        if hasattr(self.request, 'body'):
            payload = self.request.body
        else:
            payload = self.request.raw_post_data
        data = json.loads(payload)['data']
        form = form_class(instance=instance, data=data, files=self.request.FILES)
        return form

BUILTIN_MEDIA_TYPES['application/vnd.Collection+JSON'] = CollectionJSON

