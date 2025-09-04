from django.db import models
from accounts.models import User
import uuid
import os


def user_storage_path(instance, filename):
    """
    Генерация пути для сохранения файла:
    users/<username>/<uuid4>.<ext>
    """
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("users", instance.owner.username, filename)


class File(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_storage_path)

    original_name = models.CharField(max_length=255) 
    name = models.CharField(max_length=255)  
    comment = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_downloaded_at = models.DateTimeField(blank=True, null=True)

    size = models.PositiveIntegerField(default=0)

    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, "size"):
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.original_name} ({self.name})"
