===============
Admin Resources
===============

Each resource has it's own url patterns and links the urls through hypermedia links. These resources have methonds for collecting links and views for handling actions on those links.

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

