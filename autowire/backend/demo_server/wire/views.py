from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

import json
import subprocess
import os

WIRE_PATH = './wire/Wire/'
QSF_FILE = './wire/Wire/Wire.qsf'
DOTV_FILE = './wire/Wire/MyWire.v'

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

	dotv_file_text = generate_verilog(source_mapping, dst_vars, src_vars)
	with open(DOTV_FILE, 'w') as dotv_file:
		dotv_file.write(dotv_file_text)

	# Create a script to map the pins
	qsf_file_text = generate_qsf(dst_vars, src_vars)
	with open(QSF_FILE, 'w') as qsf_file:
		qsf_file.write(qsf_file_text)

	# Call the Quartus commands to generate the binary
	orig_cwd = os.getcwd()
	try:
		os.chdir(WIRE_PATH)
		result = subprocess.run('./commands.sh', shell=True, check=True)
	finally:
		os.chdir(orig_cwd)
	
	print(result.stdout)


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

def generate_verilog(source_mapping, dst_vars, src_vars):
	module_line = 'module MyWire('
	dst_args_list = ', '.join([dst_vars[key] for key in dst_vars])
	src_args_list = ', '.join([src_vars[key] for key in src_vars])
	module_line = module_line + ', '.join([dst_args_list, src_args_list]) + ');'

	dst_def_lines = '\r\n'.join(['  output wire ' + value + ';' for value in dst_vars.values()])
	src_def_lines = '\r\n'.join(['  input wire ' + value + ';' for value in src_vars.values()])
	
	assignment_lines = '\r\n'.join(['  assign ' + dst_vars[key] + ' = ' + src_vars[source_mapping[key]] + ';' for key in source_mapping])
	return '\r\n'.join([module_line, dst_def_lines, src_def_lines, assignment_lines, 'endmodule\r\n'])


def generate_qsf(dst_vars, src_vars):
	global_assignment_lines = '''set_global_assignment -name FAMILY "Cyclone IV E"
set_global_assignment -name DEVICE EP4CE10F17C8
set_global_assignment -name TOP_LEVEL_ENTITY MyWire
set_global_assignment -name ORIGINAL_QUARTUS_VERSION 17.1.0
set_global_assignment -name PROJECT_CREATION_TIME_DATE "11:33:41  JANUARY 20, 2018"
set_global_assignment -name LAST_QUARTUS_VERSION "18.0.0 Lite Edition"
set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files
set_global_assignment -name MIN_CORE_JUNCTION_TEMP 0
set_global_assignment -name MAX_CORE_JUNCTION_TEMP 85
set_global_assignment -name ERROR_CHECK_FREQUENCY_DIVISOR 1
set_global_assignment -name PARTITION_NETLIST_TYPE SOURCE -section_id Top
set_global_assignment -name PARTITION_FITTER_PRESERVATION_LEVEL PLACEMENT_AND_ROUTING -section_id Top
set_global_assignment -name PARTITION_COLOR 16764057 -section_id Top
set_global_assignment -name POWER_PRESET_COOLING_SOLUTION "23 MM HEAT SINK WITH 200 LFPM AIRFLOW"
set_global_assignment -name POWER_BOARD_THERMAL_MODEL "NONE (CONSERVATIVE)"
set_global_assignment -name VERILOG_FILE MyWire.v
set_global_assignment -name CDF_FILE output_files/Wire.cdf
set_global_assignment -name OPTIMIZATION_MODE "AGGRESSIVE PERFORMANCE"'''
	
	src_instance_assignment_lines = '\r\n'.join(['set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to ' + value for value in src_vars.values()])
	dst_instance_assignment_lines = '\r\n'.join(['set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to ' + value for value in dst_vars.values()])

	src_location_assignment_lines = '\r\n'.join(['set_location_assignment ' + key + ' -to ' + src_vars[key] for key in src_vars])
	dst_location_assignment_lines = '\r\n'.join(['set_location_assignment ' + key + ' -to ' + dst_vars[key] for key in dst_vars])

	final_line = 'set_instance_assignment -name PARTITION_HIERARCHY root_partition -to | -section_id Top'

	return '\r\n'.join([global_assignment_lines, src_instance_assignment_lines, dst_instance_assignment_lines, src_location_assignment_lines, dst_location_assignment_lines, final_line])