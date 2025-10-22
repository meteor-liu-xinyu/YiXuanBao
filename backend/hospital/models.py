from django.db import models

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=100)
    specialty = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name