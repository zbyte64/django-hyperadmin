from django.views.generic.detail import SingleObjectMixin

from hyperadmin.resources.crud.views import CRUDDetailMixin, CRUDCreateView, CRUDListView, CRUDDeleteView, CRUDDetailView

class ModelMixin(object):
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request.user)

class ModelCreateView(ModelMixin, CRUDCreateView):
    pass

class ModelListView(ModelMixin, CRUDListView):
    pass

class ModelDetailMixin(ModelMixin, CRUDDetailMixin, SingleObjectMixin):
    def get_object(self):
        if not hasattr(self, 'object'):
            self.object = SingleObjectMixin.get_object(self)
        return self.object

class ModelDeleteView(ModelDetailMixin, CRUDDeleteView):
    pass

class ModelDetailView(ModelDetailMixin, CRUDDetailView):
    pass

class InlineModelMixin(object):
    def get_state(self):
        state = super(InlineModelMixin, self).get_state()
        state['parent'] = self.get_parent()
        return state
    
    def get_changelist_links(self):
        return []
    
    def get_parent(self):
        if not hasattr(self, '_parent'):
            queryset = self.resource.parent.get_queryset(self.request.user)
            self._parent = queryset.get(pk=self.kwargs['pk'])
        return self._parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent(), self.request.user)

class InlineModelCreateView(InlineModelMixin, ModelCreateView):
    pass

class InlineModelListView(InlineModelMixin, ModelListView):
    pass

class InlineModelDetailMixin(object):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])

class InlineModelDeleteView(InlineModelDetailMixin, InlineModelMixin, ModelDeleteView):
    pass

class InlineModelDetailView(InlineModelDetailMixin, InlineModelMixin, ModelDetailView):
    pass

