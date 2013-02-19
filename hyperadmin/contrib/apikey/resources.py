from hyperadmin import site
from hyperadmin.resources.models import ModelResource

from hyperadmin.contrib.apikey.models import ApiKey


class ApiKeyResource(ModelResource):
    model = ApiKey

site.register(ApiKey, ApiKeyResource, app_name='apikey')

