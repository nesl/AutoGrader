from serapis.models import *


"""
Terminology:
    - schema: objects instantiated by AssignmentTaskFileSchema, SubmissionFileSchema, and
          TaskGradingStatusFileSchema
    - schema list: a list of schema
    - schema file: objects instantiated by AssignmentTaskFile, SubmissionFile, and
          TaskGradingStatusFile
    - schema name: a string representing the name of schema (e.g., AssignmentTaskFileSchema.name)
    - file: native python built-in File
"""


def _get_schema_name(SchemaClass, assignment):
    schema_list = SchemaClass.objects.filter(assignment_id=assignment)
    return [sch.field for sch in schema_list]

def get_assignment_task_file_schema_names(assignment):
    return _get_schema_name(AssignmentTaskFileSchema, assignment)

def get_submission_file_schema_names(assignment):
    return _get_schema_name(SubmissionFileSchema, assignment)
    
def get_task_grading_status_file_schema_names(assignment):
    return _get_schema_name(TaskGradingStatusFileSchema, assignment)


def _get_dict_schema_name_to_schema_files(SchemaClass, assignment, schema_file_list, enforce_check):
    schema_list = SchemaClass.objects.filter(assignment_id=assignment)

    if enforce_check:
        if len(schema_list) != len(schema_file_list):
            raise Exception('Records are not consistent to schema')

    schema_id_2_schema_file = {}
    for schema_file in schema_file_list:
        schema_id[schema_file.file_schema_id.id] = schema_file

    dict_schema_file = {}
    for schema in schema_list:
        dict_schema_file[schema.name] = (schema_id_2_schema_file[schema.id]
                if schema.id in schema_id_2_schema_file else None)
    return dict_schema_file

def get_dict_schema_name_to_assignment_task_schema_files(assignment_task, enforce_check=True):
    """
    Params:
      - enforce_check: True if want to check the existances of all files
    Returns:
      dict_schema_name_2_schema_file: dict of str -> AssignmentTaskFile
    """
    assignment = assignment_task.assignment_id
    schema_file_list = AssignmentTaskFile.objects.filter(assignment_task_id=assignment_task)
    return _get_dict_schema_name_to_schema_files(
            AssignmentTaskFileSchema, assignment, schema_file_list, enforce_check)

def get_dict_schema_name_to_submission_schema_files(submission, enforce_check=True):
    """
    Params:
      - enforce_check: True if want to check the existances of all files
    Returns:
      dict_schema_name_2_schema_file: dict of str -> SubmissionFile
    """
    assignment = submission.assignment_id
    schema_file_list = SubmissionFile.objects.filter(submission_id=submission)
    return _get_dict_schema_name_to_schema_files(
            SubmissionFileSchema, assignment, schema_file_list, enforce_check)

def get_dict_schema_name_to_task_grading_status_schema_files(task_grading_status, enforce_check=True):
    """
    Params:
      - enforce_check: True if want to check the existances of all files
    Returns:
      dict_schema_name_2_schema_file: dict of str -> TaskGradingStatusFile
    """
    assignment = submission.assignment_id
    schema_file_list = TaskGradingStatusFile.objects.filter(
            task_grading_status_id=task_grading_status)
    return _get_dict_schema_name_to_schema_files(
            TaskGradingStatusFileSchema, assignment, schema_file_list, enforce_check)


def _save_dict_schema_name_to_files(
        schema_name_2_schema_files, schema_name_2_files, enforce_check):
    if enforce_check:
        if len(schema_name_2_schema_files) != len(dict_sch_name_2_assignment_task_files):
            raise Exception('Records are not consistent to schema')

    for sch_name in schema_name_2_files:
        if sch_name not in schema_name_2_schema_files:
            raise Exception('Schema name "%s" does not exist' % sch_name)
        cur_schema_file = schema_name_2_schema_files[sch_name]
        cur_schema_file.file = schema_name_2_files[sch_name]
        cur_schema_file.save()

def save_dict_schema_name_to_assignment_task_files(
        assignment_task, dict_sch_name_2_assignment_task_files, enforce_check=True):
    """
    Params:
      - assignment_task: the assignment task which the files associate with
      - dict_sch_name_2_assignment_task_files: a dict of str -> File
      - enforce_check: True if want to check the existances of all files
    """
    schema_name_2_schema_files = get_dict_schema_name_to_assignment_task_schema_files(
            assignment_task, enforce_check)
    return _save_dict_schema_name_to_files(schema_name_2_schema_files,
            dict_sch_name_2_assignment_task_files, enforce_check)

def save_dict_schema_name_to_submission_files(
        submission, dict_sch_name_2_submission_files, enforce_check=True):
    """
    Params:
      - submission: the submission which the files associate with
      - dict_sch_name_2_assignment_task_files: a dict of str -> File
      - enforce_check: True if want to check the existances of all files
    """
    schema_name_2_schema_files = get_dict_schema_name_to_submission_schema_files(
            submission, enforce_check)
    return _save_dict_schema_name_to_files(schema_name_2_schema_files,
            dict_sch_name_2_submission_files, enforce_check)

def save_dict_schema_name_to_task_grading_status_files(
        task_grading_status, dict_sch_name_2_task_grading_status_files, enforce_check=True):
    """
    Params:
      - task_grading_status: the task grading status which the files associate with
      - dict_sch_name_2_assignment_task_files: a dict of str -> File
      - enforce_check: True if want to check the existances of all files
    """
    schema_name_2_schema_files = get_dict_schema_name_to_task_grading_status_schema_files(
            task_grading_status, enforce_check)
    return _save_dict_schema_name_to_files(schema_name_2_schema_files,
            dict_sch_name_2_task_grading_status_files, enforce_check)
