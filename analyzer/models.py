from django.db import models
import uuid

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.JSONField()
    image_urls = models.TextField()

    def __str__(self):
        return str(self.id)
