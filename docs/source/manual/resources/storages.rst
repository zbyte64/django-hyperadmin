===============
StorageResource
===============

.. automodule:: hyperadmin.resources.storages.storages

.. autoclass:: StorageResource
   :members:
   :undoc-members:

Allows for direct browsing and uploading of files. The storage backend may optionally provide a custom link object to facilitate direct uploading to a CDN.

API Endpoints
-------------

* "/storages/media/" lists directories and files
* "/storages/media/?path=<path>" lists directories and files belonging to a certain path
* "/storages/media/<path>/" endpoint for updating a particular file
* "/storages/static/"
* "/storages/static/<path>/"

