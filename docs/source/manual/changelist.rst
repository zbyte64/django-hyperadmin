==========
Changelist
==========


CONSIDER: this influences the contract on who constructs the state and who filters on that state. With the addition of changelists much of this functionality is absorbed by changelists themselves.
Changelists are state managers. "filter_params" of state should be populated and managed by changelists.

Hyperadmin includes it's own changelist object that operate off hyperobjects instead of the traditional method of using querysets and the request object.
The changelist object takes in a resource and it's state and returns a set of links with their corresponding state changes.


def make_link(self, lookup_params, **kwargs):
    ...

def register_section(self, name, filter_section):
    ...


Filter Section
==============

Changelist allows for groups of filters to be defined. Each grouping is considered exclusive from another. If you group your search filter seperately from your filed filtering then the two will behave independently of each other.
When one filter section is active all others are disabled (hidden). When no active filtering is being used all sections are offered.


class FilterSection
    filters = []
    ordering = None #defaults to resource.get_ordering
    paginator = None #default to resource.get_paginator
    
    def get_instances(self, state, active_index):
        ...
    
    def get_active_index(self, state):
        ...

---------
Filtering
---------

class ListFilter(object):
    title = None  # Human-readable title to appear in the right sidebar.
    
    def __init__(self, filter_section, resource):
        ...

    def get_links(self, state):
        """
        Returns links representing the filterable actions.
        """
        return []

    def get_instances(self, state, active_index):
        """
        Returns the filtered queryset.
        """
        raise NotImplementedError

    def expected_parameters(self):
        """
        Returns the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        raise NotImplementedError

Field Filtering
---------------

Date Hierarchy
--------------

Search
------


--------
Ordering
--------

----------
Pagination
----------
