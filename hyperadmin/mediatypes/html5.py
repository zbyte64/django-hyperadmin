from django.template.response import TemplateResponse

from hyperadmin.resources import BaseResource

from common import MediaType, BUILTIN_MEDIA_TYPES

class Html5MediaType(MediaType):
    template_name = 'hyperadmin/html5/resource.html'
    response_class = TemplateResponse
    
    def convert_field(self, field, name=None):
        entry = {"name": unicode(name),
                 "value": field.initial,
                 "prompt": unicode(field.label)}
        return entry
    
    def convert_resource(self, resource):
        return {'prompt':unicode(resource)}
    
    def links_for_instance(self, instance):
        result = dict()
        result['embedded_links'] = self.view.get_embedded_links(instance)
        result['outbound_links'] = self.view.get_outbound_links(instance)
        result['href'] = self.view.get_instance_url(instance)
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
        item_r['prompt'] = unicode(form.instance)
        return item_r
    
    def serialize(self, content_type, instance=None, errors=None):
        context = {'instance':instance,
                   'errors':errors}
        
        if hasattr(self.view, 'get_items_forms'):
            items = [self.convert_item_form(form) for form in self.view.get_items_forms()]
        else:
            items = [self.convert_instance(item) for item in self.view.get_items()]
        context['items'] = items
        
        context['embedded_links'] = self.view.get_embedded_links()
        context['outbound_links'] = self.view.get_outbound_links()
        context['templated_queries'] = self.view.get_templated_queries()
        context['non_idempotent_updates'] = self.view.get_ln_links(instance=instance)
        context['idempotent_updates'] = self.view.get_li_links(instance=instance)
        
        response = self.response_class(request=self.request, template=self.template_name, context=context)
        return response
    
    def deserialize(self, form_class, instance=None):
        form = form_class(instance=instance, data=self.request.POST, files=self.request.FILES)
        return form

BUILTIN_MEDIA_TYPES['application/text-html'] = Html5MediaType
BUILTIN_MEDIA_TYPES['application/x-www-form-urlencoded'] = Html5MediaType
BUILTIN_MEDIA_TYPES['multipart/form-data'] = Html5MediaType


