===============
Model Resources
===============

.. automodule:: hyperadmin.resources.models.models

-------------
ModelResource
-------------

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


ModelResource options
---------------------

* model
* fields
* exclude
* paginator
* list_display
* list_filter (basic filters, don't know about custom)
* list_per_page
* form_class
* inlines (not auto imported yet)

The params queryset, ordering, search_fields, list_select_related and date_hierarchy are planned.


API Endpoints
-------------

* "/" lists rows; POST to create
* "/add/" POST to add
* "/<id>/" displays a specific row; PUT/POST to update, DELETE to delete
* "/<id>/delete/" POST to delete

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
