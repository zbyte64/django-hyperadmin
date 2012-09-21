//TODO put this elsewhere
jQuery(function($) {
    $.extend({
        serializeJSON: function(obj) {
            var t = typeof(obj);
            if(t != "object" || obj === null) {
                // simple data type
                if(t == "string") obj = '"' + obj + '"';
                return String(obj);
            } else {
                // array or object
                var json = [], arr = (obj && obj.constructor == Array);
 
                $.each(obj, function(k, v) {
                    t = typeof(v);
                    if(t == "string") v = '"' + v + '"';
                    else if (t == "object" & v !== null) v = $.serializeJSON(v)
                    json.push((arr ? "" : '"' + k + '":') + String(v));
                });
 
                return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}");
            }
        }
    });
});

var App = Em.Application.create({});
App.contentType = 'application/vnd.Collection.hyperadmin+JSON';

App.ApplicationController = Ember.Controller.extend();

//here we define our data objects
App.CommonObject = Em.Object.extend({
  css_class: function() {
    var classes = this.get('classes');
    if (classes) {
      return classes.join(' ');
    }
    return '';
  }.property('classes')
});
App.Link = App.CommonObject.extend({
  url: function() {
    var url = this.get('href');
    if (url.charAt(0) != '/') {
        url = App.resourceController.collection.get('url') + url
    }
    return url
  }.property('href'),
  apiUrl: function() {
    var apiUrl = this.get('url')
    var base_url = App.resourceController.get('apiUrl')
    if (apiUrl.indexOf(base_url) == 0) {
        apiUrl = apiUrl.substr(base_url.length)
    }
    return apiUrl
  }.property('href'),
  emberUrl: function() {
    return '#'+this.get('apiUrl');
  }.property('href')
})
App.Query = App.Link.extend({})
App.Item = App.Link.extend({
  getLinks: function() {
    var links = this.get('links')
    var data = Em.ArrayController.create({'content':Array()})
    if (!links) return data;
    for (var i=0; i<links.length; i++) {
        var item_data = links[i];
        var item = App.Link.create(item_data);
        data.pushObject(item);
    }
    return data;
  }.property('links').cacheable()
})
App.Field = App.CommonObject.extend({
  isSelect: function() {
    return this.get('type') == 'select';
  }.property('type'),
  isChecked: function() {
    if (this.get('type') != 'checkbox') {
      return false;
    }
    return this.get('value');
  }.property('type', 'value')
})
App.Template = App.Link.extend({
  fields: function() {
    var fields = Array();
    var data = this.get('data');
    if (data) {
      for (var i=0; i<data.length; i++) {
        var field = App.Field.create(data[i])
        fields.pushObject(field)
      }
    }
    return fields;
  }.property('data')
})
App.Error = Em.Object.extend({})

App.makeControllerProperty = function(controller_class, item_class, key) {
    function_controller = function() {
        var data = controller_class.create({'content':Array()})
        var cdata = this.get('data')
        if (!cdata) return data;
        var subdata = cdata[key];
        if (!subdata) return data;
        for (var i=0; i<subdata.length; i++) {
            var item_data = subdata[i];
            var item = item_class.create(item_data);
            data.pushObject(item);
        }
        return data;
    }
    return function_controller.property('data.'+key).cacheable()
}
App.makeSimpleProperty = function(key, item_class) {
    attr_property = function() {
        var cdata = this.get('data')
        if (!cdata) return null;
        var subdata = cdata[key];
        if (item_class && subdata) {
            return item_class.create(subdata);
        }
        return subdata
    }
    return attr_property.property('data.'+key).cacheable()
}

App.QueriesController = Em.ArrayController.extend({
    sortby: function() {
        return this.filterProperty('rel', 'sortby')
    }.property('@each.rel').cacheable(),
    filters: function() {
        return this.filterProperty('rel', 'filter')
    }.property('@each.rel').cacheable(),
    pagination: function() {
        return this.filterProperty('rel', 'pagination')
    }.property('@each.rel').cacheable(),
    breadcrumbs: function() {
        return this.filterProperty('rel', 'breadcrumb')
    }.property('@each.rel').cacheable()
})
App.TemplatesController = Em.ArrayController.extend({})
    
