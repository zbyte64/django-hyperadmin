from django.views.generic import TemplateView

from hyperadmin.clients.views.common import ClientMixin
from hyperadmin.clients.views.detail import SingleObjectMixin

#TODO features: success_url, initial

class FormMixin(object):
    def get_context_data(self, **kwargs):
        context = super(FormMixin, self).get_context_data(**kwargs)
        context['form'] = self.get_link().form
        return context
    
    def post(self, request, *args, **kwargs):
        response = self.get_api_response()
        if response.status_code != 200:
            return response
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

class CreateView(FormMixin, ClientMixin, TemplateView):
    view_classes = ['add_form']

class UpdateView(FormMixin, SingleObjectMixin, ClientMixin, TemplateView):
    view_classes = ['change_form']

class DeleteView(FormMixin, SingleObjectMixin, ClientMixin, TemplateView):
    view_classes = ['delete_confirmation']

