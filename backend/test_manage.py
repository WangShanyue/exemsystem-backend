# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.conf import settings
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.db.models import Q
from backend.models import UserList, Paper, TestRecord, UserInfo, Teststore
import json
import os
import time
from backend.PaperHelper import PaperHelper
from backend.StoreHelper import StoreHelper
from backend import json_helper as jh
import xlrd
import xlwt
import sys


# reload(sys)
# sys.setdefaultencoding('utf-8')

class claPaper:
    def __init__(self, pid, pname, teaname, penabled, stulist, prolist, submitted, infoname):
        self.pid = pid
        self.pname = pname
        self.teaname = teaname
        self.penabled = penabled
        self.stulist = stulist
        self.prolist = prolist
        self.submitted = submitted
        self.infoname = infoname

    def __repr__(self):
        return repr((self.pid, self.pname, self.teaname, self.penabled,
                     self.stulist, self.prolist, self.submitted, self.infoname))


def get_stu_testlist(request):
    ret = {'code': 404, 'info': 'unknown error'}
    ph = PaperHelper()
    stuid = request.session['login_name']
    # get the list of submitted papers
    test_taken = TestRecord.objects.filter(stuid=stuid)
    takenlist = []
    for var in test_taken:
        obj = {
            'pid': var.paperid
        }
        takenlist.append(obj)
        pass
    # take out each test and test if the given student is in which tests
    all_paper = Paper.objects.all()
    retlist = []
    for paper in all_paper:
        # skip the paper if the student had taken the test
        taken_this = False
        for var in takenlist:
            if var['pid'] == paper.pid:
                taken_this = True
            pass
        ###
        sl = json.loads(paper.stulist)
        if ph.ExistStu(sl, stuid) == True and taken_this == False:
            # print("[%s] is in paper [%s]." % (stuid, paper.pid))
            infoname_t = UserInfo.objects.filter(username=paper.teaname).values("name")[0]["name"]
            stucount = json.loads(paper.stulist)['count']
            procount = json.loads(paper.prolist)['problem_count']
            retlist.append(claPaper(paper.pid, paper.pname, paper.teaname, paper.penabled,
                                    str(stucount), str(procount), 'unseen', infoname_t))
    jsonarr = json.dumps(retlist, default=lambda o: o.__dict__, sort_keys=True)
    loadarr = json.loads(jsonarr)
    ret = {'code': 200, 'list': loadarr, 'taken': takenlist}
    ###
    return HttpResponse(json.dumps(ret), content_type="application/json")


def get_history(request):
    stuid = request.session['login_name']
    records = TestRecord.objects.filter(stuid=stuid)
    takenlist = []

    for var in records:
        print(var.paperid)
        paper = Paper.objects.get(pid=var.paperid)
        score = -1
        if var.confirmed == 'yes':
            score = var.total_score

        infoName = UserInfo.objects.filter(username=paper.teaname).values("name")[0]["name"]
        print(infoName)
        print(paper.teaname)
        obj = {
            'pid': var.paperid,
            'pname': paper.pname,
            'teaname': paper.teaname,
            'subtime': var.submit_time,
            'confirmed': var.confirmed,
            'grade': score,
            'infoname': infoName
        }
        takenlist.append(obj)

    ret = {'code': 200, 'list': takenlist}
    return HttpResponse(json.dumps(ret), content_type="application/json")


def get_tea_testlist(request):
    tname = request.session['login_name']
    infoname = request.session['info_name']
    papers = Paper.objects.filter(teaname=tname)  # .all()#
    plist = []
    for var in papers:
        stucount = json.loads(var.stulist)['count']
        procount = json.loads(var.prolist)['problem_count']
        # count the number of whom submitted the answersheet
        subcount = TestRecord.objects.filter(paperid=var.pid).count()
        ###

        plist.append(claPaper(var.pid, var.pname, var.teaname,
                              var.penabled, str(stucount), str(procount), str(subcount), str(infoname)))
    jsonarr = json.dumps(plist, default=lambda o: o.__dict__, sort_keys=True)
    loadarr = json.loads(jsonarr)
    ret = {'code': 200, 'list': loadarr}
    return HttpResponse(json.dumps(ret), content_type="application/json")


# Without the engine, the car would not be  able to run, similarly, without ambition, our dream would be hard to move a single step.

