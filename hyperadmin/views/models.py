from django.utils.translation import ugettext as _
from django.views import generic
from django import http

from hyperadmin.models import log_action, DELETION
from hyperadmin.resources.links import Link

from common import ResourceViewMixin

class ModelResourceViewMixin(ResourceViewMixin, generic.edit.ModelFormMixin):
    form_class = None
    model = None
    queryset = None
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request)
    
    def get_items(self, **kwargs):
        return self.get_queryset()
    
    def get_items_forms(self, **kwargs):
        return [self.get_form(instance=item) for item in self.get_items()]
    
    def get_form_class(self, instance=None):
        return generic.edit.ModelFormMixin.get_form_class(self)
    
    def get_form_kwargs(self):
        return {}
    
    def get_form(self, **kwargs):
        form_class = self.get_form_class(instance=kwargs.get('instance', None))
        form = form_class(**kwargs)
        return form
    
    #form_valid & form_invalid should not be used

class ModelListResourceView(ModelResourceViewMixin, generic.CreateView):
    def get_form_class(self, instance=None):
        if instance:
            return self.resource.get_list_form_class()
        return generic.edit.ModelFormMixin.get_form_class(self)
    
    def get_changelist(self):
        if not hasattr(self, '_changelist'):
            self._changelist = self.resource.get_changelist(self.request)
        return self._changelist
    
    def get_queryset(self):
        return self.get_changelist().result_list
    
    def get(self, request, *args, **kwargs):
        return self.resource.generate_response(self)
    
    def post(self, request, *args, **kwargs):
        return self.resource.generate_create_response(self, form_class=self.get_form_class())
    
    def get_templated_queries(self):
        links = super(ModelListResourceView, self).get_templated_queries()
        links += self.get_changelist_links()
        return links
    
    def get_changelist_links(self):
        links = self.get_changelist_sort_links()
        links += self.get_changelist_filter_links()
        links += self.get_pagination_links()
        #links.append(self.get_search_link())
        return links
    
    def get_changelist_sort_links(self):
        links = list()
        changelist = self.get_changelist()
        from django.contrib.admin.templatetags.admin_list import result_headers
        for header in result_headers(changelist):
            if header.get("sortable", False):
                prompt = unicode(header["text"])
                classes = ["sortby"]
                if "url" in header:
                    links.append(Link(url=header["url"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                else:
                    if header["ascending"]:
                        classes.append("ascending")
                    if header["sorted"]:
                        classes.append("sorted")
                    links.append(Link(url=header["url_primary"], prompt=prompt, classes=classes+["primary"], rel="sortby"))
                    links.append(Link(url=header["url_remove"], prompt=prompt, classes=classes+["remove"], rel="sortby"))
                    links.append(Link(url=header["url_toggle"], prompt=prompt, classes=classes+["toggle"], rel="sortby"))
        return links
    
    def get_changelist_filter_links(self):
        links = list()
        changelist = self.get_changelist()
        for spec in changelist.filter_specs:
            choices = spec.choices(changelist)
            for choice in choices:
                classes = ["filter"]
                if choice['selected']:
                    classes.append("selected")
                title = spec.title
                if callable(title):
                    title = title()
                prompt = u"%s: %s" % (title, choice['display'])
                links.append(Link(url=choice['query_string'], prompt=prompt, classes=classes, rel="filter"))
        return links
    
    def get_search_link(self):
        pass
    
    def get_pagination_links(self):
        links = list()
        changelist = self.get_changelist()
        paginator, page_num = changelist.paginator, changelist.page_num
        from django.contrib.admin.templatetags.admin_list import pagination
        from django.contrib.admin.views.main import PAGE_VAR
        ctx = pagination(changelist)
        classes = ["pagination"]
        for page in ctx["page_range"]:
            if page == '.':
                continue
            url = changelist.get_query_string({PAGE_VAR: page})
            links.append(Link(url=url, prompt=u"%s" % page, classes=classes, rel="pagination"))
        if ctx["show_all_url"]:
            links.append(Link(url=ctx["show_all_url"], prompt="show all", classes=classes, rel="pagination"))
        return links
    
    def get_ln_links(self, instance=None):
        form = self.get_form(instance=instance)
        create_link = Link(url=self.request.path,
                           method='POST', #TODO should this be put?
                           form=form,
                           prompt='create',
                           rel='create',)
        return [create_link] + super(ModelListResourceView, self).get_ln_links(instance)

class ModelDetailResourceView(ModelResourceViewMixin, generic.UpdateView):
    #TODO get_form retrieves information from mediatype
    
    def get_items(self, **kwargs):
        if not getattr(self, 'object', None):
            self.object = self.get_object()
        return [self.object]
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.resource.generate_response(self, instance=self.object)
    
    def post(self, request, *args, **kwargs):
        # Workaround browsers not being able to send a DELETE method.
        #if request.POST.get('DELETE', None) == "DELETE":
        #    request.method = 'DELETE'
        #    return self.delete(request, *args, **kwargs)
        self.object = self.get_object()
        return self.resource.generate_update_response(self, instance=self.object, form_class=self.get_form_class())
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.can_delete():
            return http.HttpResponseForbidden(_(u"You may not delete that object"))
        
        with log_action(request.user, self.object, DELETION, request=request):
            self.object.delete()
        
        return self.resource.generate_delete_response(self)
    
    def get_ln_links(self, instance=None):
        links = super(ModelDetailResourceView, self).get_ln_links(instance)
        assert instance
        if instance:
            form = self.get_form(instance=instance)
            update_link = Link(url=self.request.path,
                               method='POST',
                               form=form,
                               prompt='update',
                               rel='update',)
            return [update_link] + links
        return links
    
    def get_outbound_links(self, instance=None):
        links = super(ModelDetailResourceView, self).get_outbound_links(instance=instance)
        if instance is None:
            detail_link = Link(url=self.resource.get_instance_url(self.object), rel='breadcrumb', prompt=unicode(self.object))
            links.append(detail_link)
        return links

class InlineModelMixin(object):
    def get_changelist_links(self):
        return []
    
    def get_parent(self):
        queryset = self.resource.parent_resource.get_queryset(self.request)
        parent = queryset.get(pk=self.kwargs['pk'])
        return parent
    
    def get_queryset(self):
        return self.resource.get_queryset(self.request, instance=self.get_parent())

class InlineModelListResourceView(InlineModelMixin, ModelListResourceView):
    pass

class InlineModelDetailResourceView(InlineModelMixin, ModelDetailResourceView):
    def get_object(self):
        queryset = self.get_queryset()
        return queryset.get(pk=self.kwargs['inline_pk'])


