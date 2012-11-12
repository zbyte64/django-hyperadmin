from django.views.generic import TemplateView

from hyperadmin.clients.views.common import ClientMixin

class SingleObjectMixin(object):
    context_object_name = None
    
    def get_resource_item(self):
        return self.get_state().item
    
    def get_object(self):
        return self.get_resource_item().instance
    
    def get_context_object_name(self):
        """
        Get the name to use for the object.
        """
        if self.context_object_name:
            return self.context_object_name
        else:
            return 'object'
    
    def get_context_data(self, **kwargs):
        context = super(SingleObjectMixin, self).get_context_data(**kwargs)
        context_object_name = self.get_context_object_name()
        context[context_object_name] = self.get_object()
        context['resource_item'] = self.get_resource_item()
        return context


class DetailView(SingleObjectMixin, ClientMixin, TemplateView):
    view_classes = ['change_form']
    
    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        return context
