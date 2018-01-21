#api/serializers.py

from rest_framework import serializers
from .models import User
from .models import Info
from .models import MonthView
from .models import Task
from .models import FriendList
import json
from .models import Weather
from .models import Holiday
from .models import Group
from .models import TagMe
from .models import Note

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
        fields = ('id','user_id', 'date', 'tasks','task_count','tag_flag','all_done')

class TaskSerializer(serializers.ModelSerializer):
    reminders = serializers.SerializerMethodField()

    class Meta:

        model = Task
        fields = ('id','user_id','image','category','title','from_time','to_time','description','reminders','tagged','date','complete','tag_flag','group_tag')

    def get_reminders(self,obj):
        return obj.reminders
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields= ('id','image','mail','name','phoneNumber')

class TopTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields=('id','title','tag_flag')

class TaskSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id','title','date','from_time','tag_flag','complete')

class WeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Weather
        fields = ('city','atm','astronomy','forecast','current')

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ('id','country','year','holidays')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id','user_id','group_name','group_list')

class TagMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagMe
        fields = ('id','tagged_id','tagger_id','task_id')

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ('id','user_id','title','description')

class TaskTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id','date','category','title','from_time')
