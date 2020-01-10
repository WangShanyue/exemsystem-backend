# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.conf import settings
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from backend.models import UserList, UserInfo
from backend import global_vars
import json
import os
import xlrd
import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')


def login(request):
  # POST means trying to login
  if request.method == 'POST':
    username = request.POST.get('account')
    password = request.POST.get('password')
    ulist = UserList.objects.all()

    for var in ulist:
      if username == var.username and password == var.password:
        if var.usertype == 'admin':
          infoName = 'admin'
        else:
          infoName = UserInfo.objects.filter(username=var.username).values("name")[0]["name"]
        request.session['login_name'] = username
        request.session.modified = True
        request.session['info_name'] =infoName
        # set pages to jump to by users' types
        if var.usertype == 'student':
          request.session['type'] = 'student'
          status = {'code': 200, 'redirect': 'student.html', 'username': username , 'infoname':infoName }
        elif var.usertype == 'teacher':
          request.session['type'] = 'teacher'
          status = {'code': 200, 'redirect': 'teacher.html', 'username': username,'infoname':infoName  }
        elif var.usertype == 'admin':
          request.session['type'] =  'admin'
          status = {'code': 200, 'redirect': 'admin.html', 'username': username,'infoname':infoName  }
        else:
          status = {'code': 403, 'redirect': 'error.html', 'username': username,'infoname':infoName  }
          del request.session['login_name']
        return HttpResponse(json.dumps(status), content_type="application/json")
    # login failed
    status = {'code': 403, 'redirect': 'error.html' }
    return HttpResponse(json.dumps(status), content_type="application/json")
  
  # GET means getting login status
  elif request.method == 'GET':
    try:
      uname = request.session["login_name"]
      infoName =  request.session["info_name"]
      status = {'code': 200, 'username': uname,'infoname':infoName }
    except Exception:
      status = {'code': 403, 'info': 'not logged in' }
    return HttpResponse(json.dumps(status), content_type="application/json")

  # other types of request are not allowed
  else:
    return HttpResponse("This request is invalid.")


def myinfo(request):
  ret = {'code': 200, 'info': 'your personal info' }
  return HttpResponse(json.dumps(ret), content_type="application/json")


class User:
  def __init__(self, username, password, usertype, infoname):
    self.username = username
    self.password = password
    self.usertype = usertype
    self.infoname = infoname

  def __repr__(self):
    return repr((self.username, self.password, self.usertype,self.infoname))


def get_all_user(request):
  userlist = UserList.objects.all()
  userarr = []
  for var in userlist:
    print(var.username)
    infoName = ""
    if var.usertype == 'admin':
      infoName = 'admin'
    else:
      infoName = UserInfo.objects.filter(username= var.username).values("name")[0]["name"]
    print(infoName)
    userarr.append(User(var.username, var.password, var.usertype,infoName))

  #print (userarr)
  jsonarr = json.dumps(userarr, default=lambda o: o.__dict__, sort_keys=True)
  #print (jsonarr)
  loadarr = json.loads(jsonarr)
  #print (loadarr)
  retdata = {'code': 200, 'userlist': loadarr }
  #print (retdata)
  return HttpResponse(json.dumps(retdata), content_type="application/json")


def if_user_exist(uname):
  #print(uname)
  if UserList.objects.filter(username = uname).count() > 0:
    return True
  else:
    return False


def add_user(request):
  uname = request.POST.get('username')
  print(uname + ' to be add')
  if if_user_exist(uname) == True:
    status = {'code': 403, 'info': uname + ' is already existing' }
    return HttpResponse(json.dumps(status), content_type="application/json")
  database = UserList(username = uname, password = request.POST.get('password'),
    usertype = request.POST.get('usertype'))
  database.save()
  database2 = UserInfo(username = uname,name =  request.POST.get('name'))
  database2.save()
  status = {'code': 200, 'info': uname }
  return HttpResponse(json.dumps(status), content_type="application/json")


