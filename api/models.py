from django.db import models
import datetime
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
#/api/models.py
# Create your models here.


class User(models.Model):

    mail = models.CharField(max_length=255, blank=False,unique=True)
    password = models.CharField(max_length=255, blank=False)
    name = models.CharField(max_length=255,blank=True,default=None, null=True)
    image = models.ImageField(upload_to='Image/', default=None, blank=True, null=True)
    phoneNumber = models.CharField(max_length=20,blank=True,default=None,null=True)
    fcm_token = JSONField(default=None,blank=True, null=True) 
    active = models.BooleanField(default=False)
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
    tasks = JSONField(blank=True,null=True,default=None)
    task_count = models.IntegerField(blank=True,null=True,default=None)
    tag_flag = models.BooleanField(default=False)
    all_done = models.BooleanField(default=False)

def reminder_default():
    return {"time":""}

class Task(models.Model):
    date = models.DateField(blank=False, default = datetime.today)
    image = models.CharField(max_length=255, blank=False, default=None)
    category = models.CharField(max_length=255, blank=False, default="event")
    title = models.CharField(max_length=255, blank=False, default="task")
    from_time = models.TimeField(blank=True, null=True,default=None)
    to_time = models.TimeField(blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    reminders = JSONField(default = None, blank=True, null=True)
    user_id = models.IntegerField(default=None)
    complete = models.BooleanField(default=False)
    tagged = JSONField(default=None, blank=True, null=True)
    tag_flag = models.BooleanField(default=False)
    group_tag = JSONField(default=None,blank=True, null=True)

def friend_list_default():
    return [{"id":""}]

class FriendList(models.Model):
    user_id = models.IntegerField(blank=False,default=None)
    friend_list = JSONField("friends",default=friend_list_default, blank=True,null=True)

class ForgotPass(models.Model):
    mail = models.CharField(max_length=255, blank=False,unique=True)
    token = models.CharField(max_length=20,default=None, blank=True,null=True)
    dateTime = models.DateTimeField(default= timezone.now()- timedelta(seconds=1),blank=True)

class Weather(models.Model):
    country = models.CharField(max_length=255, default = None, blank=False, null=True)
    city = models.CharField(max_length=255, default = None, blank=False, null=True)
    last_update = models.DateTimeField(default=None, blank=False,null=True)
    atm = JSONField(default=None, blank=False, null=True)
    astronomy = JSONField(default = None, blank=False, null=True)
    forecast = JSONField(default = None, blank=False, null=True)
    current = models.CharField(max_length=255,default=None,blank=True,null=True)

class Holiday(models.Model):
    country = models.CharField(max_length=255, default=None, blank=False, null=True)
    year = models.IntegerField(max_length=20,default=None, blank=False, null=True)
    holidays = JSONField(default = None, blank=False, null=True)

def group_default():
    return []
class Group(models.Model):
    user_id = models.IntegerField(blank=False,default = None)
    group_name = models.CharField(max_length=255, default = None, blank=True, null=True)
    group_list = JSONField(default=group_default, blank=True, null=True)

class GroupMap(models.Model):
    user_id = models.IntegerField(blank=False,default=None)
    group_id = models.IntegerField(blank=False,default=None)

# event type, task =1, group = 2
class TagMe(models.Model):
    tagged_id = models.IntegerField(blank=False,default=None)
    tagger_id = models.IntegerField(blank=False,default=None)
    event_id = models.IntegerField(blank=False,default=None)
    date = models.DateField(blank=False, default = None) 
    event_type = models.IntegerField(blank=False,default=1)
    action = models.IntegerField(blank=False,default=0)

class Note(models.Model):
    user_id = models.IntegerField(blank=False,default = None)
    title = models.CharField(max_length=255, blank=False, default="note")
    description = models.TextField(blank=True, null=True, default=None)
