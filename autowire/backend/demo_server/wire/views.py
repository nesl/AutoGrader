from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

import json

def index(request):
	template = loader.get_template('wire/index.html')
	return HttpResponse(template.render({}, request))

@csrf_exempt
def configure_device(request):
	print('configure request received')
	if request.body:
		print(json.loads(request.body.decode('utf-8')))
	return JsonResponse({})