"""
Helper function for logging all events that come through the API.
"""
# TODO Write logging model

from contextlib import contextmanager
import logging

from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

class RelList(list):
    """
    A list subclass that allows us to use dot notation to search for elements
    that match the reltype.
    
    >>> links = RelList([{"rel":"self", "href": "self"}, {"rel":"other", "href":"other"}])
    >>> links.self["href"]
    'self'
    >>> links.other["href"]
    'other'
    >>> links.foo
    
    """
    def __getattr__(self, name):
        for item in self:
            if item['rel'] == name:
                return item

LOGGER = logging.getLogger('hypermedia')

UNSPECIFIED = 0
ADDITION = 1
CHANGE = 2
DELETION = 3

ACTION_NAME = {
    UNSPECIFIED: "???",
    ADDITION: "added",
    CHANGE: "changed",
    DELETION: "deleted"
}

@contextmanager
def log_action(user, obj, action_flag, change_message="", request=None):
    """
    A context manager that logs the action.
    
    If the action fails, it logs that, too.
    """
    if user.is_anonymous:
        user = None
    
    action = ACTION_NAME[action_flag]
    object_repr = smart_unicode(obj)
    
    if not change_message:
        change_message = _(u"Object %s was %s." % (
            object_repr, action
        ))
    
    # Allow the body of the context to run
    try:
        yield
    except:
        LOGGER.error(_(u"Unable to %s object %s." % (action, object_repr)),
            exc_info=True,
            extra={
                'request': request,
                'data': {
                    'user': user
                }
            }
        )
        raise
    
    LOGGER.info(change_message, exc_info=True, extra={
        'stack': True,
        'request': request,
        'data': {
            'user': user
        }
    })