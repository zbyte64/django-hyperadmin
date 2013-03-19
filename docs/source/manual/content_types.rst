=============
Content Types
=============

Media Type Selection
====================

The incomming media type is handled seperately from the outgoing media type. The selection of each media type can be controlled with the following HTTP headers:

**Accept**: Specifies the media type of the response

**Content-Type**: Specifies the media type of the request

Alternatively they may also be controlled by the following GET parameters:

**_HTTP_ACCEPT**: Specifies the media type of the response

**_CONTENT_TYPE**: Specifies the media type of the request

Note: When passing a media type through the url, replace all "+" symbols with "%2B" or else the browser will replace the "+" symbol with a space and the media type will not be recognized.

