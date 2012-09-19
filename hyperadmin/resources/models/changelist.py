from hyperadmin.resources.crud.changelist import ChangeList, FilterSection
from hyperadmin.resources.models.filters import FieldFilter, SearchFilter

from django.db import models
from django.contrib.admin.util import get_fields_from_path, lookup_needs_distinct


class ModelChangeList(ChangeList):
    def __init__(self, resource, list_filter, search_fields, date_hierarchy):
        super(ModelChangeList, self).__init__(resource)
        self.list_filter = list_filter
        self.search_fields = search_fields
        self.date_hierarchy = date_hierarchy
        self.detect_sections()
    
    @property
    def model(self):
        return self.resource.model
    
    def detect_sections(self):
        filter_section = self.register_section('filter', FilterSection)
        if self.list_filter:
            for list_filter in self.list_filter:
                use_distinct = False
                if callable(list_filter):
                    # This is simply a custom list filter class.
                    spec = list_filter(section=filter_section)
                else:
                    field_path = None
                    if isinstance(list_filter, (tuple, list)):
                        # This is a custom FieldListFilter class for a given field.
                        field, field_list_filter_class = list_filter
                    else:
                        # This is simply a field name, so use the default
                        # FieldListFilter class that has been registered for
                        # the type of the given field.
                        field, field_list_filter_class = list_filter, FieldFilter.create
                    if not isinstance(field, models.Field):
                        field_path = field
                        field = get_fields_from_path(self.model, field_path)[-1]
                    spec = field_list_filter_class(field, field_path=field_path, section=filter_section)
                    # Check if we need to use distinct()
                    use_distinct = (use_distinct or
                                    lookup_needs_distinct(self.resource.opts,
                                                          field_path))
                if spec:
                    filter_section.filters.append(spec)
        
        search_section = self.register_section('search', FilterSection)
        if self.search_fields:
            search_section.register_filter(SearchFilter, search_fields=self.search_fields)
        
        date_section = self.register_section('date', FilterSection)
        if self.date_hierarchy:
            pass
    
    def get_paginator_kwargs(self):
        return {'per_page':self.resource.list_per_page,}
    
    def get_links(self, state):
        links = super(ModelChangeList, self).get_links(state)
        #links += self.getchangelist_sort_links(state)
        return links
    
    def get_changelist_sort_links(self, state):
        links = list()
        changelist = state['changelist']
        from django.contrib.admin.templatetags.admin_list import result_headers
        for header in result_headers(changelist):
            if header.get("sortable", False):
                prompt = unicode(header["text"])
                classes = ["sortby"]
                if "url" in header:
                    links.append(self.get_resource_link(url=header["url"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                else:
                    if header["ascending"]:
                        classes.append("ascending")
                    if header["sorted"]:
                        classes.append("sorted")
                    links.append(self.get_resource_link(url=header["url_primary"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                    links.append(self.get_resource_link(url=header["url_remove"], prompt=prompt, classes=classes+["remove"], rel="sortby"))
                    links.append(self.get_resource_link(url=header["url_toggle"], prompt=prompt, classes=classes+["toggle"], rel="sortby"))
        return links
 
