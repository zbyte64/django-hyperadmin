=============
Content Types
=============

Hyperadmin supports 3 different modes of content types:

* HTML - renders a response using the django template engine
* Hypermedia - renders a structured response representing a workflow and data (ie application/vnd.collection+json)
* Datatap - renders and loads fixtures (ie application/json)

Media Type Selection
====================

The incomming media type is handled seperately from the outgoing media type. The selection of each media type can be controlled with the following HTTP headers:

**Accept**: Specifies the media type of the response

**Content-Type**: Specifies the media type of the request

Alternatively they may also be controlled by the following GET parameters:

**_HTTP_ACCEPT**: Specifies the media type of the response

**_CONTENT_TYPE**: Specifies the media type of the request

**Note**: Arguments passed by the GET method needs to be URL encoded. In JavaScript you can use the built-in `encodeURIComponent` method like so:

.. code-block:: javascript

    var contentType = encodeURIComponent('application/vnd.Collection.hyperadmin+JSON')

