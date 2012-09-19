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
    pass

class StorageCreateView(StorageMixin, CRUDCreateView):
    pass

class StorageListView(StorageMixin, CRUDListView):
    pass

class StorageDetailMixin(StorageMixin, CRUDDetailMixin):
    def get_object(self):
        if not hasattr(self, 'object'):
            self.object = BoundFile(self.resource.resource_adaptor, self.kwargs['path'])
        return self.object

class StorageDeleteView(StorageDetailMixin, CRUDDeleteView):
    pass

class StorageDetailView(StorageDetailMixin, CRUDDetailView):
    pass

