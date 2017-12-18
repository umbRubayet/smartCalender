from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
#serializers-------
from .serializers import UserSerializer
from .serializers import MonthViewSerializer
from .serializers import TaskSerializer
#serializers--------

#models---------
from .models import User
from .models import Info
from .models import MonthView
from .models import Task
#models---------

from rest_framework.response import Response
import json
import requests

# Create your views here.

@api_view (['GET','POST'])
def user_list(request):
    """
    new user create on post method. i.e : signing up
    """
    if request.method == 'GET':
        pass

    elif request.method =='POST':
        serializer = UserSerializer(data=request.data)
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        #print("type"+data_dict['mail'])
        mail = data_dict['mail']
        exists = User.objects.filter(mail=mail).exists()
        if exists:
            response = {"success":"false","data":"","message":"already exists"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save()
            response = {"success":"true","data": serializer.data,"message":"new user created"}
            return Response(response,status=status.HTTP_201_CREATED)
        response = {"success":"false","data":"", "message":"bad request"}
        return Response(response , status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    """
    login method
    """
    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        requested_mail = data_dict['mail']
        requested_password = data_dict['password']
        exists = User.objects.filter(mail = requested_mail).exists()
        print ("mail...."+ str(exists) )
        if exists :
            user = User.objects.get(mail=requested_mail)
            print ("requested-password..."+requested_password+ "user password.." + user.password)
            if requested_password ==  user.password :
                response = {"success":"true","id":user.id,"message":"logged in"}
                return Response(response,status=status.HTTP_200_OK)
            else:
                response = {"success":"false","message":"password didn't match"}
                return Response(response, status = status.HTTP_404_NOT_FOUND)

        else:
            response = {"success":"false","message":"user doesn't exist"}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def month_tasks(request):
    """
    monthview task  count add with default value = 1
    """

    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        requested_user_id = data_dict['user_id']
        requested_date = data_dict['date']
        
        data_dict['tasks'] = data_dict['tasks'][0]
        exists = MonthView.objects.filter(user_id = requested_user_id, date = requested_date).exists()

        if exists :
            """ Update tasks """
            monthView = MonthView.objects.get(user_id=requested_user_id, date = requested_date)
            task_list =[]

            tasks = monthView.tasks
            if monthView.task_count > 2 :
                min_id = monthView.tasks[0]['task_id']

                for i in tasks :
                    if min_id > i['task_id'] :
                        min_id = i['task_id']


                for i in tasks:
                    if i['task_id'] > min_id :
                        task_list.append(i)
            else:
                for i in tasks:
                    task_list.append(i)
            
            task_list.append(data_dict['tasks'])
            monthView.tasks = task_list
            monthView.task_count = monthView.task_count + 1
            monthView.save()
            response = {"success":"true","task_count":monthView.task_count}
            return Response(response , status = status.HTTP_200_OK)
        else:
            """ create new task """
            serializer = MonthViewSerializer(data = request.data)
            if serializer.is_valid():
                serializer.save()
                response = {"success":"true","data": serializer.data,"message":"new month view task saved"}
                return Response(response,status = status.HTTP_201_CREATED)
            response = {"success":"false","data": serializer.data,"message":""}
            return Response(response, data = serializer.data , status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST','GET'])
def tasks(request):
    """ create new task """

    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        user_id = data_dict['user_id']
        date = data_dict['date']
        task_id = data_dict['task_id']
        task_title = data_dict['task_title']

        """ POST task to month view to update internally """
        task_dict = {}
        task_dict['task_id'] = task_id
        task_dict['task_title'] = task_title

        json_data = {}
        json_data['user_id'] = user_id
        json_data['date'] = date
        json_data['tasks'] = [task_dict]

        response = requests.post('http://127.0.0.1:8000/month_tasks/',json = json_data)
        #print("status Code.....  " + int(response.status_code) )

        if response.status_code == 201 :
            response = {"success":"true","message":"month view data created"}
            return Response (response, status = status.HTTP_201_CREATED)
        if response.status_code == 200 :
            return Response ({"success":"edit","message":"updated task count"}, status = status.HTTP_200_OK)
        return Response(status = status.HTTP_400_BAD_REQUEST)

@api_view (['GET','POST'])
def get_month_tasks(request, user_id):
    """ get all tasks for an user from monthView table in specific date range """
    if request.method == 'GET':
        exists = MonthView.objects.filter(user_id = user_id).exists()
        
        if exists : 
            monthViewAllTasks = MonthView.objects.filter(user_id = user_id)
            serializer = MonthViewSerializer(monthViewAllTasks, many=True)
            response = {"success":"true", "data":serializer.data, "message":"all tasks"}
            return Response(response, status = status.HTTP_200_OK)
        else :
            response = {"success":"true", "message":"user doesn't have any task yet", "data":"" }
            return Response (response , status = status.HTTP_200_OK)

        return Response (status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def postTask(request):
    serializer = TaskSerializer(data=request.data)
    image = request.data['file']
    task = Task.objects.create(image=image)
    task.save()
    return Response(status = status.HTTP_200_OK)

