from hyperadmin.resources.indexes import Index
from hyperadmin.resources.storages.views import BoundFile

from django.core.paginator import Page


class StoragePaginator(object):
    #count, num_pages, object_list
    def __init__(self, index):
        self.instances = index
        self.count = len(self.instances)
        self.num_pages = 1
        self.object_list = self.instances
    
    @property
    def endpoint(self):
        return self.state.endpoint
    
    def page(self, page_num):
        return Page(self.object_list, page_num, self)

class StorageIndex(Index):
    paginator_class = StoragePaginator
    
    @property
    def storage(self):
        return self.resource.storage
    
    def populate_state(self):
        self.path = self.state.params.get('path', '')
        self.dirs, self.files = self.query(self.path)
        self.instances = [BoundFile(self.storage, file_name) for file_name in self.files]
    
    def get_filtered_index(self):
        return self.instances
    
    def get_filter_links(self, **link_kwargs):
        links = list()
        if self.path:
            kwargs = {
                'url':'./%s' % self.state.get_query_string({}, ['path']),
                'prompt':u"/", 
                'classes':['filter', 'directory'], 
                'rel':"filter", 
                'group':"directory",
            }
            kwargs.update(link_kwargs)
            link = self.get_link(**kwargs)
            links.append(link)
        for directory in self.dirs:
            kwargs = {
                'url':'./%s' % self.state.get_query_string({'path':directory}),
                'prompt':directory,
                'classes':['filter', 'directory'],
                'rel':"filter",
                'group':"directory",
            }
            kwargs.update(link_kwargs)
            link = self.get_link(**kwargs)
            links.append(link)
        if '/' in self.path:
            kwargs = {
                'url':'./%s' % self.state.get_query_string({'path':self.path[:self.path.rfind('/')]}),
                'prompt':u"../",
                'classes':['filter', 'directory'],
                'rel':"filter",
                'group':"directory"
            }
            kwargs.update(link_kwargs)
            link = self.get_link(**kwargs)
            links.append(link)
        return links
