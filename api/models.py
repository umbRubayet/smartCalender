from django.db import models
import datetime
from datetime import datetime
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
#/api/models.py
# Create your models here.


class User(models.Model):

    mail = models.CharField(max_length=255, blank=False,unique=True)
    password = models.CharField(max_length=255, blank=False)

    def __str__(self):
        return "{}".format(self.mail)

class Info(models.Model):
    user_id = models.IntegerField()
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return "{}".format(self.phone_number)

def tasks_default():
    return {"task_id":"","title":""}

class MonthView(models.Model):
    user_id = models.IntegerField()
    date = models.DateField()
    tasks = JSONField("Tasks",default=tasks_default)
    task_count = models.IntegerField(default=1)
