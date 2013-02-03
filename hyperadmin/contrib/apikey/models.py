from django.db import models
from django.contrib.auth.models import User


class ApiKey(models.Model):
    key = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    
    def __unicode__(self):
        return self.key

