.. image:: https://secure.travis-ci.org/zbyte64/django-hyperadmin.png?branch=master
   :target: http://travis-ci.org/zbyte64/django-hyperadmin


Introduction
============

django-hyperadmin is an Admin interface for resources in Django that are powered by Hypermedia REST APIs.

This is ALPHA

--------
Features
--------
* Supported Media Formats:
 * application/vnd.Collection+JSON
 * application/vnd.Collection.next+JSON
 * application/text-html - for browsing
* Build API Resources like building and Admin Model

Installation
============

Put 'hyperadmin' into your ``INSTALLED_APPS`` section of your settings file.

And the following to urls.py::

    import hyperadmin
    hyperadmin.autodiscover() #TODO this does nothing
    hyperadmin.site.install_models_from_site(admin.site)

Add to root url patterns::

    url(r'^hyper-admin/', include(hyperadmin.site.urls)),


Builtin Resources
=================

SiteResource
------------

API Endpoints

* "/" lists resources known in the system. Additionally provides an html fallback to load up the ember.js interface.
* "/authentication/" ; PUT/POST to authenticate, DELETE to logout, GET for useful info and login forms. Uses django sessions by default.

ApplicationResource
-------------------

API Endpoints

* "/<appname>/" lists resources belonging to the app
* "/<appname>/<module>/" mount point of crud resource

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

TODO: Admin Actions
-------------------

Admin actions are functions that return a link object. 
If the action is a string then it is assumed to be the function of the resource. The string is mapped as a url and a link object is automatically generated for it. The ``ActionResourceView`` returns a response with the main form being the link object and the post going to the function of the admin.

Unknowns
--------

* inlines
* fieldsets
* display hints? 
* custom controls; some fields may need to specify custom front-end logic so there needs to be away to register new controls in the frontend

Inlines: Make it a sub resource. Inline information & templates are slurped in at the top resource but adding another inline would be an ajax call. May add new field type "schema" which nests in a subtemplate.

Link/Form display hints:
* field inline, display result inlined with a field
* module inline, display towards the bottom of the page, group the resources
* page inline, new page but indicate that it is one nested in


Idea: transactional resource creation (documents only).

TODO
----

* changelist
 * list display
 * search
 * date hierarchy
* form manipulations
 * readonly
 * markup
* logging
* permissions
* admin actions



TODO: Backporting
=================

Converting admin models from within::

    from hyperadmin import TransitionalAdminModel
    from django.contrib import admin
    from myapp.models import MyModel
    
    admin.site.register(MyModel, TransitionalAdminModel)


This admin model would be built ontop the standard admin model but would inject extra context to load up the ember.js interface. Additionally it registers the model with the hyperadmin.
~ 2 days to integrate


TODO: Client
============

resource <=> hfactor <=> media type <=> |browser| <=> media type layer <=> template engine / js form handler / css



Hypermedia APIs
===============

http://www.amundsen.com/hypermedia/hfactor/

http://code.ge/media-types/collection-next-json/