def get_paper_detail(request):
    #  print("request is "+request)
    paperid = request.GET.get('id')
    # get paper from database
    # TODO(LOW): verify if the specified paper is existing
    ###
    print("paperid is " + paperid)
    paper = Paper.objects.filter(pid=paperid)
    prolist = json.loads(paper[0].prolist)
    stulist = json.loads(paper[0].stulist)
    slist = []
    subcount = TestRecord.objects.filter(paperid=paperid).count()

    for var in stulist['stu_list']:
        print(var['stu'])
        infoName = UserInfo.objects.filter(username=var['stu']).values("name")[0]["name"]
        slist.append(infoName)
    stulist["stu_info"] = slist
    infoname_t = UserInfo.objects.filter(username=paper[0].teaname).values("name")[0]["name"]
    strpaper = json.dumps(claPaper(paper[0].pid, paper[0].pname, paper[0].teaname,
                                   paper[0].penabled, str(stulist['count']), str(prolist['problem_count']), subcount,
                                   infoname_t),
                          default=lambda o: o.__dict__, sort_keys=True)
    jsonpaper = json.loads(strpaper)
    ret = {'code': 200, 'info': jsonpaper, 'paper': prolist, 'stulist': stulist}
    return HttpResponse(json.dumps(ret), content_type="application/json")


def manage_paper(request):
    postjson = jh.post2json(request)
    action = postjson['action']
    ret = {'code': 404, 'info': 'unknown action ' + action}
    ph = PaperHelper()

    if action == 'create':
        # TODO(LOW): verify if the specified paper name is used
        ###
        # get paper name and initialize the new paper with a time id
        database = Paper(pid=time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())),
                         pname=postjson['papername'],
                         teaname=request.session['login_name'],
                         penabled='no',
                         stulist=json.dumps(ph.CreateStuList()),
                         prolist=json.dumps(ph.CreateProList()))
        database.save()
        ret = {'code': 200, 'info': 'ok', 'papername': postjson['papername']}

    elif action == 'delete':
        # get the paper id and delete it from database
        Paper.objects.filter(pid=postjson['paperid']).delete()
        TestRecord.objects.filter(paperid=postjson['paperid']).delete()
        ###
        ret = {'code': 200, 'info': 'ok', 'paperid': postjson['paperid']}

    elif action == 'enable':
        # turn the status of paper to yes
        paperdb = Paper.objects.get(pid=postjson['paperid'])
        paperdb.penabled = 'yes'
        paperdb.save()
        ###
        ret = {'code': 200, 'info': 'ok', 'paperid': postjson['paperid']}
    elif action == 'disable':
        # turn the status of paper to no
        paperdb = Paper.objects.get(pid=postjson['paperid'])
        paperdb.penabled = 'no'
        paperdb.save()
        ###
        ret = {'code': 200, 'info': 'ok', 'paperid': postjson['paperid']}

    return HttpResponse(json.dumps(ret), content_type="application/json")


def modify_paper_prolist(request):
    postjson = jh.post2json(request)
    action = postjson['action']
    ret = {'code': 404, 'info': 'unknown action ' + action}
    ph = PaperHelper()
    sh = StoreHelper()

    if action == 'addpro':
        # add problem given in POST packet to paper
        paperid = postjson['paperid']
        problem = postjson['problem']
        # fetch original problem list from database
        paperdb = Paper.objects.get(pid=paperid)
        original_prolist = json.loads(paperdb.prolist)
        ph.AddPro(original_prolist, problem["problem"], problem["ptype"], problem["point"],
                  problem["right"], problem["wrong1"], problem["wrong2"], problem["wrong3"])
        paperdb.prolist = json.dumps(original_prolist)
        paperdb.save()
        ret = {'code': 200, 'info': 'ok'}

    elif action == 'add_from_store':
        # add problem given in POST packet to paper
        paperid = postjson['paperid']
        problem = postjson['problem']
        store = postjson['storeid']
        newpro = postjson['newpro']
        # fetch original problem list from database
        paperdb = Paper.objects.get(pid=paperid)
        storedb = Teststore.objects.get(storeid=store)
        original_prolist = json.loads(paperdb.prolist)
        storeprolist = json.loads(storedb.prolist)
        question = sh.GetPro(storeprolist, problem)
        ph.AddPro(original_prolist, question["problem"], question["type"], newpro["point"],
                  question["right"], question["wrong1"], question["wrong2"], question["wrong3"])
        paperdb.prolist = json.dumps(original_prolist)
        paperdb.save()
        ret = {'code': 200, 'info': 'ok'}

    elif action == 'delpro':
        # delete problem given in POST packet from paper
        paperid = postjson['paperid']
        problem = postjson['problem']
        paperdb = Paper.objects.get(pid=paperid)
        original_prolist = json.loads(paperdb.prolist)
        ph.DelPro(original_prolist, problem)
        paperdb.prolist = json.dumps(original_prolist)
        paperdb.save()
        ret = {'code': 200, 'paper': 'ok'}

    elif action == 'delall':
        paperid = postjson['paperid']
        paperdb = Paper.objects.get(pid=paperid)
        paperdb.prolist = json.dumps(ph.CreateProList())
        paperdb.save()
        ret = {'code': 200, 'paper': 'ok'}

    return HttpResponse(json.dumps(ret), content_type="application/json")