App.CollectionController = Em.ObjectController.extend({
    data: null, //powers all data bound to it
    namespace: App.makeSimpleProperty('namespace'),
    version: App.makeSimpleProperty('version'),
    href: App.makeSimpleProperty('href'),
    resource_class: App.makeSimpleProperty('resource_class'),
    isResourceListing: function() {
        return this.get('resource_class') == 'resourcelisting'
    }.property('resource_class'),
    isCrudResource: function() {
        return this.get('resource_class') == 'crudresource'
    }.property('resource_class'),
    display_fields: App.makeControllerProperty(Em.ArrayController, App.CommonObject, 'display_fields'),
    url: function() {
        var url = this.get('href');
        var end_pos = url.indexOf('?')
        if (end_pos > -1) {
            url = url.substr(0, end_pos)
        }
        return url
    }.property('href'),
    links: App.makeControllerProperty(App.QueriesController, App.Query, 'links'),
    items: App.makeControllerProperty(Em.ArrayController, App.Item, 'items'),
    queries: App.makeControllerProperty(App.QueriesController, App.Query, 'queries'),
    templates: App.makeControllerProperty(App.TemplatesController, App.Template, 'templates'),
    error: App.makeSimpleProperty('error', App.Error),
    namespaces: function() {
        var data = Em.ArrayController.create({'content':Array()})
        var cdata = this.get('data')
        if (!cdata) return data;
        var subdata = cdata['namespaces'];
        if (!subdata) return data;
        
        for (var name_key in subdata) {
            var namespace = App.CollectionController.create({})
            namespace.handleResponse(subdata[name_key])
            data.pushObject(namespace);
        }
        return data
    }.property('data.namespaces').cacheable(),
    handleResponse: function(data) {
        this.set('data', data)
        console.log(this, data)
    }
})

App.uploadingFiles = false;
App.initUploadFile = function(field, options) {
  console.log('upload init', field, options)
  function add(e, data) {
    console.log('upload add', e, data)
    App.uploadingFiles = true;
    
    var fileInput = $(e.target);
    var file = data.files[0];
    fileInput.siblings('.uploadstatus').remove()
    fileInput.after('<span class="uploadstatus">Uploading: '+file.name+'<span class="uploadprogress">&nbsp;</span></span>')
    fileInput.hide()
    
    //TODO this is only necessary because forms insist on resaving and "upload to" is not communicated
    data.formData = {'name':'hyperadmin-tmp/'+file.name}
    data.submit()
  }
  function progress(e, data) {
    console.log('upload progress', e, data)
    var fileInput = $(e.target);
    var progress = parseInt(data.loaded / data.total * 100, 10);
    fileInput.siblings('.uploadstatus').find('.uploadprogress').text(progress+'%')
  }
  function fail(e, data) {
    console.log('upload fail', e, data)
  }
  function done(e, data) {
    console.log('upload done', e, data)
    var fileInput = $(e.target);
    var fields = $.parseJSON(data.result).collection.items[0]['data']
    var path = null;
    var file = data.files[0]
    console.log(fields)
    for(var i=0; i<fields.length; i++) {
      var field = fields[i];
      if (field.name == 'name') {
        path = field.value;
        break;
      }
    }
    
    function remove_click() {
      fileInput.data('path', null);
      fileInput.siblings('.uploadstatus').remove()
      fileInput.show()
    }
    
    fileInput.data('api-skip', true);
    fileInput.data('path', path);
    fileInput.siblings('.uploadstatus').remove()
    fileInput.after('<span class="uploadstatus">File uploaded: '+file.name+' <a href="#">Remove</a><input name="'+fileInput.attr('name')+'" value="'+path+'" type="hidden"/></span>')
    fileInput.siblings('.uploadstatus').find('a').click(remove_click)
    fileInput.siblings('.uploadstatus').find(':input').data('api-type', 'file')
    
    var form = get_form(this)
    if (form.data('submitted')) {
      //TODO submit form
    }
  }
  function stop(e) {
    console.log('upload stop', e)
    App.uploadingFiles = false;
  }
  
  function get_form(item) {
    return $(item).parents('form:first')
  }
  var options = $.extend({
        //'onUploadSuccess': on_upload_success,
        'add': add,
        //'progress': progress,
        'fail': fail,
        'done': done,
        'stop': stop,
        //'onUploadError': on_upload_error,
        //'onUploadCancel': on_upload_cancel,
        'autoUpload': true,
        'multi': false,
        //'removeCompleted': false,
        //'uploadLimit': 1,
        'async': true,
        'type': 'POST',
        'url': '/hyper-admin/-storages/media/add/',
        'paramName': 'upload',
        'accepts': {
          'json': App.contentType, //custom media type defintion
        },
        'headers': {
            'Accept': App.contentType,
            //'Content-Type': 'multipart/form-data'
            //'Content-Type': 'text/html'
        }
    }, options);
    field.fileupload(options);
}

//define a controller for managing these data objects
//views bind to this and are automatically updated when the controller issues update actions
App.resourceController = Em.ObjectController.create({
    apiUrl: null,
    collection: App.CollectionController.create({}), 
    followLink: function(url) {
        var settings = $.extend({}, App.requestDefaults, {
            url: url,
            success: this.handleResponse
        })
        $.ajax(settings)
    },
    submitForm: function(form) {
        var payload = App.serializeFormJSON(form)
        console.log(payload)
        var settings = $.extend({}, App.requestDefaults, {
            url: form.attr('target'),
            type: form.attr('method') || 'POST',
            data: payload,
            success: this.handleResponse,
            contentType: App.contentType
        })
        $.ajax(settings)
    },
    handleResponse: function(data, textStatus, jqXHR) {
        App.resourceController.collection.handleResponse(data['collection'])
    }
});

