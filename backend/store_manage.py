
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.conf import settings
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.db.models import Q
from backend.models import UserList, Paper, TestRecord, UserInfo,Teststore
import json
import os
import time
from backend.StoreHelper import StoreHelper

from backend import json_helper as jh
import xlrd
import xlwt
import sys




def upload_prolist(request):
    ret = {'code': 403, 'info': 'denied method ' + request.method}
    sh = StoreHelper()

    if request.method == 'POST':
        # acquire subject from form
        subject = request.POST.get('subject')
        obj = request.FILES.get('file')
        paper_db = Teststore.objects.filter(subject=subject)
        if not paper_db.exists():
            database = Teststore(
                            storeid= time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())),
                            subject = subject,
                             prolist=json.dumps(sh.CreateProList()))
            database.save()
        paperdb =  Teststore.objects.get(subject=subject)

        original_prolist = json.loads(paperdb.prolist)
        print("original_prolist"+str(original_prolist))
        # acquire file from form
        obj = request.FILES.get('file')
        save_path = os.path.join(settings.BASE_DIR, 'upload.xls')
        # print(save_path)
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
            # print(sheet1.cell_value(line, 0))
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
            nowtime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            sh.AddPro(original_prolist, problem, ptype, point, right, wrong1, wrong2, wrong3,nowtime)
            paperdb.prolist = json.dumps(original_prolist)
            line += 1
            print(problem)
        paperdb.save()
        '''
    paperdb = Paper.objects.get(pid = subject)
    original_prolist = json.loads(paperdb.prolist)
    ph.AddPro(original_prolist, problem["problem"], problem["ptype"], problem["point"],
     problem["right"], problem["wrong1"], problem["wrong2"], problem["wrong3"])
    paperdb.prolist = json.dumps(original_prolist)
    paperdb.save()
    '''

        # delete file after used
        os.remove(save_path)
        ret = {'code': 200, 'info': 'ok'}
        pass

    return HttpResponse(json.dumps(ret), content_type="application/json")





def store_manage(request):
    postjson = jh.post2json(request)
    action = postjson['action']
    subject = postjson['subject']
    ret = {'code': 404, 'info': 'unknown action ' + action}
    sh = StoreHelper()
    print(action,subject)
    if action == 'search':
        paper_db = Teststore.objects.filter(subject=subject)
        if  paper_db.exists():
            ret = {'code': 200, 'info': 'success' + action, 'storeid': paper_db.values("storeid")[0]['storeid']}
    if action == 'get':
        list = Teststore.objects.filter(subject=subject).values("prolist")[0]
        ret = {'code': 200, 'list': list}
    return HttpResponse(json.dumps(ret), content_type="application/json")


def get_store_detail(request):
    #  print("request is "+request)
    storeid = request.GET.get('storeid')
    # get paper from database
    # TODO(LOW): verify if the specified paper is existing
    ###
    print("subject is " + str(storeid))
    paper = Teststore.objects.filter(storeid=storeid)
    prolist = json.loads(paper[0].prolist)
    subject = paper[0].subject
    for var in  prolist["question_list"]:
       var["inpaper"] = 'false'
    ret = {'code': 200, 'paper': prolist,'subject':subject}
    return HttpResponse(json.dumps(ret), content_type="application/json")