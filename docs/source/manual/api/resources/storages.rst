===============
StorageResource
===============

.. automodule:: hyperadmin.resources.storages


Allows for direct browsing and uploading of files. The storage resource includes an endpoint for generating a direct upload link.

API Endpoints
-------------

* "/storages/media/" lists directories and files
* "/storages/media/?path=<path>" lists directories and files belonging to a certain path
* "/storages/media/upload-link/" POST to create a direct upload link
* "/storages/media/<path>/" endpoint for updating a particular file
* "/storages/static/"
* "/storages/static/<path>/"


Methods
-------

.. autoclass:: StorageResource
   :show-inheritance:
   :members:
   :undoc-members:
