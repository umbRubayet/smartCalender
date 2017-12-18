#api/serializers.py

from rest_framework import serializers
from .models import User
from .models import Info
from .models import MonthView
from .models import Task
class UserSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ('id','mail','password')

class InfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Info
        fields = ('id','user_id','phone_number')

class MonthViewSerializer(serializers.ModelSerializer) :

    class Meta:
        model = MonthView
        fields = ('id','user_id', 'date', 'tasks','task_count')

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('pk','image')
