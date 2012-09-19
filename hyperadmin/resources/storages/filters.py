from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

from hyperadmin.resources.crud.filters import BaseChoicesFilter

class PathFilter(BaseChoicesFilter):
    def __init__(self, section):
        self.title = _('Path')
        super(PathFilter, self).__init__(section)
    
    def expected_parameters(self):
        return ['path']

    def is_active(self, state):
        return 'path' in state.get('filter_params', {})
    
    def filter_index(self, state, active_index):
        path = state['filter_params']['path']
        return active_index


