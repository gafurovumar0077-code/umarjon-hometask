from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

class EmailConfirm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=8)

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now())
    def __str__(self):
        return self.title