def modify_paper_stulist(request):
    postjson = jh.post2json(request)
    paperid = postjson['paperid']
    action = postjson['action']
    ph = PaperHelper()
    ret = {'code': 404, 'info': 'unknown action' + action}
    # TODO(LOW): verify paperid whether existing
    ###
    print(paperid)
    paperdb = Paper.objects.get(pid=paperid)
    if (action == 'addstu'):
        stulist = postjson['stulist']
        stuarray = stulist.split(';')
        original_stulist = json.loads(paperdb.stulist)
        count = 0
        for var in stuarray:
            # TODO(LOW): verify var(stuid) whether existing
            #
            result = UserList.objects.filter(username=var)
            if not result.exists():
                continue

            if (var == ''):
                continue
            ph.AddStu(original_stulist, var)
            count += 1
        paperdb.stulist = json.dumps(original_stulist)
        paperdb.save()
        ret = {'code': 200, 'info': 'ok', 'count': count}

    elif (action == 'delstu'):
        stu_to_del = postjson['stu_to_del']
        original_stulist = json.loads(paperdb.stulist)
        ph.DelStu(original_stulist, stu_to_del)
        paperdb.stulist = json.dumps(original_stulist)
        paperdb.save()
        ret = {'code': 200, 'info': 'ok', 'deleted': stu_to_del}

    elif (action == 'cleanstu'):
        original_stulist = json.loads(paperdb.stulist)
        gradelist = json.loads(paperdb.stulist)
        count = original_stulist['count']
        empty_list = ph.CreateStuList()
        paperdb.stulist = json.dumps(empty_list)
        paperdb.save()
        ret = {'code': 200, 'info': 'ok', 'count': count}

    return HttpResponse(json.dumps(ret), content_type="application/json")


def result_manage(request):
    ph = PaperHelper()
    ret = {'code': 404, 'info': 'unknown method ' + request.method}
    if request.method == 'GET':
        paperid = request.GET.get('paperid')
        stuid = request.session['login_name']
        db = Paper.objects.get(pid=paperid)
        paper_pro = json.loads(db.prolist)

        db1 = TestRecord.objects.get(paperid=paperid, stuid=stuid)
        stu_res = json.loads(db1.answers)
        zhuguan_grd = json.loads(db1.zhuguan_detail)
        test = ph.Paper2Result(paper_pro, stu_res, zhuguan_grd)
        ###
        subcount = TestRecord.objects.filter(paperid=paperid).count()
        infoname_t = UserInfo.objects.filter(username=db.teaname).values("name")[0]["name"]
        test_info = json.dumps(claPaper(db.pid, db.pname, db.teaname, db.penabled,
                                        'notused', 'notused', str(subcount), infoname_t), default=lambda o: o.__dict__,
                               sort_keys=True)
        test_info = json.loads(test_info)
        # print(test)
        ret = {'code': 200, 'info': 'ok', 'test': test, 'test_info': test_info}
    return HttpResponse(json.dumps(ret), content_type="application/json")


