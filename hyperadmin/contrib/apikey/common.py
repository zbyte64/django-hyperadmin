from hyperadmin.contrib.apikey.models import ApiKey

def authenticate(key):
    try:
        entry = ApiKey.objects.get(key=key, active=True)
    except ApiKey.DoesNotExist:
        return None
    return entry.user