def add_user_batch(request):
  #print(request.POST.get('batch_names'))
  addlist = request.POST.get('batch_names').split('\n')
  success_count = 0
  for var in addlist:
    single = var.split()
    print(single[0] + '#' + single[1] + '#' + single[2])
    if if_user_exist(single[0]) == True:
      status = {'code': 403, 'info': single[0] + ' exists already, but ' + str(success_count) + ' succeed' }
      return HttpResponse(json.dumps(status), content_type="application/json")
    if single[2] != 'student' and single[2] != 'teacher':
      status = {'code': 403, 'info': single[0] + ' has an invalid type ' + single[2] + ' ,but ' + str(success_count) + ' succeed' }
      return HttpResponse(json.dumps(status), content_type="application/json")
    db = UserList(username = single[0], password = single[1], usertype = single[2])
    db.save()
    success_count = success_count + 1
  status = {'code': 200, 'info': success_count }
  return HttpResponse(json.dumps(status), content_type="application/json")


def delete_user(request):
  user_to_del = request.POST.get('username')
  print (user_to_del)
  #database = UserList.objects.get(username = user_to_del)
  #database.delete()
  UserList.objects.filter(username = user_to_del).delete()
  UserInfo.objects.filter(username = user_to_del).delete()
  status = {'code': 200, 'info': user_to_del }
  return HttpResponse(json.dumps(status), content_type="application/json")


def logout(request):
  try:
    outname = request.session['login_name']
    del request.session['login_name']
  except Exception:
    status = {'code': 403, 'info': 'not logged in' }
    return HttpResponse(json.dumps(status), content_type="application/json")

  status = {'code': 200, 'info': outname }
  return HttpResponse(json.dumps(status), content_type="application/json")


def upload_userlist(request):
  ret = {'code': 403, 'info': 'denied method ' + request.method }

  if request.method == 'POST':
    # acquire paperid from form
    obj = request.FILES.get('file')

    # acquire file from form
    obj = request.FILES.get('file')
    save_path = os.path.join(settings.BASE_DIR, 'upload.xls')
    #print(save_path)
    f = open(save_path, 'wb')
    for chunk in obj.chunks():
      f.write(chunk)
    f.close()

    # read the xls file and load problems
    x1 = xlrd.open_workbook(save_path)
    sheet1 = x1.sheet_by_name("Sheet1")
    line = 4
    while line <= 50 and line < sheet1.nrows:
      if sheet1.cell_value(line, 0) == "":
        break
      uname = str(sheet1.cell_value(line, 0))
      name = str(sheet1.cell_value(line, 1))
      utype = str(sheet1.cell_value(line, 2))
      passwd = str(sheet1.cell_value(line, 3))
      if utype == '教师':
        utype = 'teacher'
      else:
        utype = 'student'
      if if_user_exist(uname) == True:
        line += 1
        continue
      print(uname + '#' + name + '#' + passwd + '#' + utype)
      new_record1 = UserList(username = uname, password = passwd, usertype = utype)
      new_record1.save()

      new_record2 = UserInfo(username=uname, name = name)
      new_record2.save()
      line += 1
      '''
      problem = str(sheet1.cell_value(line, 0))
      ptype = str(sheet1.cell_value(line, 1))
      if ptype == '主观题':
        ptype = 'zhuguan'
      else:
        ptype = 'keguan'
      point = int(sheet1.cell_value(line, 2))
      right = str(sheet1.cell_value(line, 3))
      wrong1 = str(sheet1.cell_value(line, 4))
      wrong2 = str(sheet1.cell_value(line, 5))
      wrong3 = str(sheet1.cell_value(line, 6))
      ph.AddPro(original_prolist, problem, ptype, point, right, wrong1, wrong2, wrong3)
      paperdb.prolist = json.dumps(original_prolist)
      line += 1
      '''

    #paperdb.save()

    # delete file after used
    os.remove(save_path)
    ret = {'code': 200, 'info': 'ok' }
    pass

  return HttpResponse(json.dumps(ret), content_type="application/json")