def test_manage(request):
    ph = PaperHelper()
    ret = {'code': 404, 'info': 'unknown method ' + request.method}
    # GET method means getting test problems
    if request.method == 'GET':
        # TODO: send the test generated back to student
        paperid = request.GET.get('paperid')
        db = Paper.objects.get(pid=paperid)
        paper_pro = json.loads(db.prolist)
        test = ph.Paper2Test(paper_pro)
        ###
        subcount = TestRecord.objects.filter(paperid=paperid).count()
        infoname_t = UserInfo.objects.filter(username=db.teaname).values("name")[0]["name"]
        test_info = json.dumps(claPaper(db.pid, db.pname, db.teaname, db.penabled,
                                        'notused', 'notused', str(subcount), infoname_t), default=lambda o: o.__dict__,
                               sort_keys=True)
        test_info = json.loads(test_info)
        # print(test)
        ret = {'code': 200, 'info': 'ok', 'test': test, 'test_info': test_info}

    # POST method means submitting answers
    elif request.method == 'POST':
        postjson = jh.post2json(request)
        # print(postjson)
        # given postjson and get the new json with only answer, id, type, point
        answers = ph.ExtractAnswers(postjson['test'])
        # print(answers)
        answers = json.dumps(answers)
        stuname = request.session['login_name']
        paperid = postjson['paperid']
        if TestRecord.objects.filter(Q(stuid=stuname) & Q(paperid=paperid)).count() > 0:
            ret = {'code': 403, 'info': 'already exists', 'stu': stuname, 'pname': postjson['pname']}
        else:
            db = TestRecord(paperid=paperid,
                            stuid=stuname,
                            submit_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                            answers=answers,
                            keguan_grade=-1,
                            keguan_detail='',
                            zhuguan_grade=-1,
                            zhuguan_detail='',
                            total_score=-1,
                            confirmed='no'
                            )
            db.save()
            ret = {'code': 200, 'info': 'ok', 'stu': stuname, 'pname': postjson['pname']}

    return HttpResponse(json.dumps(ret), content_type="application/json")


class claRecord:
    def __init__(self, paperid, stuid, submit_time, answers, keguan_grade,
                 keguan_detail, zhuguan_grade, zhuguan_detail, total_score, confirmed):
        self.paperid = paperid
        self.stuid = stuid
        self.submit_time = submit_time
        self.answers = answers
        self.keguan_grade = keguan_grade
        self.keguan_detail = keguan_detail
        self.zhuguan_grade = zhuguan_grade
        self.zhuguan_detail = zhuguan_detail
        self.total_score = total_score
        self.confirmed = confirmed

    def __repr__(self):
        return repr((self.paperid, self.stuid, self.submit_time, self.answers, self.keguan_grade,
                     self.keguan_detail, self.zhuguan_grade, self.zhuguan_detail, self.total_score))


def judge_manage(request):
    ret = {'code': 200, 'info': 'ok'}
    postjson = jh.post2json(request)
    action = postjson['action']
    paperid = postjson['paperid']
    ph = PaperHelper()
    if action == 'getans':
        ret = {'code': 200, 'info': 'ok'}
        # build the list of all students' answers
        retlist = []
        illulist = [0, 0, 0, 0, 0]
        db = TestRecord.objects.filter(paperid=paperid)
        for var in db:
            retlist.append(claRecord(var.paperid, var.stuid, var.submit_time, var.answers,
                                     var.keguan_grade, var.keguan_detail, var.zhuguan_grade, var.zhuguan_detail,
                                     var.total_score, var.confirmed))
            print(var.total_score)
            if not var.confirmed == "yes":
                continue
            if (var.total_score < 60):
                illulist[0] += 1
            elif var.total_score >= 90:
                illulist[4] += 1
            else:
                illulist[int((var.total_score - 50) / 10)] += 1
        print(illulist)
        jsonarr = json.dumps(retlist, default=lambda o: o.__dict__, sort_keys=True)
        loadarr = json.loads(jsonarr)
        ret = {'code': 200, 'info': 'ok', 'anslist': loadarr, 'illulist': illulist}
        ###

    elif action == 'delans':
        # delete the specified answer sheet from records
        stuname = postjson['stuname']
        TestRecord.objects.filter(Q(stuid=stuname) & Q(paperid=paperid) & Q(confirmed='no')).delete()
        ret = {'code': 200, 'info': 'ok'}
        ###

    elif action == 'submit':
        records = TestRecord.objects.filter(Q(paperid=paperid) & Q(confirmed='no'))
        for var in records:
            record = TestRecord.objects.get(Q(stuid=var.stuid) & Q(paperid=paperid) & Q(confirmed='no'))
            record.confirmed = 'yes'
            record.total_score = record.keguan_grade + record.zhuguan_grade
            record.save()
            pass
        ret = {'code': 200, 'info': 'ok'}
        pass

    return HttpResponse(json.dumps(ret), content_type="application/json")


