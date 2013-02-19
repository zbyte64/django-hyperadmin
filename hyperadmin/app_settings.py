from django.conf import settings
from django.utils.importlib import import_module


path = getattr(settings, 'DEFAULT_API_REQUEST_CLASS', 'hyperadmin.apirequests.HTTPAPIRequest')
path, classname = path.rsplit('.', 1)

DEFAULT_API_REQUEST_CLASS = getattr(import_module(path), classname)

