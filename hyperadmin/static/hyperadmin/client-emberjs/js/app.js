var App = Em.Application.create();

App.handleResponse = function(data, textStatus, jqXHR) {
    var view_cls = App.ResourceView
    var view = view_cls.create(data)
    $('#container').empty()
    view.appendTo('#container')
}

App.handleResponseError = function(jqXHR, textStatus, errorThrown) {
    if (jqXHR.status == 401) {
        var login_url = jqXHR.getResponseHeader("Location")
        if (login_url) {
            App.followLink(login_url)
        } else {
            console.log([jqXHR, textStatus, errorThrown])
        }
    } else {
        console.log([jqXHR, textStatus, errorThrown])
    }
}

App.requestDefaults = {
    accepts: {
        'json': 'application/vnd.Collection.next+JSON',
    },
    success: App.handleResponse,
    error: App.handleResponseError,
    dataType: "json"
}

App.followLink = function(url) {
    var settings = $.extend({}, App.requestDefaults, {url: url})
    $.ajax(settings)
}

App.init_application = function() {
  var url = $('body').attr('data-api-endpoint')
  var settings = $.extend({}, App.requestDefaults, {url: url})
  $.ajax(settings)
}

App.AdminView = Em.View.extend({
    followLink: function(event) {
        console.log([event, this])
        App.followLink($(this).attr('href'))
    },
    submitForm: function(event) {
        var settings = $.extend({}, App.requestDefaults, {
            url: $(this).attr('target'),
            type: $(this).attr('method') || 'POST',
            data: $(this).serialize()
        })
        $.ajax(settings)
    }
})

App.LoadingView = App.AdminView.extend({

});

App.ResourceView = App.AdminView.extend({
  templateName: 'resource'
})

App.BreadcrumbsView = App.AdminView.extend({
  templateName: 'breadcrumbs'
})

App.QueriesView = App.AdminView.extend({
  templateName: 'queries'
})

App.ItemsView = App.AdminView.extend({
  templateName: 'items'
})

App.TemplateView = App.AdminView.extend({
  templateName: 'template'
})

App.LinkView = App.AdminView.extend({
  templateName: 'link'
})

App.BreadcrumbView = App.LinkView.extend({

})

App.FormView = App.AdminView.extend({
  templateName: 'form'
})

