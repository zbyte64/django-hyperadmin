.. image:: https://secure.travis-ci.org/zbyte64/django-hyperadmin.png
   :target: http://travis-ci.org/zbyte64/django-hyperadmin

============
Introduction
============

django-hyperadmin is an API framework for building RESTful resources in Django. Resources tend to be anything you can manipulate with forms (including models) and configuration of an API resource is similar to an Admin Model. APIs support REST out of the box and clients may be installed seperately to provide additional functionality.

This is BETA

Documentation: http://django-hyperadmin.readthedocs.org/

--------
Features
--------
* ModelResource works like AdminModel
* StorageResource powers file uploads in client
* Data store agnostic
* Supported Media Formats:
 * application/text-html, text/html - provides HTML responses
 * application/vnd.Collection+JSON
 * application/vnd.Collection.next+JSON
 * application/vnd.Collection.hyperadmin+JSON - for the emberjs client
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

Add to root url patterns::

    url(r'^hyperapi/', include('hyperadmin.urls')),


=======
Clients
=======

Visiting the api endpoint in a browser will let you browse the various hyberobjects made available through the resource. Clients may be installed on a different url.

----------------------
Django Template Client
----------------------

https://github.com/zbyte64/django-hyperadmin-client

Uses django templates to render an admin interface. Responsive design out of the box.

-----------------
Ember REST Client
-----------------

https://github.com/zbyte64/django-hyperadmin-emberclient

Uses REST calls and emberjs to render an admin interface.

-----------------
Backbone Bindings
-----------------

https://github.com/zbyte64/django-hyperadmin-backboneclient

Provides basic bindings to the Backbone API.

----------
Dockit CMS
----------

https://github.com/zbyte64/django-dockitcms (endpoints branch)

A dynamic API builder with a public HTML (template driven) client.


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


=============================
Reading up on Hypermedia APIs
=============================

http://www.amundsen.com/hypermedia/hfactor/

http://code.ge/media-types/collection-next-json/