def judge_keguan(request):
    postjson = jh.post2json(request)
    action = postjson['action']
    paperid = postjson['paperid']
    ph = PaperHelper()
    ret = {'code': 404, 'info': 'unknown action ' + action}

    if action == 'judge_keguan':
        # take out each submit and compare with normal answer
        # then save the result into the model.
        print("paperId is" + paperid)
        paper = Paper.objects.get(pid=paperid)
        answerlist = TestRecord.objects.filter(Q(paperid=paperid) & Q(confirmed='no'))
        for var in answerlist:
            # print(var.answers)
            score = ph.JudgeKeguan(json.loads(var.answers), json.loads(paper.prolist))
            # print(score)
            record = TestRecord.objects.get(Q(stuid=var.stuid) & Q(paperid=paperid) & Q(confirmed='no'))
            record.keguan_grade = json.dumps(score['score'])
            record.keguan_detail = json.dumps(score['detail'])
            record.save()
            pass
        ret = {'code': 200, 'info': 'ok'}
        ###
        pass

    elif action == 'clean_keguan':
        answerlist = TestRecord.objects.filter(Q(paperid=paperid)
                                               & Q(confirmed='no')).update(keguan_grade=-1, keguan_detail="")
        ret = {'code': 200, 'info': 'ok'}
        pass

    return HttpResponse(json.dumps(ret), content_type="application/json")


def judge_zhuguan(request):
    postjson = jh.post2json(request)
    action = postjson['action']
    paperid = postjson['paperid']
    ph = PaperHelper()
    ret = {'code': 404, 'info': 'unknown action ' + action}

    if action == 'getans':
        stuid = postjson['stuid']
        student = TestRecord.objects.get(Q(stuid=stuid) & Q(paperid=paperid))
        zhuguan = ph.GetZhuguan(json.loads(student.answers))
        judge = {}
        has_judge = 0
        if student.zhuguan_grade != -1:
            judge = student.zhuguan_detail
            judge = json.loads(judge)
            has_judge = 1
        # print(zhuguan)
        ret = {'code': 200, 'count': zhuguan['count'], 'list': zhuguan['zhuguan_list'],
               'has_judge': has_judge, 'judge': judge, 'confirmed': student.confirmed}
        pass

    elif action == 'submit':
        stuid = postjson['stuid']
        record = TestRecord.objects.get(Q(stuid=stuid) & Q(paperid=paperid) & Q(confirmed='no'))
        record.zhuguan_grade = json.dumps(postjson['score'])
        record.zhuguan_detail = json.dumps(postjson['detail'])
        record.save()
        ret = {'code': 200, 'info': 'ok'}
        pass

    elif action == 'clean_zhuguan':
        answerlist = TestRecord.objects.filter(Q(paperid=paperid)
                                               & Q(confirmed='no')).update(zhuguan_grade=-1, zhuguan_detail="")
        ret = {'code': 200, 'info': 'ok'}
        pass

    elif action == 'getpro':
        paper = Paper.objects.get(pid=paperid)
        pro = ph.GetProb(json.loads(paper.prolist)['question_list'], postjson['proid'])
        ret = {'code': 200, 'problem': pro['problem'], 'right': pro['right']}
        pass

    elif action == 'nextid':
        records = TestRecord.objects.filter(Q(paperid=paperid) & Q(zhuguan_grade=-1) & Q(confirmed='no'))
        if records.count() == 0:
            ret = {'code': 201, 'info': 'no next student is found'}
        else:
            ret = {'code': 200, 'nextid': records[0].stuid}
        pass

    return HttpResponse(json.dumps(ret), content_type="application/json")


def upload_prolist(request):
    ret = {'code': 403, 'info': 'denied method ' + request.method}
    ph = PaperHelper()

    if request.method == 'POST':
        # acquire paperid from form
        paperid = request.POST.get('paperid')
        obj = request.FILES.get('file')
        paperdb = Paper.objects.get(pid=paperid)
        original_prolist = json.loads(paperdb.prolist)

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
            ph.AddPro(original_prolist, problem, ptype, point, right, wrong1, wrong2, wrong3)
            paperdb.prolist = json.dumps(original_prolist)
            line += 1

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
        os.remove(save_path)
        ret = {'code': 200, 'info': 'ok'}
        pass

    return HttpResponse(json.dumps(ret), content_type="application/json")


