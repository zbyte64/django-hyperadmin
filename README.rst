.. image:: https://secure.travis-ci.org/zbyte64/django-hyperadmin.png?branch=master
   :target: http://travis-ci.org/zbyte64/django-hyperadmin

============
Introduction
============

django-hyperadmin is an API driven Admin interface for resources in Django. Resources tend to be anything you can manipulate with a form (including models) and you configure your API resource like you would an Admin Model. The current client is written in emberjs and is powered by a Hypermedia REST API.

This is (mostly) ALPHA

--------
Features
--------
* ModelResource works like AdminModel
* StorageResource for RESTful media uploads
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

============
Installation
============

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

=================
Builtin Resources
=================

Each resource has it's own url patterns and links the urls through hypermedia links. There will be a going back and forth between the frontend needs and defining extra metadata in an extended version of the collections media type. The ember.js client should treat each view as uniformally as possible as all the contextual data should be contained in the API.

------------
SiteResource
------------

API Endpoints
-------------

* "/" lists resources known in the system.
* "/_authentication/" ; PUT/POST to authenticate, DELETE to logout, GET for useful info and login forms. Uses django sessions by default.

-------------------
ApplicationResource
-------------------

API Endpoints
-------------

* "/<appname>/" lists resources belonging to the app
* "/<appname>/<module>/" mount point of crud resource

---------------
StorageResource
---------------

Allows for direct browsing and uploading of files. The storage backend may optionally provide a custom link object to facilitate direct uploading to a CDN.

API Endpoints
-------------

* "/storages/media/" lists directories and files
* "/storages/media/?path=<path>" lists directories and files belonging to a certain path
* "/storages/media/<path>/" endpoint for updating a particular file
* "/storages/static/"
* "/storages/static/<path>/"

-------------
ModelResource
-------------

API Endpoints
-------------

* "/" lists rows; POST to create
* "/<id>/" displays a specific row; POST to update, DELETE to delete

Registering models
-------------------

Registering a model with hyperadmin::

    import hyperadmin
    from hpyeradmin.resources imoprt ModelResource, InlineModelResource
    from myapp.models import MyModel, ChildModel
    
    class ChildModelResource(InlineModelResource):
        model = ChildModel
    
    class MyModelResource(ModelResource):
        inlines = [ChildModelResource]
        list_display = ['name', 'number']
        list_filter = ['timestamp', 'category']
    
    hyperadmin.site.register(MyModel, MyModelResource)


======
Client
======

Currently there is one client written using emberjs. See ``hyperadmin.clients.emberjs.EmberJSClient``
This client is able to browse the API and perform CRUD operations. There are plans to support inlines and file uploading.

=============================
Reading up on Hypermedia APIs
=============================

http://www.amundsen.com/hypermedia/hfactor/

http://code.ge/media-types/collection-next-json/

