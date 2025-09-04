from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    storage_path = models.CharField(max_length=500, blank=True)

    def save(self, *args, **kwargs):
        if not self.storage_path:
            self.storage_path = f"users/{self.username}/"
        super().save(*args, **kwargs)
