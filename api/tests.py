from django.test import TestCase

#api/tests.py
# Create your tests here.

from .models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.core.urlresolvers import reverse



class ModelTestCase(TestCase):



    def setUp(self):
        self.mail = 'a@gmail.com'
        self.password='1234'
        self.user = User(mail=self.mail,password=self.password)



    def test_model_can_create_a_User(self):
        old_count = User.objects.count()
        self.user.save()
        new_count = User.objects.count()
        self.assertNotEqual(old_count,new_count)

class ViewTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user_data = {'mail':'a@gmail.com',password='sdasad'}
        self.response = self.client.post(reverse('create'),self.user_data,format="json")

    def test_api_can_create_a_user(self):
        self.assertEqual(self.response.status_code,status.HTTP_201_CREATED)
