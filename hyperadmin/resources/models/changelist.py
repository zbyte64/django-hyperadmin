import operator

from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.core.paginator import InvalidPage
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode, smart_str
from django.utils.translation import ugettext, ugettext_lazy
from django.utils.http import urlencode
from django.test.client import RequestFactory

from django.contrib.admin import FieldListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import (quote, get_fields_from_path,
    lookup_needs_distinct, prepare_lookup_value)

# Changelist settings
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
TO_FIELD_VAR = 't'
IS_POPUP_VAR = 'pop'
ERROR_FLAG = 'e'

IGNORED_PARAMS = (
    ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, TO_FIELD_VAR)

# Text to display within change-list table cells if the value is blank.
EMPTY_CHANGELIST_VALUE = ugettext_lazy('(None)')

