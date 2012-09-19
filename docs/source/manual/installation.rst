Installation
============

------------
Requirements
------------

* Python 2.6 or later
* Django 1.3 or later

--------
Settings
--------

Put 'hyperadmin' into your ``INSTALLED_APPS`` section of your settings file.

And the following to urls.py::

    import hyperadmin
    from hyperadmin.clients import EmberJSClient
    hyperadmin.autodiscover() #TODO this does nothing
    hyperadmin.site.install_models_from_site(admin.site) #ports admin models to hyperadmin
    hyperadmin.site.install_storage_resources() #enables the storage resource for media and static
    admin_client = EmberJSClient(api_endpoint='/hyper-admin/')

Add to root url patterns::

    url(r'^hyper-admin/', include(hyperadmin.site.urls)),
    url(r'^emberjs-admin/', include(admin_client.urls)),

