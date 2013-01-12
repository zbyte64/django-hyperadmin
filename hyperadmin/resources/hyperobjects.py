from hyperadmin.hyperobjects import Item


class ResourceItem(Item):
    @property
    def resource(self):
        return getattr(self.endpoint, 'resource', self.endpoint)

