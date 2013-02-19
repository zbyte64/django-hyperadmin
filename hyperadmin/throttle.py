import time
from django.core.cache import cache
from django.http import HttpResponse


class BaseThrottle(object):
    def throttle_check(self, api_request, endpoint):
        return None

class Throttle(BaseThrottle):
    def __init__(self, throttle_at=150, timeframe=3600, expiration=None):
        self.throttle_at = throttle_at
        # In seconds, please.
        self.timeframe = timeframe
        
        if expiration is None:
            # Expire in a week.
            expiration = 604800
        
        self.expiration = int(expiration)
    
    def throttle_check(self, api_request, endpoint):
        """
        Returns a link if the request should be throttled
        """
        key = self.get_identifier(api_request, endpoint)
        
        # Make sure something is there.
        cache.add(key, [])
        
        # Weed out anything older than the timeframe.
        minimum_time = int(time.time()) - int(self.timeframe)
        times_accessed = [access for access in cache.get(key) if access >= minimum_time]
        
        if len(times_accessed) >= int(self.throttle_at):
            # Throttle them.
            if hasattr(api_request.site, 'get_throttle_link'):
                return api_request.site.get_throttle_link()
            return HttpResponse(status=429)
        
        times_accessed.append(int(time.time()))
        cache.set(key, times_accessed, self.expiration)
        return None
    
    def get_identifier(self, api_request, endpoint):
        return '%s_%s' % (endpoint.get_url_name(), self.user_id(api_request))
    
    def user_id(self, api_request):
        if api_request.user:
            if hasattr(api_request.user, 'pk'):
                return  api_request.user.pk
            return api_request.user
        return ''

