# -*- coding: utf-8 -*-

from django.conf import settings
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from backend.models import UserList, Paper
import json
import os

# use this to get request body when json-emulation is not enabled
def post2json(request):
  concat = request.POST
  postBody = request.body
  json_result = json.loads(postBody.decode())
  return json_result

  