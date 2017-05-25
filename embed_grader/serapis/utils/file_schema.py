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
    schema_list = SchemaClass.objects.filter(assignment_fk=assignment)
    return [sch.field for sch in schema_list]

def get_assignment_task_file_schema_names(assignment):
    return _get_schema_name(AssignmentTaskFileSchema, assignment)

def get_submission_file_schema_names(assignment):
    return _get_schema_name(SubmissionFileSchema, assignment)
    
def get_task_grading_status_file_schema_names(assignment):
    return _get_schema_name(TaskGradingStatusFileSchema, assignment)


def _get_dict_schema_name_to_schema_files(SchemaClass, assignment, schema_file_list, enforce_check):
    schema_list = SchemaClass.objects.filter(assignment_fk=assignment)

    if enforce_check:
        if len(schema_list) != len(schema_file_list):
            raise Exception('Records are not consistent to schema')

    schema_id_2_schema_file = {}
    for schema_file in schema_file_list:
        schema_id_2_schema_file[schema_file.file_schema_fk.id] = schema_file

    dict_schema_file = {}
    for schema in schema_list:
        dict_schema_file[schema.field] = (schema_id_2_schema_file[schema.id]
                if schema.id in schema_id_2_schema_file else None)
    return dict_schema_file

def get_dict_schema_name_to_assignment_task_schema_files(assignment_task, enforce_check=True):
    """
    Params:
      - enforce_check: True if want to check the existances of all files
    Returns:
      dict_schema_name_2_schema_file: dict of str -> AssignmentTaskFile
    """
    assignment = assignment_task.assignment_fk
    schema_file_list = AssignmentTaskFile.objects.filter(assignment_task_fk=assignment_task)
    return _get_dict_schema_name_to_schema_files(
            AssignmentTaskFileSchema, assignment, schema_file_list, enforce_check)

def get_dict_schema_name_to_submission_schema_files(submission, enforce_check=True):
    """
    Params:
      - enforce_check: True if want to check the existances of all files
    Returns:
      dict_schema_name_2_schema_file: dict of str -> SubmissionFile
    """
    assignment = submission.assignment_fk
    schema_file_list = SubmissionFile.objects.filter(submission_fk=submission)
    return _get_dict_schema_name_to_schema_files(
            SubmissionFileSchema, assignment, schema_file_list, enforce_check)

def get_dict_schema_name_to_task_grading_status_schema_files(task_grading_status, enforce_check=True):
    """
    Params:
      - enforce_check: True if want to check the existances of all files
    Returns:
      dict_schema_name_2_schema_file: dict of str -> TaskGradingStatusFile
    """
    assignment = task_grading_status.assignment_task_fk.assignment_fk
    schema_file_list = TaskGradingStatusFile.objects.filter(
            task_grading_status_fk=task_grading_status)
    return _get_dict_schema_name_to_schema_files(
            TaskGradingStatusFileSchema, assignment, schema_file_list, enforce_check)


def create_empty_task_grading_status_schema_files(task_grading_status):
    assignment = task_grading_status.assignment_task_fk.assignment_fk
    schema_list = TaskGradingStatusFileSchema.objects.filter(assignment_fk=assignment)
    for sch in schema_list:
        TaskGradingStatusFile.objects.create(
                task_grading_status_fk=task_grading_status,
                file_schema_fk=sch,
                file=None,
        )


def _save_dict_schema_name_to_files(schema_name_2_schema_files, schema_name_2_files,
        enforce_check, assignment, get_schema_func, obj, create_schema_file_func):

    # all the schema name should be defined in schema list
    for sch_name in schema_name_2_files:
        if sch_name not in schema_name_2_schema_files:
            raise Exception('Schema name "%s" does not exist' % sch_name)

    # if enforce is check, all the schema names should be presented
    if enforce_check:
        if len(schema_name_2_schema_files) != len(schema_name_2_files):
            raise Exception('Records are not consistent to schema')
    
    for sch_name in schema_name_2_schema_files:
        cur_schema_file = schema_name_2_schema_files[sch_name]
        cur_file = schema_name_2_files[sch_name] if sch_name in schema_name_2_files else None
        if cur_schema_file:
            cur_schema_file.file = cur_file
            cur_schema_file.save()
        elif not cur_schema_file and cur_file:
            schema = get_schema_func(assignment, sch_name)
            schema_file = create_schema_file_func(obj, schema, cur_file)

