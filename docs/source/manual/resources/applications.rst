=====================
Application Resources
=====================

.. automodule:: hyperadmin.resources.applications

------------
SiteResource
------------

.. automodule:: hyperadmin.resources.applications.site

API Endpoints
-------------

* "/" lists resources known in the system.
* "/_authentication/" ; PUT/POST to authenticate, DELETE to logout, GET for useful info and login forms. Uses django sessions by default.


Methods
-------

.. autoclass:: SiteResource
   :members:
   :undoc-members:

-------------------
ApplicationResource
-------------------

.. automodule:: hyperadmin.resources.applications.application

API Endpoints
-------------

* "/<appname>/" lists resources belonging to the app
* "/<appname>/<module>/" mount point of crud resource

Methods
-------

.. autoclass:: ApplicationResource
   :members:
   :undoc-members:
