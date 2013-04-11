#from django.core.files import File

from hyperadmin.links import Link

from datatap.datataps import DataTap


class HypermediaFormDataTap(DataTap):
    '''
    A datatap that serializes forms from hypermedia items to primitives
    '''
    def get_domain(self):
        if self.instream is None: #no instream, I guess we write?
            return 'deserialized_form'
        if isinstance(self.instream, (list, tuple)):
            return 'primitive'
        if self.instream.domain == 'primitive':
            return 'deserialized_form'

    def get_primitive_stream(self, instream):
        '''
        Convert forms to primitive objects
        '''
        return self.serialize_forms(instream)

    def serialize_forms(self, item_list):
        serializable_items = list()
        for item in item_list:
            serializable_items.append(self.serialize_form(item))
        return serializable_items

    #CONSIDER this is redundant in mediatype. Should factor this out
    def serialize_form(self, item):
        return self.get_form_instance_values(item)

    def prepare_field_value(self, val):
        #if isinstance(val, File):
        #    if hasattr(val, 'name'):
        #        val = val.name
        #    else:
        #        val = None
        if isinstance(val, Link):
            val = Link.get_absolute_url()
        return val

    def get_form_instance_values(self, form):
        data = dict()
        for name, field in form.fields.iteritems():
            val = form[name].value()
            val = self.prepare_field_value(val)
            data[name] = val
        return data

    def get_deserialized_form_stream(self, instream):
        '''
        Convert primitive objects to deserialized form instances
        '''
        #TODO
        return instream
