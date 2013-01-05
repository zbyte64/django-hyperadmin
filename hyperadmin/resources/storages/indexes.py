from hyperadmin.indexes import Index
from hyperadmin.resources.storages.endpoints import BoundFile

from django.core.paginator import Page
from django.core.exceptions import ObjectDoesNotExist


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
    
    def get_url_params(self, param_map={}):
        """
        returns url parts for use in the url regexp for conducting item lookups
        """
        param_map.setdefault('path', 'path')
        return [r'(?P<{path}>.+)'.format(**param_map)]
    
    def get_url_params_from_item(self, item, param_map={}):
        param_map.setdefault('path', 'path')
        return {param_map['path']: item.instance.name}
    
    def populate_state(self):
        self.path = self.state.params.get('path', '')
        query = self.get_index_query().filter(self.path)
        self.dirs, self.instances = query.get_dirs_and_files()
    
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

