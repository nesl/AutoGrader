from serapis.models import *

def get_assignment_task_file_schema(assignment):
    schema_list = AssignmentTaskFileSchema.objects.filter(assignment_id=assignment)
    return [sch.field for sch in schema_list]


"""
When strict is set to be True, all the corresponding records has to be found
in AssignmentTaskFileSchema.
"""
def get_assignment_task_files(assignment, assignment_task, strict=True):
    schema_list = AssignmentTaskFileSchema.objects.filter(assignment_id=assignment)
    assignment_task_files = {}
    for schema in schema_list:
        file_recs = AssignmentTaskFile.objects.filter(
                assignment_task_id=assignment_task, file_schema_id=schema)
        if len(file_recs) == 1:
            file_rec = file_recs[0]
        else:
            if strict:
                raise Exception('Records are not consistent to schema')
            else:
                file_rec = None
        assignment_task_files[schema.field] = file_rec
    return assignment_task_files


def get_submission_file_schema(assignment):
    schema_list = SubmissionFileSchema.objects.filter(assignment_id=assignment)
    return [sch.field for sch in schema_list]


"""
When strict is set to be True, all the corresponding records has to be found
in SubmissionFileSchema.
"""
def get_submission_files(assignment, submission, strict=True):
    schema_list = SubmissionFileSchema.objects.filter(assignment_id=assignment)
    submission_files = {}
    for schema in schema_list:
        file_recs = SubmissionFile.objects.filter(submission_id=submission, file_schema_id=schema)
        if len(file_recs) == 1:
            file_rec = file_recs[0]
        else:
            if strict:
                raise Exception('Records are not consistent to schema')
            else:
                file_rec = None
        submission_files[schema.field] = file_rec
    return submission_files


def get_task_grading_status_file_schema(assignment):
    schema_list = TaskGradingStatusFileSchema.objects.filter(assignment_id=assignment)
    return [sch.field for sch in schema_list]


"""
When strict is set to be True, all the corresponding records has to be found
in TaskGradingStatusFileSchema.
"""
def get_task_grading_status_files(assignment, task_grading_status, strict=True):
    schema_list = TaskGradingStatusFileSchema.objects.filter(assignment_id=assignment)
    grading_files = {}
    for schema in schema_list:
        file_recs = TaskGradingStatusFile.objects.filter(
                task_grading_status_id=task_grading_status, file_schema_id=schema)
        if len(file_recs) == 1:
            file_rec = file_recs[0]
        else:
            if strict:
                raise Exception('Records are not consistent to schema')
            else:
                file_rec = None
        grading_files[schema.field] = file_rec
    return grading_files
