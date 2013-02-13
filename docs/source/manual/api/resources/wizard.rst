================
Wizard Resources
================

.. automodule:: hyperadmin.resources.wizard

------
Wizard
------

API Endpoints
-------------

* "/" loads the wizard, lists the substeps. POST to skip steps

Methods
-------

.. autoclass:: Wizard
   :show-inheritance:
   :members:
   :undoc-members:


--------
FormStep
--------

API Endpoints
-------------

* "/<slug>/" POST to submit step

Methods
-------

.. autoclass:: FormStep
   :show-inheritance:
   :members:
   :undoc-members:

-------------
MultiPartStep
-------------

API Endpoints
-------------

* "/<slug>/" POST to skip substeps
* "/<slug>/<substep>/" POST to submit substep

Methods
-------

.. autoclass:: MultiPartStep
   :show-inheritance:
   :members:
   :undoc-members:

