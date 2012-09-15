from django.template.response import TemplateResponse
from django.middleware.csrf import CsrfViewMiddleware

from common import MediaType, BUILTIN_MEDIA_TYPES

class Html5MediaType(MediaType):
    template_name = 'hyperadmin/html5/resource.html'
    template_dir_name = 'hyperadmin'
    response_class = TemplateResponse
    
    def convert_field(self, field, name=None):
        entry = {"name": unicode(name),
                 "value": field.initial,
                 "prompt": unicode(field.label)}
        return entry
    
    def links_for_item(self, item):
        result = dict()
        result['embedded_links'] = item.get_embedded_links()
        result['outbound_links'] = item.get_outbound_links()
        result['href'] = item.get_absolute_url()
        return result
    
    def convert_item(self, item):
        result = self.links_for_item(item)
        result['data'] = self.convert_form(item.form)
        result['prompt'] = item.get_prompt()
        return result
    
    def convert_form(self, form):
        data = list()
        for name, field in form.fields.iteritems():
            entry = self.convert_field(field, name)
            if form.instance:
                entry['value'] = form[name].value()
            data.append(entry)
        return data
    
    def get_context_data(self, form_link, meta=None):
        context = {'form_link':form_link,
                   'meta':meta,}
        
        resource_item = form_link.item
        
        items = [self.convert_item(item) for item in resource_item.get_resource_items()]
        context['items'] = items
        
        context['embedded_links'] = form_link.get_embedded_links()
        context['outbound_links'] = form_link.get_outbound_links()
        context['templated_queries'] = form_link.get_templated_queries()
        if resource_item:
            context['non_idempotent_updates'] = resource_item.get_ln_links()
            context['idempotent_updates'] = resource_item.get_idempotent_links()
        else:
            context['non_idempotent_updates'] = form_link.get_ln_links()
            context['idempotent_updates'] = form_link.get_idempotent_links()
        
        if meta and 'display_fields' in meta:
            context['display_fields'] = meta['display_fields']
        
        return context
    
    def get_template_names(self):
        params = {
            'base': self.template_dir_name,
            'view_class': self.view.view_class,
            'resource_name': getattr(self.resource, 'resource_name', None),
            'app_name': self.resource.app_name,
        }
        
        names = [
            '{base}/{app_name}/{resource_name}/{view_class}.html'.format(**params),
            '{base}/{app_name}/{view_class}.html'.format(**params),
            '{base}/{view_class}.html'.format(**params),
            self.template_name,
        ]
        
        return names
    
    def serialize(self, content_type, link, meta=None):
        if self.detect_redirect(link):
            return self.handle_redirect(link)
        context = self.get_context_data(form_link=link, meta=meta)
        response = self.response_class(request=self.request, template=self.get_template_names(), context=context)
        response['Content-Type'] = 'text/html'
        return response
    
    def deserialize(self):
        self.check_csrf()
        
        return {'data':self.request.POST,
                'files':self.request.FILES,}
    
    def check_csrf(self):
        csrf_middleware = CsrfViewMiddleware()
        response = csrf_middleware.process_view(self.view.request, self.deserialize, self.view.args, self.view.kwargs)
        if response is not None:
            assert False, 'csrf failed' #TODO APIException(response) or SuspiciousOperation ....
            raise response

BUILTIN_MEDIA_TYPES['text/html'] = Html5MediaType
BUILTIN_MEDIA_TYPES['application/xhtml+xml'] = Html5MediaType
BUILTIN_MEDIA_TYPES['application/text-html'] = Html5MediaType
BUILTIN_MEDIA_TYPES['application/x-www-form-urlencoded'] = Html5MediaType
BUILTIN_MEDIA_TYPES['multipart/form-data'] = Html5MediaType

