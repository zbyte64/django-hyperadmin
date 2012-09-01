.. image:: https://secure.travis-ci.org/zbyte64/django-hyperadmin.png?branch=master
   :target: http://travis-ci.org/zbyte64/django-hyperadmin


Introduction
============

django-hyperadmin is an Admin interface for resources in Django that are powered by Hypermedia REST APIs.

This is ALPHA

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


Builtin Resources
=================

SiteResource
------------

API Endpoints

* "/" lists resources known in the system. Additionally provides an html fallback to load up the ember.js interface.
* "/_authentication/" ; PUT/POST to authenticate, DELETE to logout, GET for useful info and login forms. Uses django sessions by default.

ApplicationResource
-------------------

API Endpoints

* "/<appname>/" lists resources belonging to the app
* "/<appname>/<module>/" mount point of crud resource

StorageResource
---------------

API Endpoints

* "/storages/media/" lists directories and files
* "/storages/media/?path=<path>" lists directories and files belonging to a certain path
* "/storages/media/<path>/" endpoint for updating a particular file
* "/storages/static/"
* "/storages/static/<path>/"

Registering models
==================

Registering a model with hyperadmin::

    import hyperadmin
    from hpyeradmin.resources imoprt ModelResource, InlineModelResource
    from myapp.models import MyModel, ChildModel
    
    class ChildModelResource(InlineModelResource):
        model = ChildModel
    
    class MyModelResource(ModelResource):
        inlines = [ChildModelResource]
    
    hyperadmin.site.register(MyModel, MyModelResource)

Each resource has it's own url patterns and links the urls through hypermedia links. There will be a going back and forth between the frontend needs and defining extra metadata in an extended version of the collections media type. Hyperadmin facilitates this by allowing for custom mediatypes to be defined. The ember.js client should treat each view as uniformally as possible as all the contextual data should be contained in the API.


Client
======

Currently there is one client written using emberjs. See ``hyperadmin.clients.emberjs.EmberJSClient``
This client is able to browse the API and perform CRUD operations. There are plans to support inlines and file uploading.

TODOs
=====

Admin Actions
-------------

Admin actions are functions that return a link object. 
If the action is a string then it is assumed to be the function of the resource. The string is mapped as a url and a link object is automatically generated for it. The ``ActionResourceView`` returns a response with the main form being the link object and the post going to the function of the admin.

Unknowns
--------

* inlines
* fieldsets - perhaps this should be configured client side
* custom controls; some fields may need to specify custom front-end logic so there needs to be away to register new controls in the frontend

Inlines: Make it a sub resource. Inline information & templates are slurped in at the top resource but adding another inline would be an ajax call. May add new field type "schema" which nests in a subtemplate.

Link/Form display hints:
* field inline, display result inlined with a field
* module inline, display towards the bottom of the page, group the resources
* page inline, new page but indicate that it is one nested in


Idea: transactional resource creation (documents only).

Other Features
--------------

* changelist
 * search
 * date hierarchy
* form manipulations
 * readonly
 * markup
* logging
* permissions
* admin actions


Hypermedia APIs
===============

http://www.amundsen.com/hypermedia/hfactor/

http://code.ge/media-types/collection-next-json/

