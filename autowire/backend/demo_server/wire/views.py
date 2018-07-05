from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

import json

QSF_FILE = './Wire/Wire.qsf'
DOTV_FILE = './Wire/Wire.v'

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
	source_mapping, dst_vars, src_vars = parse_data(device_data)
	print(source_mapping)
	print(dst_vars)
	print(src_vars)

	# Create a script to map the pins
	pass

	# Call the Quartus commands to generate the binary
	pass

	# Program the FPGA
	pass

def parse_data(device_data):
	connections = device_data['connections']

	# The key is the destination of the connection, since each input (dst) should only have one source
	source_mapping = {}

	for connection in connections:
		dst_pin = connection['to']['fpga_pin']
		src_pin = connection['from']['fpga_pin']

		if dst_pin in source_mapping:
			raise Exception('An input pin has multiple sources')
		else:
			source_mapping[dst_pin] = src_pin

	# Assign a variable name to each of the pins
	dsts = source_mapping.keys()
	srcs = source_mapping.values()

	dst_vars = {key: 'dst_' + str(num) for num, key in enumerate(dsts)}
	src_vars = {key: 'src_' + str(num) for num, key in enumerate(srcs)}

	return source_mapping, dst_vars, src_vars