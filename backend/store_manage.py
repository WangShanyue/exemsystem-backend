
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
from backend.PaperHelper import PaperHelper
from backend import json_helper as jh
import xlrd
import  random
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
            print()
            degree = int(sheet1.cell_value(line, 7))
            nowtime = time.strftime('%Y.%m.%d', time.localtime(time.time()))

            sh.AddPro(original_prolist, problem, ptype, point, right, wrong1, wrong2, wrong3,nowtime,degree)
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
    dlist = ['','简单', '中等', '困难']
    for pro in prolist['question_list']:
        pro['degree']=dlist[pro['degree']]
    subject = paper[0].subject
    for var in  prolist["question_list"]:
       var["inpaper"] = 'false'
       var['valid'] = 'true'
    ret = {'code': 200, 'paper': prolist,'subject':subject}
    return HttpResponse(json.dumps(ret), content_type="application/json")


def auto_paper(request):
    postjson = jh.post2json(request)
    storeid = postjson['storeid']
    print("storeid",storeid)

    klist=[0,int(postjson['ks']),int(postjson['km']),int(postjson['kh'])]
    zlist=[0,int(postjson['zs']),int(postjson['zm']),int(postjson['zh'])]
    kpoint = int(postjson['kp'])
    zpoint = int(postjson['zp'])

    print(klist)
    store = Teststore.objects.filter(storeid=storeid)
    prolist = json.loads(store[0].prolist)
    sorted(prolist['question_list'], key=lambda x: x['lastTime'], reverse=False)
    retlist = []
    for pro in prolist['question_list']:
        vol = int(pro['degree'])
        if pro['type'] == 'keguan':
            if klist[vol]>0:
                klist[vol] -=1
                pro['point']  = kpoint
                pro['valid'] = 'true'
                retlist.append(pro.copy())
        else:
            if zlist[vol]>0:
                zlist[vol] -=1
                pro['point'] = zpoint
                pro['valid'] = 'true'
                retlist.append(pro.copy())
    dlist = ['','简单', '中等', '困难']
    sorted(retlist, key=lambda x: x['type'], reverse=False)
    for pro in retlist:
        pro['degree']=dlist[pro['degree']]
    ret = {'code': 200, 'prolist': retlist}

    return HttpResponse(json.dumps(ret), content_type="application/json")


def modify_pro (request):
    postjson = jh.post2json(request)
    storeid = postjson['storeid']
    print("storeid",storeid)
    store = Teststore.objects.filter(storeid=storeid)
    prolist = json.loads(store[0].prolist)

    type = postjson['modify_type']
    degree = postjson['modify_degree']

    truelist = []
    dlist = {'简单':1,'中等':2,'困难':3}
    tlist = {'主观题':'zhuguan','客观题':'keguan'}

    for pro in prolist['question_list']:
        if pro['degree'] == dlist[degree] and pro['type'] == tlist[type] :
            truelist.append(pro.copy())

    ranlist = list(range(0,len(truelist)))
    print(len(truelist))
    random.shuffle(ranlist)
    retlist = [truelist[ranlist[0]],truelist[ranlist[1]],truelist[ranlist[2]]]
    dlist = ['','简单', '中等', '困难']
    for pro in retlist:
        pro['degree']=dlist[pro['degree']]
    ret = {'code': 200, 'prolist': retlist}
    return HttpResponse(json.dumps(ret), content_type="application/json")


def auto_save(request):
    ret = {'code': 403, 'info': 'denied method ' + request.method}
    ph = PaperHelper()

    if request.method == 'POST':
        # acquire paperid from form
        postjson = jh.post2json(request)
        print(postjson)
        paperid = postjson['paperid']
        storeid = postjson['storeid']
        print(paperid)
        paperdb = Paper.objects.get(pid=paperid)
        original_prolist = json.loads(paperdb.prolist)
        prolist = postjson['prolist']



        for pro in prolist:
            if pro['valid'] == 'false':
                continue
            problem = pro['problem']
            ptype = pro['type']
            if ptype == '主观题':
                ptype = 'zhuguan'
            else:
                ptype = 'keguan'
            point = pro['point']
            right = pro['right']
            wrong1 = pro['wrong1']
            wrong2 = pro['wrong2']
            wrong3 = pro['wrong3']
            ph.AddPro(original_prolist, problem, ptype, point, right, wrong1, wrong2, wrong3)
            paperdb.prolist = json.dumps(original_prolist)

        paperdb.save()
        '''
    paperdb = Paper.objects.get(pid = paperid)
    original_prolist = json.loads(paperdb.prolist)
    ph.AddPro(original_prolist, problem["problem"], problem["ptype"], problem["point"],
     problem["right"], problem["wrong1"], problem["wrong2"], problem["wrong3"])
    paperdb.prolist = json.dumps(original_prolist)
    paperdb.save()
    '''

        # delete file after used
        ret = {'code': 200, 'info': 'ok'}
        pass

    return HttpResponse(json.dumps(ret), content_type="application/json")

