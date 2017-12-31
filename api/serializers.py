#api/serializers.py

from rest_framework import serializers
from .models import User
from .models import Info
from .models import MonthView
from .models import Task
from .models import FriendList
import json
class UserSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ('id','mail','password','name','phoneNumber','image')

class InfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Info
        fields = ('id','user_id','phone_number')

class MonthViewSerializer(serializers.ModelSerializer) :

    class Meta:
        model = MonthView
        fields = ('id','user_id', 'date', 'tasks','task_count')

class TaskSerializer(serializers.ModelSerializer):
    reminders = serializers.SerializerMethodField()

    class Meta:

        model = Task
        fields = ('id','user_id','image','category','title','from_time','to_time','description','reminders','date','complete')
    
    def get_reminders(self,obj):
        return obj.reminders
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields= ('id','image','mail','name','phoneNumber')

class TopTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields=('id','task_title')
