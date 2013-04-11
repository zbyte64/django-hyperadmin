Installation
============

------------
Requirements
------------

* Python 2.6 or later
* Django 1.3 or later
* django-datatap

--------
Settings
--------

Put 'hyperadmin' into your ``INSTALLED_APPS`` section of your settings file.

And the following to urls.py::

    import hyperadmin
    hyperadmin.autodiscover() #TODO this does nothing
    hyperadmin.site.install_models_from_site(admin.site) #ports admin models to hyperadmin
    hyperadmin.site.install_storage_resources() #enables the storage resource for media and static

Add to root url patterns::

    url(r'^hyperapi/', include(hyperadmin.site.urls)),


(Optional) Install a client:

* :ref:`clients`

(Optional) Install additional authenticators:

* :ref:`authentication`
