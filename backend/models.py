# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class UserList(models.Model):
  username = models.CharField(max_length = 20, unique = True)
  password = models.CharField(max_length = 20)
  usertype = models.CharField(max_length = 20)

class UserInfo(models.Model):
  username =  models.CharField(max_length = 20, unique = True)
  name = models.CharField(max_length = 50)

class Paper(models.Model):
  pid = models.CharField(max_length = 20)
  pname = models.CharField(max_length = 20)
  teaname = models.CharField(max_length = 20)
  stulist = models.CharField(max_length = 10240)
  prolist = models.CharField(max_length = 102400)
  penabled = models.CharField(max_length = 20)

class TestRecord(models.Model):
  paperid = models.CharField(max_length = 20)
  stuid = models.CharField(max_length = 20)
  submit_time = models.CharField(max_length = 20)
  answers = models.CharField(max_length = 102400)
  keguan_grade = models.IntegerField()
  keguan_detail = models.CharField(max_length = 102400)
  zhuguan_grade = models.IntegerField()
  zhuguan_detail = models.CharField(max_length = 102400)
  total_score = models.IntegerField()
  confirmed = models.CharField(max_length = 20)

class Teststore(models.Model):
  storeid = models.CharField(max_length = 20, unique = True,primary_key=True)
  subject = models.CharField(max_length = 200)
  prolist = models.CharField(max_length = 1024000)