from django.utils.functional import Promise
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
from django.core.serializers.json import DjangoJSONEncoder


class HyperadminJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(HyperadminJSONEncoder, self).default(obj)
