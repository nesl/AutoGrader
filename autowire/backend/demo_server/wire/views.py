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
		device_data = json.loads(request.body.decode('utf-8'))
		print(device_data)
		program_fpga(device_data)
	return JsonResponse({})

def program_fpga(device_data):
	# Create a Verilog file according to the connections.
	pass

	# Create a script to map the pins
	pass

	# Call the Quartus commands to generate the binary
	pass

	# Program the FPGA
	pass