from cloudinary.models import CloudinaryField
from django.db import models


class HeroBanner(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    image = CloudinaryField("hero")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"
