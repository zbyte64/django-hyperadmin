from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

import hyperadmin
hyperadmin.autodiscover()

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    hyperadmin.site.install_models_from_site(admin.site) #ports admin models to hyperadmin

hyperadmin.site.install_storage_resources() #enables the storage resource for media and static

urlpatterns = patterns('',
    url(r'', include(hyperadmin.site.urls)),
)

