from hyperadmin.resources.crud.views import CRUDDetailMixin, CRUDCreateView, CRUDListView, CRUDDeleteView, CRUDDetailView


class BoundFile(object):
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name
    
    @property
    def pk(self):
        return self.name
    
    @property
    def url(self):
        return self.storage.url(self.name)
    
    def delete(self):
        return self.storage.delete(self.name)

class StorageMixin(object):
    def get_links_and_items(self):
        if not hasattr(self, '_links'):
            self._links, self._items = self.resource.get_links_and_items(self.request)
        return self._links, self._items

class StorageCreateView(StorageMixin, CRUDCreateView):
    pass

class StorageListView(StorageMixin, CRUDListView):
    def get_state(self):
        state = super(StorageListView, self).get_state()
        links, items = self.get_links_and_items()
        state['links'] = links
        state['items'] = items
        return state

class StorageDetailMixin(StorageMixin, CRUDDetailMixin):
    def get_object(self):
        if not hasattr(self, 'object'):
            self.object = BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
        return self.object

class StorageDeleteView(StorageDetailMixin, CRUDDeleteView):
    pass

class StorageDetailView(StorageDetailMixin, CRUDDetailView):
    pass

