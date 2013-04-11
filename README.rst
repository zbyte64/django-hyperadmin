.. image:: https://secure.travis-ci.org/zbyte64/django-hyperadmin.png
   :target: http://travis-ci.org/zbyte64/django-hyperadmin

============
Introduction
============

django-hyperadmin is a HATEOAS API framework for building resources in Django. Resources are anything that can be manipulated with forms and configuration of a Resource is similar to that of an Admin Model. While Resources offer a REST CRUD layer out of the box they are meant to power workflows that go beyond CRUD. Additionally Resources aim to be reusable throughout the web application and not to be limitted to a single API endpoint.

This is BETA

Documentation: http://django-hyperadmin.readthedocs.org/

--------
Features
--------
* ModelResource works like AdminModel
* Data store agnostic
* Media type agnostic
* Index classes define search and filter capabilities through forms
* Autoloads basic functionality from admin site
* Inline support
* Clients packaged seperately
* Throttling
* API key authentication
* Wizard workflows

Supported Media Formats:

* application/text-html, text/html - provides HTML responses
* application/json - plain json serialization, uses datataps
* text/javascript - for jsonp
* application/vnd.Collection+JSON
* application/vnd.Collection.next+JSON
* application/vnd.Collection.hyperadmin+JSON - for the emberjs client
* TODO: xml, yaml, ???

Headers control media type; "Accepts" and "Content-Type" control response and request format

------------
Requirements
------------

* Python 2.6 or later
* Django 1.3 or later
* django-datatap


===============
Help & Feedback
===============

We have a mailing list for general discussion and help: http://groups.google.com/group/django-hyperadmin/

============
Installation
============

Install hyperadmin into your python environment::

    pip install django-hyperadmin

or::

    pip install -e git+git://github.com/webcube/django-hyperadmin.git#egg=django-hyperadmin


Put 'hyperadmin' into your ``INSTALLED_APPS`` section of your settings file.

Add to root url patterns::

    url(r'^hyperapi/', include('hyperadmin.urls')),


=============
Configuration
=============

------------------
Registering models
------------------

Registering a model with hyperadmin::

    import hyperadmin
    from hpyeradmin.resources.models import ModelResource, InlineModelResource
    from myapp.models import MyModel, ChildModel
    
    class ChildModelResource(InlineModelResource):
        model = ChildModel
    
    class MyModelResource(ModelResource):
        inlines = [ChildModelResource]
        list_display = ['name', 'number']
        list_filter = ['timestamp', 'category']
    
    hyperadmin.site.register(MyModel, MyModelResource)


API Endpoints
-------------

* "/" lists rows; POST to create
* "/add/" POST to add
* "/<id>/" displays a specific row; PUT/POST to update, DELETE to delete
* "/<id>/delete/" POST to delete

Inline API Endpoints
--------------------

* "/<parent_id>/(relname)/" lists rows; POST to create
* "/<parent_id>/(relname)/add/" POST to add
* "/<parent_id>/(relname)/<id>/" displays a specific row; PUT/POST to update, DELETE to delete
* "/<parent_id>/(relname)/<id>/delete/" POST to delete

-----------------------------
Autoloading from Django Admin
-----------------------------

The following registers the models from admin site (this is already done if you import from ``hyperadmin.urls``)::

    from hyperadmin.resources.models.autload import DjangoCTModelAdminLoader
    from django.contrib.admin import site as admin_site
    from hyperadmin import site as root_endpoint
    
    loader = DjangoCTModelAdminLoader(root_endpoint, admin_site)
    loader.register_resources()


=======
Clients
=======

Visiting the api endpoint in a browser will let you browse the various hyberobjects made available through the resource. Clients may be installed on a different url.

----------------------
Django Template Client
----------------------

https://github.com/webcube/django-hyperadmin-client

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

https://github.com/webcube/django-dockitcms

A dynamic API builder with a public HTML (template driven) client.

=============================
Reading up on Hypermedia APIs
=============================

http://www.amundsen.com/hypermedia/hfactor/

http://code.ge/media-types/collection-next-json/

