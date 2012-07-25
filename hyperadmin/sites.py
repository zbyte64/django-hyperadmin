class ResourceSite(object):
    def register_media_type(self, media_type, media_type_handler):
        self.media_types[media_type] = media_type_handler

site = ResourceSite()
from mediatypes import BUILTIN_MEDIA_TYPES
for key, value in BUILTIN_MEDIA_TYPES.iteritems():
    site.register_media_type(key, value)
