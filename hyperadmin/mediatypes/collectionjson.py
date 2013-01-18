from django.utils.functional import Promise
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django import http

from hyperadmin.mediatypes.common import MediaType
from hyperadmin.links import Link


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)

class CollectionJSON(MediaType):
    recognized_media_types = [
        'application/vnd.Collection+JSON'
    ]
    
    def prepare_field_value(self, val):
        val = super(CollectionJSON, self).prepare_field_value(val)
        if isinstance(val, Link):
            val = Link.get_absolute_url()
        return val
    
    def convert_field(self, field):
        entry = {"name": force_text(field.name),
                 "prompt": force_text(field.label)}
        return entry
    
    def links_for_item(self, item):
        result = dict()
        links = list()
        links.extend(item.links.get_item_embedded_links())
        links.extend(item.links.get_item_outbound_links())
        result["links"] = [self.convert_link(link) for link in links]
        result["href"] = item.get_absolute_url()
        return result
    
    def convert_item(self, item):
        result = self.links_for_item(item)
        form = item.get_form()
        result['data'] = self.convert_form(form)
        result['prompt'] = item.get_prompt()
        return result
    
    def convert_form(self, form):
        data = list()
        entry_data = self.get_form_instance_values(form)
        for field in form:
            entry = self.convert_field(field)
            #TODO handle link values
            entry['value'] = entry_data.get(field.name, None)
            data.append(entry)
        return data
    
    def convert_link(self, link):
        link_r = {"href":link.get_absolute_url(),
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
    
    def prepare_collection(self, form_link, state):
        data = self.prepare_link(form_link)
        
        items = [self.convert_item(item) for item in state.get_resource_items()]
        
        #the following maps hfactor to this media type
        links = list()
        links.extend(state.links.get_embedded_links())
        links.extend(state.links.get_outbound_links())
        queries = state.links.get_filter_links()
        
        data.update({
            "links": [self.convert_link(link) for link in links],
            "items": items,
            "queries": [self.convert_link(query) for query in queries],
        })
        
        data.update(meta=state.meta, prompt=state.resource.get_prompt())
        return data
    
    def prepare_link(self, form_link):
        data = {
            'href':form_link.get_absolute_url(),
            'version': '1.0',
        }
        if form_link and form_link.form and form_link.form.errors:
            data['error'] = self.convert_errors(form_link.form.errors)
        
        if form_link.form:
            data['template'] = self.convert_link(form_link)
        return data
    
    def serialize(self, content_type, link, state):
        if self.detect_redirect(link):
            return self.handle_redirect(link)
        data = self.prepare_collection(link, state)
        content = json.dumps({"collection":data}, cls=LazyEncoder)
        assert content_type in self.recognized_media_types, "%s not in %s" % (content_type, self.recognized_media_types)
        return http.HttpResponse(content, content_type)
    
    def options_serialize(self, content_type, links, state):
        methods = dict()
        for method, link in links.iteritems():
            methods[method] = {'collection':self.prepare_link(link)}
        content = json.dumps(methods, cls=LazyEncoder)
        allow = ','.join(links.iterkeys())
        response = http.HttpResponse(content, content_type)
        response['Allow'] = allow
        return response
    
    def deserialize(self):
        request = self.get_django_request()
        if hasattr(request, 'body'):
            payload = request.body
        else:
            payload = request.raw_post_data
        data = json.loads(payload)
        data = data['data']
        form_data = dict()
        files = dict()
        for field in data:
            form_data[field['name']] = field['value']
            if field['type'] == 'file' and field['value']:
                #TODO storage lookup could be done better
                storage = self.site.applications['-storages'].resource_adaptor['media'].resource_adaptor
                files[field['name']] = storage.open(field['value'])
        
        return {'data':form_data,
                'files':files,}

CollectionJSON.register_with_builtins()

class CollectionNextJSON(CollectionJSON):
    recognized_media_types = [
        'application/vnd.Collection.next+JSON'
    ]
    
    def convert_field(self, field):
        entry = super(CollectionNextJSON, self).convert_field(field)
        entry['required'] = field.field.required
        entry['type'] = self.get_html_type_from_field(field)
        if hasattr(field.field, 'choices') and field.field.choices is not None:
            options = list()
            for value, prompt in field.field.choices:
                options.append({"value":value,
                                "prompt":prompt})
            entry['list'] = {'options':options}
            from django.forms.widgets import SelectMultiple
            if isinstance(field.field.widget, SelectMultiple):
                entry['multiple'] = True
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

CollectionNextJSON.register_with_builtins()

class CollectionHyperAdminJSON(CollectionNextJSON):
    recognized_media_types = [
        'application/vnd.Collection.hyperadmin+JSON'
    ]
    
    def get_accepted_namespaces(self):
        namespaces = list()
        for entry in self.api_request.META.get('HTTP_ACCEPT_NAMESPACES', '').split(','):
            entry = entry.strip()
            if entry:
                namespaces.append(entry)
        return namespaces
    
    def convert_field(self, field):
        entry = super(CollectionHyperAdminJSON, self).convert_field(field)
        resource = self.get_related_resource_from_field(field)
        if resource:
            if isinstance(resource, basestring):
                entry['related_resource_url'] = resource
            else:
                entry['related_resource_url'] = resource.get_absolute_url()
        entry['classes'] = field.css_classes().split()
        #if isinstance(field, forms.FileField):
        #    field.form.instance
        #TODO upload to
        return entry
    
    def prepare_collection(self, form_link, state, include_namespaces=True):
        data = super(CollectionHyperAdminJSON, self).prepare_collection(form_link, state)
        resource_item = state.item
        
        if resource_item:
            update_links = resource_item.links.get_item_ln_links() + resource_item.links.get_item_idempotent_links()
        else:
            update_links = state.links.get_ln_links() + state.links.get_idempotent_links()
        #get_non_idempotent_updates
        #get_idempotent_updates
        if len(update_links):
            data['templates'] = [self.convert_link(link) for link in update_links]
        
        if include_namespaces and resource_item:
            data['namespaces'] = dict()
            accepted_namespaces = self.get_accepted_namespaces()
            #for key, namespace in state.get_namespaces().iteritems():
            for key, namespace in resource_item.get_namespaces().iteritems():
                for a_key in accepted_namespaces:
                    if key.startswith(a_key):
                        data['namespaces'][key] = self.prepare_collection(form_link=namespace.link, state=namespace.state, include_namespaces=False)
                        data['namespaces'][key]['namespace'] = key
                        break
        
        data['resource_class'] = form_link.resource.resource_class
        if 'display_fields' in state.meta:
            data['display_fields'] = state.meta['display_fields']
        return data

CollectionHyperAdminJSON.register_with_builtins()

