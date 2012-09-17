from django.views.generic.detail import SingleObjectMixin

from hyperadmin.resources.crud.views import CRUDDetailMixin, CRUDCreateView, CRUDListView, CRUDDeleteView, CRUDDetailView

class ModelMixin(object):
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request.user)
    
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.request.user, self.request.GET)
        return self._changelist

class ModelCreateView(ModelMixin, CRUDCreateView):
    pass

class ModelListView(ModelMixin, CRUDListView):
    def get_state(self):
        state = super(ModelListView, self).get_state()
        state['changelist'] = self.get_changelist()
        return state
    
    def get_paginator(self):
        return self.get_changelist().paginator

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
    def get_changelist_links(self):
        return []
    
    def get_parent(self):
        queryset = self.resource.parent.get_queryset(self.request.user)
        parent = queryset.get(pk=self.kwargs['pk'])
        return parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.get_parent(), self.request.user)

class InlineModelCreateView(InlineModelMixin, ModelCreateView):
    pass

class InlineModelListView(InlineModelMixin, ModelListView):
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.get_parent(), self.request.user, self.request.GET)
        return self._changelist

class InlineModelDetailMixin(object):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])

class InlineModelDeleteView(InlineModelDetailMixin, InlineModelMixin, ModelDeleteView):
    pass

class InlineModelDetailView(InlineModelDetailMixin, InlineModelMixin, ModelDetailView):
    pass