def upload_stulist(request):
    ret = {'code': 403, 'info': 'denied method ' + request.method}
    ph = PaperHelper()
    if request.method == 'POST':
        # acquire paperid from form
        paperid = request.POST.get('paperid')
        obj = request.FILES.get('file')
        print(paperid)
        paperdb = Paper.objects.get(pid=paperid)
        original_stulist = json.loads(paperdb.stulist)

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
            uname = str(sheet1.cell_value(line, 0))
            print(uname)
            if not UserList.objects.filter(username=uname).exists():
                line += 1
                continue
            ph.AddStu(original_stulist, uname)

            line += 1
        paperdb.stulist = json.dumps(original_stulist)
        paperdb.save()

        os.remove(save_path)
        ret = {'code': 200, 'info': 'ok'}
        pass

        return HttpResponse(json.dumps(ret), content_type="application/json")


def paper_export(request):
    postjson = jh.post2json(request)
    paperid = postjson['paperid']
    action = postjson['action']
    ph = PaperHelper()
    ret = {'code': 404, 'info': 'unknown action' + action}
    # TODO(LOW): verify paperid whether existing
    ###
    db = TestRecord.objects.filter(paperid=paperid)

    # 创建一个workbook 设置编码
    workbook = xlwt.Workbook(encoding='utf-8')
    # 创建一个worksheet
    worksheet = workbook.add_sheet('成绩单')
    # 设置宽度和格式
    worksheet.col(0).width = 3200
    worksheet.col(1).width = 3200
    worksheet.col(2).width = 3200
    worksheet.col(3).width = 3200
    alignment = xlwt.Alignment()  # Create Alignment
    alignment.horz = xlwt.Alignment.HORZ_CENTER  # May be: HORZ_GENERAL, HORZ_LEFT, HORZ_CENTER, HORZ_RIGHT, HORZ_FILLED, HORZ_JUSTIFIED, HORZ_CENTER_ACROSS_SEL, HORZ_DISTRIBUTED
    alignment.vert = xlwt.Alignment.VERT_CENTER  # May be: VERT_TOP, VERT_CENTER, VERT_BOTTOM, VERT_JUSTIFIED, VERT_DISTRIBUTED
    style = xlwt.XFStyle()  # Create Style
    style.alignment = alignment  # Add Alignment to Style
    pattern = xlwt.Pattern()  # Create the Pattern
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN  # May be: NO_PATTERN, SOLID_PATTERN, or 0x00 through 0x12
    pattern.pattern_fore_colour = 5  # May be: 8 through 63. 0 = Black, 1 = White, 2 = Red, 3 = Green, 4 = Blue, 5 = Yellow, 6 = Magenta, 7 = Cyan, 16 = Maroon, 17 = Dark Green, 18 = Dark Blue, 19 = Dark Yellow , almost brown), 20 = Dark Magenta, 21 = Teal, 22 = Light Gray, 23 = Dark Gray, the list goes on...

    # 写入excel
    # 参数对应 行, 列, 值
    worksheet.write(0, 0, '学号', style)
    worksheet.write(0, 1, '姓名', style)
    worksheet.write(0, 2, '客观题', style)
    worksheet.write(0, 3, '主观题', style)
    worksheet.write(0, 4, '总分', style)
    max = 0
    min = 1000000
    summary = 0
    row = 1
    for var in db:
        if var.confirmed == "yes":
            infoName = UserInfo.objects.filter(username=var.stuid).values("name")[0]["name"]

            worksheet.write(row, 0, var.stuid, style)
            worksheet.write(row, 1, infoName, style)
            worksheet.write(row, 2, var.keguan_grade, style)
            worksheet.write(row, 3, var.zhuguan_grade, style)
            worksheet.write(row, 4, var.total_score, style)
            row += 1
            summary += var.total_score
            if var.total_score > max:
                max = var.total_score
            if var.total_score < min:
                min = var.total_score

    style.pattern = pattern  # Add Pattern to Style
    worksheet.write(row + 2, 0, '平均分', style)
    worksheet.write(row + 3, 0, '最高分', style)
    worksheet.write(row + 4, 0, '最低分', style)
    worksheet.write(row + 2, 1, summary / (row - 1), style)
    worksheet.write(row + 3, 1, max, style)
    worksheet.write(row + 4, 1, min, style)

    # 保存
    workbook.save('files/试卷成绩单.xls')

    ret = {'code': 200, 'info': 'ok'}
    return HttpResponse(json.dumps(ret), content_type="application/json")
