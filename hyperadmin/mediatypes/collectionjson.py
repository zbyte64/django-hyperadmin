from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django import http

from hyperadmin.resources import BaseResource

from common import MediaType, BUILTIN_MEDIA_TYPES

class CollectionJSON(MediaType):
    def convert_field(self, field, name=None):
        entry = {"name": unicode(name),
                 "value": field.initial,
                 "prompt": unicode(field.label)}
        return entry
    
    def convert_resource(self, resource):
        return {}
    
    def links_for_instance(self, instance):
        result = dict()
        links = list()
        links.extend(self.view.get_embedded_links(instance))
        links.extend(self.view.get_outbound_links(instance))
        result["links"] = [self.convert_link(link) for link in links]
        result["href"] = self.view.get_instance_url(instance)
        return result
    
    def convert_instance(self, instance):
        #instance may be: ApplicationResource or CRUDResource
        result = self.links_for_instance(instance)
        if isinstance(instance, BaseResource):
            result.update(self.convert_resource(instance))
        return result
    
    def convert_form(self, form):
        data = list()
        for name, field in form.fields.iteritems():
            entry = self.convert_field(field, name)
            if form.instance:
                entry['value'] = form[name].value()
            data.append(entry)
        return data
    
    def convert_item_form(self, form):
        item_r = self.links_for_instance(form.instance)
        item_r['data'] = self.convert_form(form)
        return item_r
    
    def convert_link(self, link):
        link_r = {"href":link.url,
                  "rel":link.rel,
                  "prompt":link.prompt,
                  "classes":link.classes,
                  }
        if link.descriptors and "label" in link.descriptors:
            link_r['prompt'] = link.descriptors['label']
        if link.form:
            link_r['data'] = self.convert_form(link.form)
        return link_r
    
    def convert_errors(self, errors):
        error_r = {'title':'An error occurred',
                   'code':'00',
                   'message':str(errors),}
        return error_r
    
    def serialize(self, content_type, instance=None, errors=None):
        #CONSIDER a better inferface
        if hasattr(self.view, 'get_items_forms'):
            items = [self.convert_item_form(form) for form in self.view.get_items_forms()]
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
        }
        
        if errors:
            data['error'] = self.convert_errors(errors)
        
        ln_links = self.view.get_ln_links(instance=instance)
        #get_non_idempotent_updates
        #get_idempotent_updates
        if len(ln_links):
            data['template'] = self.convert_link(ln_links[0])
        
        data.update(href=self.request.build_absolute_uri(), version="1.0")
        content = json.dumps({"collection":data}, cls=DjangoJSONEncoder)
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

class CollectionNextJSON(CollectionJSON):
    def convert_field(self, field, name=None):
        entry = super(CollectionNextJSON, self).convert_field(field, name)
        entry['required'] = field.required
        #TODO: entry['type'] = '' #html5 type
        #TODO:
        if hasattr(field, 'options') and field.options:
            options = list()
            for value, prompt in field.options:
                options.append({"value":value,
                                "prompt":prompt})
            entry['list'] = {'options':options}
        '''
        entry['list'] = {
            'multiple':True,
            'options': [{"value":"", "prompt":""}]
        }
        '''
        return entry
    
    def convert_errors(self, errors):
        messages = list()
        for key, error in errors.iteritems():
            message = {'name':key,
                       'message':unicode(error)}
            messages.append(message)
        error_r = {'code':'00',
                   'messages':messages,}
        return error_r
    
    def convert_link(self, link):
        link_r = super(CollectionNextJSON, self).convert_link(link)
        #TODO link_r["method"]
        link_r["method"] = {"options": [{"value":link.method}]}
        #TODO link_r["enctype"]
        return link_r

BUILTIN_MEDIA_TYPES['application/vnd.Collection.next+JSON'] = CollectionNextJSON

