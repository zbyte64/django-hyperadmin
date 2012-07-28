=================
Django-Hyperadmin
=================

Roadmap/Brainstorm

Installation
============

Put 'hyperadmin' into your ``INSTALLED_APPS`` section of your settings file.

Add to root url patterns::

    url(r'^hyper-admin/', include(hyperadmin.site.urls)),

And the following to urls.py::

    import hyperadmin
    hyperadmin.autodiscover()


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

Admin Actions
=============

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

* list display
* list filters
* search
* pagination
* date hierarchy
* ordering
* form manipulations (exclude, markup, readonly)
* logging



Backporting
===========

Converting admin models from within::

    from hyperadmin import TransitionalAdminModel
    from django.contrib import admin
    from myapp.models import MyModel
    
    admin.site.register(MyModel, TransitionalAdminModel)


This admin model would be built ontop the standard admin model but would inject extra context to load up the ember.js interface. Additionally it registers the model with the hyperadmin.
~ 2 days to integrate



