class Link(object):
    def __init__(self, url, method='GET', form=None, classes=[], descriptors=None, rel=None, cu_headers=None, cr_headers=None):
        '''
        fields = dictionary of django fields describing the accepted data
        descriptors = dictionary of data describing the link
        
        '''
        self.url = url
        self.method = str(method).upper() #CM
        self.form = form
        self.classes = classes
        self.descriptors = descriptors
        self.rel = rel #CL
        self.cu_headers = cu_headers
        self.cr_headers = cr_headers
    
    def get_link_factor(self):
        if self.method in ('PUT', 'DELETE'):
            return 'LI'
        if self.method == 'POST':
            return 'LN'
        if self.method == 'GET':
            if self.form:
                return 'LT'
            #TODO how do we determine which to return?
            return 'LO'
            return 'LE'
        return 'L?'


