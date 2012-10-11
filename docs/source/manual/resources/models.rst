===============
Model Resources
===============

.. automodule:: hyperadmin.resources.models.models

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


Methods
-------

.. autoclass:: ModelResource
   :members:
   :undoc-members:


-------------------
InlineModelResource
-------------------

Methods
-------

.. autoclass:: InlineModelResource
   :members:
   :undoc-members:
