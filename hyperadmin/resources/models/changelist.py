from hyperadmin.resources.crud.changelist import ChangeList, FilterSection
from hyperadmin.resources.models.filters import FieldFilter

class ModelChangeList(ChangeList):
    def __init__(self, resource, list_filter, search_fields, date_hierarchy):
        super(ModelChangeList, self).__init__(resource)
        self.list_filter = list_filter
        self.search_fields = search_fields
        self.date_hierarchy = date_hierarchy
        self.detect_sections()
    
    def detect_sections(self):
        section = self.register_section('main', FilterSection)
        #TODO detect filters
        for param in self.list_filter:
            pass
        if self.search_fields:
            pass
        if self.date_hierarchy:
            pass
    
    def get_paginator_kwargs(self):
        return {'per_page':self.resource.list_per_page,}

