from serapis.models import *
import os
import shutil

upload_dir = '/home/prod/AutoGrader/embed_grader/uploaded_files/'


def place_file(tmp_path, folder_name):
    if tmp_path == 'xxxxx':
        return None
    basename = os.path.basename(tmp_path)
    full_path = os.path.join(upload_dir, folder_name, basename)
    try:
        try:
            os.makedirs(os.path.dirname(full_path))
        except:
            pass
        shutil.copyfile(tmp_path, full_path)
    except:
        print('ERROR: Cannot copy %s to %s' % (tmp_path, full_path))
    return full_path

with open('/tmp/assignment.txt') as f:
    for line in f.readlines():
        aid = int(line.split()[0])
        a = Assignment.objects.get(id=aid)
        #
        schema = AssignmentTaskFileSchema()
        schema.assignment_id = a
        schema.field = 'input_waveform'
        schema.save()
        #
        schema = SubmissionFileSchema()
        schema.assignment_id = a
        schema.field = 'dut_binary'
        schema.save()
        #
        schema = TaskGradingStatusFileSchema()
        schema.assignment_id = a
        schema.field = 'dut_serial_output'
        schema.save()
        schema = TaskGradingStatusFileSchema()
        schema.assignment_id = a
        schema.field = 'output_waveform'
        schema.save()

with open('/tmp/assignment_task.txt') as f:
    for line in f.readlines():
        at_id = int(line.split()[0])
        at_test_input = line.split()[1]
        #
        at = AssignmentTask.objects.get(id=at_id)
        a = at.assignment_id
        #
        schema = AssignmentTaskFileSchema.objects.filter(assignment_id=a, field='input_waveform')
        if len(schema) != 1:
            print('ABORT: find more than one schema')
            break
        schema = schema[0]
        atf = AssignmentTaskFile()
        atf.assignment_task_id = at
        atf.file_schema_id = schema
        atf.file = place_file(at_test_input, 'AssignmentTaskFile_file')
        atf.save()

with open('/tmp/submission.txt') as f:
    for line in f.readlines():
        s_id = int(line.split()[0])
        s_file = line.split()[1]
        #
        s = Submission.objects.get(id=s_id)
        a = s.assignment_id
        #
        schema = SubmissionFileSchema.objects.filter(assignment_id=a, field='dut_binary')
        if len(schema) != 1:
            print('ABORT: find more than one schema')
            break
        schema = schema[0]
        sf = SubmissionFile()
        sf.submission_id = s
        sf.file_schema_id = schema
        sf.file = place_file(s_file, 'SubmissionFile_file')
        sf.save()

with open('/tmp/task_grading_status.txt') as f:
    for line in f.readlines():
        tgs_id = int(line.split()[0])
        tgs_DUT_serial_output = line.split()[1]
        tgs_output_file = line.split()[2]
        #
        tgs = TaskGradingStatus.objects.get(id=tgs_id)
        a = tgs.assignment_task_id.assignment_id
        #
        schema = TaskGradingStatusFileSchema.objects.filter(assignment_id=a, field='dut_serial_output')
        if len(schema) != 1:
            print('ABORT: find more than one schema')
            break
        schema = schema[0]
        tgsf = TaskGradingStatusFile()
        tgsf.task_grading_status_id = tgs
        tgsf.file_schema_id = schema
        tgsf.file = place_file(tgs_DUT_serial_output, 'TaskGradingStatusFile_file')
        tgsf.save()
        #
        schema = TaskGradingStatusFileSchema.objects.filter(assignment_id=a, field='output_waveform')
        if len(schema) != 1:
            print('ABORT: find more than one schema')
            break
        schema = schema[0]
        tgsf = TaskGradingStatusFile()
        tgsf.task_grading_status_id = tgs
        tgsf.file_schema_id = schema
        tgsf.file = place_file(tgs_output_file, 'TaskGradingStatusFile_file')
        tgsf.save()


