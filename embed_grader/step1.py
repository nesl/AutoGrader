from serapis.models import *
import os
import shutil


def pull_file(file_field):
    if not file_field:
        return 'xxxxx'
    path = file_field.path
    basename = os.path.basename(path)
    tmp_name = '/tmp/%s' % basename
    if os.path.exists(tmp_name):
        prefix, ext = os.path.splitext(tmp_name)
        i = 1
        while True:
            new_name = '%s_%d%s' % (prefix, i, ext)
            if not os.path.exists(new_name):
                tmp_name = new_name
                break
            i += 1
    try:
        shutil.copyfile(path, tmp_name)
    except:
        print('Error: cannot copy %s to %s' % (path, tmp_name))
    return tmp_name

with open('/tmp/assignment.txt', 'w') as fo:
    for a in Assignment.objects.all():
        fo.write('%d\n' % a.id)

with open('/tmp/assignment_task.txt', 'w') as fo:
    for at in AssignmentTask.objects.all():
        tmp_test_input = pull_file(at.test_input)
        fo.write('%d %s\n' % (at.id, tmp_test_input))

with open('/tmp/submission.txt', 'w') as fo:
    for s in Submission.objects.all():
        tmp_file = pull_file(s.file)
        fo.write('%d %s\n' % (s.id, tmp_file))

with open('/tmp/task_grading_status.txt', 'w') as fo:
    for t in TaskGradingStatus.objects.all():
        tmp_DUT_serial_output = pull_file(t.DUT_serial_output)
        tmp_output_file = pull_file(t.output_file)
        fo.write('%d %s %s\n' % (t.id, tmp_DUT_serial_output, tmp_output_file))


