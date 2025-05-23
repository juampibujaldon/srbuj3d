from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    role = models.CharField(max_length=50, blank=True, null=True) 

    def __str__(self):
        return self.username