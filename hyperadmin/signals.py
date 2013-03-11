'''
NOTE: the construction of the sender is based on the urlname and the event.
This allows for listeners to be registered independently of resource construction.
'''

from django.dispatch import Signal


endpoint_event = Signal(providing_args=["endpoint", "event", "item_list"])
endpoint_event.__doc__ = '''
Sent by the endpoint when an event occurs

:param sender: The full url name of the endpoint + ! + the event
:param endpoint: The endpoint emitting the event
:param event: A string representing the event
:param item_list: An item list for which the event applies, may be empty
'''

resource_event = Signal(providing_args=["resource", "event", "item_list"])
resource_event.__doc__ = '''
Sent by the resource when an event occurs

:param sender: The full url name of the resource + ! + the event
:param resource: The resource emitting the event
:param event: A string representing the event
:param item_list: An item list for which the event applies, may be empty
'''
