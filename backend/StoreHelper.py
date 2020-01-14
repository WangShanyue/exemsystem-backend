import json
import random


class StoreHelper:
    def __init__(self):
        pass

    def __del__(self):
        pass

    def CreateProList(self):
        obj = {
            'problem_count': 0,
            'id_seed': 1,
            'question_list': []
        }
        return obj

    def AddPro(self, list_to_append, problem, ptype, point, right, wrong1, wrong2, wrong3, lastTime,degree):
        list_to_append['problem_count'] += 1
        obj = {
            'id': list_to_append['id_seed'],
            'problem': problem,
            'type': ptype,
            'right': right,
            'wrong1': wrong1,
            'wrong2': wrong2,
            'wrong3': wrong3,
            'lastTime': lastTime,
            'point': 0,
            'degree': degree
        }
        list_to_append['question_list'].append(obj)
        list_to_append['id_seed'] += 1

    def GetPro(self, list_to_get, id):

        questions = list_to_get['question_list']
        checked = False
        ret = questions[0]
        for i in range(0, list_to_get['problem_count']):
            if (questions[i]['id'] == id):
                ret = questions[i]
                checked = True
                break
        if (checked):
            return ret
        else:
            print('error from StoreHelper GetPro : problem id ' + str(id) + ' does not exist')

    def DelPro(self, list_to_del, id):
        questions = list_to_del['question_list']
        checked = False
        for i in range(0, list_to_del['problem_count']):
            if (questions[i]['id'] == id):
                questions.pop(i)
                checked = True
                break
        if (checked):
            list_to_del['problem_count'] -= 1
        else:
            print('error from PaperHelper DelPro : problem id ' + str(id) + ' does not exist')