App.updateResourcePath = function() {
    //updates the location to match our current resource controller state
    var url = App.resourceController.collection.get('href')
    var base_url = App.resourceController.get('apiUrl')
    if (url.indexOf(base_url) == 0) {
        url = url.substr(base_url.length)
    }
    App.router.location.setURL(url)
}

//when href changes, call our observer function to update the path
App.resourceController.collection.addObserver('href', App, 'updateResourcePath')

App.Router = Em.Router.extend({
  location: 'hash',
  root: Em.Route.extend({
    index: Em.Route.extend({
      route: '/',
      connectOutlets: function(router) {
        router.get('applicationController').connectOutlet('Resource');
      },
      followLink: function(router, event) {
        var view = event.view
        var url = view.bindingContext.get('url')
        App.resourceController.followLink(url)
      },
      submitForm: function(router, event) {
        var view = event.view
        var form = view.$().find('form');
        App.resourceController.submitForm(form)
      },
      deserialize: function(router, params) {
        //since there are no states, this only gets called once and that is to interpret the initial #url
        //console.log('deserialize', router, params)
        var hash = router.location.location.hash
        var url = App.resourceController.get('apiUrl')
        if (hash) {
            url = url + hash.substr(1);
        }
        //console.log('deserialized', url)
        App.resourceController.followLink(url)
        //location.setURL(path);
        //params = {resource_url: url}
        //return params
      }
    })
  })
});

App.handleResponseError = function(jqXHR, textStatus, errorThrown) {
    if (jqXHR.status == 401) {
        var login_url = jqXHR.getResponseHeader("Location")
        if (login_url) {
            //TODO preserve previous url so we are redirected on login success
            App.resourceController.followLink(login_url)
        } else {
            console.log([jqXHR, textStatus, errorThrown])
        }
    } else {
        console.log([jqXHR, textStatus, errorThrown])
    }
}

App.serializeFormJSON = function(form) {
    //TODO power this by the view context as well as form
    var o = Array();
    form.find(':input').each(function() {
        var $this = $(this)
        if ($this.data('api-skip') || !$this.attr('name')) return;
        var type = $this.data('api-type') || $this.attr('type') || 'text'
        var value = $this.val()
        var name = $this.attr('name')
        o.push({"type": type,
                "value": value,
                "name": name})
    });
    return $.serializeJSON({'data':o});
};

App.requestDefaults = {
    accepts: {
        'json': App.contentType, //custom media type defintion
    },
    success: App.resourceController.handleResponse,
    error: App.handleResponseError,
    dataType: "json",
    beforeSend: function(jqXHR, settings) { //inject csrf token
        jQuery(document).ajaxSend(function(event, xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            function safeMethod(method) {
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }
            
            if (!safeMethod(settings.type) && !settings.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        });
    },
    headers: {
        'Accept-Namespaces':'inline'
    }
}

//emberjs first loads ApplicationView
App.ApplicationView = Em.View.extend({
  templateName: 'main'
});

App.AdminView = Em.View.extend({})

App.ResourceView = App.AdminView.extend({
  templateName: 'resource',
  classNames: ['resource']
})

App.NamespacesView = App.AdminView.extend({
  templateName: 'namespaces',
  classNames: ['namespaces']
})

App.BreadcrumbsView = App.AdminView.extend({
  templateName: 'breadcrumbs',
  classNames: ['breadcrumbs']
})

App.QueriesView = App.AdminView.extend({
  templateName: 'queries',
  classNames: ['queries', 'container']
})

App.ErrorView = App.AdminView.extend({
  templateName: 'error',
  classNames: ['error']
})

App.ItemsView = App.AdminView.extend({
  templateName: 'items',
  classNames: ['items', 'container']
})

App.CrudItemsView = App.ItemsView.extend({
  templateName: 'cruditems'
})

App.ResourceItemsView = App.ItemsView.extend({
  templateName: 'resourceitems'
})

App.TemplateView = App.AdminView.extend({
  templateName: 'template',
  classNames: ['template']
})

App.LinkView = App.AdminView.extend({
  templateName: 'link',
  classNames: ['link']
})

App.ButtonView = App.LinkView.extend({
  templateName: 'button',
})

App.BreadcrumbView = App.LinkView.extend({})

App.FormView = App.AdminView.extend({
  templateName: 'form',
  classNames: ['form'],
  didInsertElement: function() {
    var file_fields = this.$().find('input[type="file"]')
    App.initUploadFile(file_fields)
  }
})

$(function() {
  var url = $('body').attr('data-api-endpoint')
  App.resourceController.set('apiUrl', url)
  App.initialize();
});

