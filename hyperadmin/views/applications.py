from django.views import generic

from common import ResourceViewMixin

class ApplicationResourceView(ResourceViewMixin, generic.ListView):
    def get_items(self):
        return self.resource.get_items(self.request)
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)

class SiteResourceView(ApplicationResourceView, generic.TemplateView):
    template_name = 'hyperadmin/index.html'
    
    def get_template_names(self):
        return [self.template_name]
    
    def get(self, request, *args, **kwargs):
        try:
            self.resource.get_media_type(self)
        except ValueError, e:
            return generic.TemplateView.get(self, request, *args, **kwargs)
        return ApplicationResourceView.get(self, request, *args, **kwargs)