def _create_assignment_task_file(assignment_task, schema, file):
    return AssignmentTaskFile.objects.create(assignment_task_fk=assignment_task,
            file_schema_fk=schema, file=file)

def _create_submission_file(submission, schema, file):
    return SubmissionFile.objects.create(submission_fk=submission,
            file_schema_fk=schema, file=file)

def _create_task_grading_status_file(task_grading_status, schema, file):
    return TaskGradingStatusFile.objects.create(task_grading_status_fk=task_grading_status,
            file_schema_fk=schema, file=file)

def _get_assignment_task_file_schema(assignment, field_name):
    return AssignmentTaskFileSchema.objects.get(assignment_fk=assignment, field=field_name)

def _get_submission_file_schema(assignment, field_name):
    return SubmissionFileSchema.objects.get(assignment_fk=assignment, field=field_name)

def _get_task_grading_status_file_schema(assignment, field_name):
    return TaskGradingStatusFileSchema.objects.get(assignment_fk=assignment, field=field_name)

def save_dict_schema_name_to_assignment_task_files(
        assignment_task, dict_sch_name_2_assignment_task_files, enforce_check=True):
    """
    Params:
      - assignment_task: the assignment task which the files associate with
      - dict_sch_name_2_assignment_task_files: a dict of str -> File
      - enforce_check: True if want to check the existances of all files
    """
    schema_name_2_schema_files = get_dict_schema_name_to_assignment_task_schema_files(
            assignment_task, False)  # the schema file may haven't established
    _save_dict_schema_name_to_files(
            schema_name_2_schema_files=schema_name_2_schema_files,
            schema_name_2_files=dict_sch_name_2_assignment_task_files,
            enforce_check=enforce_check,
            assignment=assignment_task.assignment_fk,
            get_schema_func=_get_assignment_task_file_schema,
            obj=assignment_task,
            create_schema_file_func=_create_assignment_task_file,
    )

def save_dict_schema_name_to_submission_files(
        submission, dict_sch_name_2_submission_files, enforce_check=True):
    """
    Params:
      - submission: the submission which the files associate with
      - dict_sch_name_2_assignment_task_files: a dict of str -> File
      - enforce_check: True if want to check the existances of all files
    """
    schema_name_2_schema_files = get_dict_schema_name_to_submission_schema_files(
            submission, False)  # the schema file may haven't established
    _save_dict_schema_name_to_files(
            schema_name_2_schema_files=schema_name_2_schema_files,
            schema_name_2_files=dict_sch_name_2_submission_files,
            enforce_check=enforce_check,
            assignment=submission.assignment_fk,
            get_schema_func=_get_submission_file_schema,
            obj=submission,
            create_schema_file_func=_create_submission_file,
    )

def save_dict_schema_name_to_task_grading_status_files(
        task_grading_status, dict_sch_name_2_task_grading_status_files, enforce_check=True):
    """
    Params:
      - task_grading_status: the task grading status which the files associate with
      - dict_sch_name_2_assignment_task_files: a dict of str -> File
      - enforce_check: True if want to check the existances of all files
    """
    schema_name_2_schema_files = get_dict_schema_name_to_task_grading_status_schema_files(
            task_grading_status, False)  # the schema file may haven't established
    _save_dict_schema_name_to_files(
            schema_name_2_schema_files=schema_name_2_schema_files,
            schema_name_2_files=dict_sch_name_2_task_grading_status_files,
            enforce_check=enforce_check,
            assignment=task_grading_status.assignment_task_fk.assignment_fk,
            get_schema_func=_get_task_grading_status_file_schema,
            obj=task_grading_status,
            create_schema_file_func=_create_task_grading_status_file,
    )
