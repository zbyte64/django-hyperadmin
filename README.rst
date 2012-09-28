.. image:: https://secure.travis-ci.org/zbyte64/django-hyperadmin.png?branch=master
   :target: http://travis-ci.org/zbyte64/django-hyperadmin

============
Introduction
============

django-hyperadmin is an API driven Admin interface for resources in Django. Resources tend to be anything you can manipulate with a form (including models) and you configure your API resource like you would an Admin Model. The current client is written in emberjs and is powered by a Hypermedia REST API.

This is (mostly) ALPHA

Documentation: http://django-hyperadmin.readthedocs.org/

Demo site: http://hyperadmindemo.herokuapp.com/

--------
Features
--------
* ModelResource works like AdminModel
* StorageResource powers file uploads in client
* Supported Media Formats:
 * application/vnd.Collection+JSON
 * application/vnd.Collection.next+JSON
 * application/vnd.Collection.hyperadmin+JSON - for the emberjs client
 * application/text-html - for browsing
 * application/json - plain json serialization
 * text/javascript - for jsonp
 * TODO: xml, yaml, ???
* Architecture allows for more media formats
* Internal resource representation based on hfactor and forms
* Headers control media type; "Accepts" and "Content-Type" control response and request format
* Clients packaged seperately


------------
Requirements
------------

* Python 2.6 or later
* Django 1.3 or later


============
Installation
============

Put 'hyperadmin' into your ``INSTALLED_APPS`` section of your settings file.

And the following to urls.py::

    import hyperadmin
    hyperadmin.autodiscover() #TODO this does nothing
    hyperadmin.site.install_models_from_site(admin.site) #ports admin models to hyperadmin
    hyperadmin.site.install_storage_resources() #enables the storage resource for media and static

Add to root url patterns::

    url(r'^hyperapi/', include(hyperadmin.site.urls)),


(Optional) Install a client:

* https://github.com/zbyte64/django-hyperadmin-emberclient
* https://github.com/zbyte64/django-hyperadmin-client

=============
Configuration
=============

-------------
ModelResource
-------------

API Endpoints
-------------

* "/" lists rows; POST to create
* "/add/" POST to add
* "/<id>/" displays a specific row; PUT/POST to update, DELETE to delete
* "/<id>/delete/" POST to delete

Registering models
-------------------

Registering a model with hyperadmin::

    import hyperadmin
    from hpyeradmin.resources.models imoprt ModelResource, InlineModelResource
    from myapp.models import MyModel, ChildModel
    
    class ChildModelResource(InlineModelResource):
        model = ChildModel
    
    class MyModelResource(ModelResource):
        inlines = [ChildModelResource]
        list_display = ['name', 'number']
        list_filter = ['timestamp', 'category']
    
    hyperadmin.site.register(MyModel, MyModelResource)


=======
Clients
=======

Emberjs Client: https://github.com/zbyte64/django-hyperadmin-emberclient
Django Template Client: https://github.com/zbyte64/django-hyperadmin-client

Visiting the api endpoint in a browser will let you browse the various hyberobjects made available through the resource.


=============================
Reading up on Hypermedia APIs
=============================

http://www.amundsen.com/hypermedia/hfactor/

http://code.ge/media-types/collection-next-json/

