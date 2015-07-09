from django.db import models
from django.core.files.storage import FileSystemStorage

fs = FileSystemStorage(location="/home/django/django_project/media")

# Create your models here.
class Picture(models.Model):
    pic = models.ImageField(storage=fs, upload_to="%Y/%m/%d")
