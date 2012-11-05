from hyperadmin.resources.storages.views import BoundFile
from hyperadmin.hyperobjects import Link
from hyperadmin.resources.crud.changelist import ChangeList

class StoragePaginator(object):
    #count, num_pages, object_list
    def __init__(self, index, storage, state):
        self.state = state
        self.path = state.params.get('path', '')
        self.dirs, self.files = index
        self.storage = storage
        
        self.count = len(self.files)
        self.num_pages = 1
        
        self.links, self.instances = self.get_links_and_instances()
        self.object_list = self.instances
    
    def get_links_and_instances(self):
        items = list()
        for file_name in self.files:
            items.append(BoundFile(self.storage, file_name))
        
        links = list()
        if self.path:
            url = './%s' % self.state.get_query_string({}, ['path'])
            link = Link(url=url, resource=self, prompt=u"/", classes=['filter', 'directory'], rel="filter", group="directory")
            links.append(link)
        for directory in self.dirs:
            url = './%s' % self.state.get_query_string({'path':directory})
            link = Link(url=url, resource=self, prompt=directory, classes=['filter', 'directory'], rel="filter", group="directory")
            links.append(link)
        if '/' in self.path:
            url = './%s' % self.state.get_query_string({'path':self.path[:self.path.rfind('/')]})
            link = Link(url=url, resource=self, prompt=u"../", classes=['filter', 'directory'], rel="filter", group="directory")
            links.append(link)
        return links, items

class StorageChangeList(ChangeList):
    def populate_state(self):
        for section in self.sections.itervalues():
            section.populate_state()
        index = self.resource.get_active_index()
        paginator = StoragePaginator(index, storage=self.resource.storage, state=self.state)
        self.state['paginator'] = paginator
        self.state['page'] = paginator
        self.state['links'] = paginator.links

