===============
Model Resources
===============

.. automodule:: hyperadmin.resources.models

-------------
ModelResource
-------------

Registering models
-------------------

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


Options
-------

* model
* fields
* exclude
* paginator
* list_display
* list_filter (basic filters, don't know about custom)
* search_fields
* list_per_page
* form_class
* inlines

The params queryset, ordering, search_fields, list_select_related and date_hierarchy are planned.

Autoloaded Options
------------------

These options are mapped to the ModelResource when using autoload.

* model
* fields
* fieldsets (flattened to provide fields)
* exclude
* paginator
* list_display
* list_filter (basic filters, don't know about custom)
* search_fields
* list_per_page
* form_class
* inlines


API Endpoints
-------------

* "/" lists rows; POST to create
* "/add/" POST to add
* "/<id>/" displays a specific row; PUT/POST to update, DELETE to delete
* "/<id>/delete/" POST to delete

Methods
-------

.. autoclass:: ModelResource
   :show-inheritance:
   :members:
   :undoc-members:


-------------------
InlineModelResource
-------------------

Methods
-------

.. autoclass:: InlineModelResource
   :show-inheritance:
   :members:
   :undoc-members:

API Endpoints
-------------

* "/<parent_id>/(relname)/" lists rows; POST to create
* "/<parent_id>/(relname)/add/" POST to add
* "/<parent_id>/(relname)/<id>/" displays a specific row; PUT/POST to update, DELETE to delete
* "/<parent_id>/(relname)/<id>/delete/" POST to delete


--------------------------
GenericInlineModelResource
--------------------------

.. automodule:: hyperadmin.resources.models.generic

Methods
-------

.. autoclass:: GenericInlineModelResource
   :show-inheritance:
   :members:
   :undoc-members:

