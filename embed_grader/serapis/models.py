from django.db import models
from django.contrib.auth.models import User, Group

from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from django.utils import timezone
import datetime

from ckeditor_uploader.fields import RichTextUploadingField

from django.core.validators import MinValueValidator

class UserProfile(models.Model):
    #Connect to built-in User model, which already has firstname, lastname, email and password
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    uid = models.CharField(max_length=20, unique=True, verbose_name="University ID")

    #for activation of user. One time use
    activation_key = models.CharField(max_length=40, null=True, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


#Common model for both DUT and Hardware Engines
class HardwareType(models.Model):
    HARDWARE_ENGINE = 0
    DEVICE_UNDER_TEST = 1
    HARDWARE_ROLES = (
        (HARDWARE_ENGINE, 'Hardware Engine'),
        (DEVICE_UNDER_TEST, 'Device Under Test'),
    )
    name = models.CharField(max_length=50, unique=True)
    pinout = models.FileField(upload_to='HardwareType_pinout')
    link_to_manual = models.URLField(null=True)
    hardware_role = models.IntegerField(choices=HARDWARE_ROLES)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ('view_hardware_type', 'View hardware type'),
        )


class HardwareTypePin(models.Model):
    hardware_type = models.ForeignKey(HardwareType, on_delete=models.CASCADE)
    pin_name = models.CharField(max_length=10)

    def __str__(self):
        return self.hardware_type.name + ": "+self.pin_name


# Model that encapsulates the entire Testbed, including the Hardware Engines and DUTs
class TestbedType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# Model that links the TestbedType to it's list of hardware types
class TestbedHardwareList(models.Model):
    testbed_type = models.ForeignKey(TestbedType, on_delete=models.CASCADE)
    hardware_type = models.ForeignKey(HardwareType, on_delete=models.CASCADE)
    hardware_index = models.IntegerField()
    firmware = models.FileField(null=True, blank=True, upload_to='TestbedHardwareList_firmware')

    def __str__(self):
        return '%s, %s, %d' % (self.testbed_type.name, self.hardware_type.name, self.hardware_index)


# Wiring for the TestbedType
class TestbedTypeWiring(models.Model):
    testbed_type = models.ForeignKey(TestbedType, on_delete = models.CASCADE)
    #The device index should match the index in TestbedHardwareList model
    dev_1_index = models.IntegerField()
    dev_1_pin = models.ForeignKey(HardwareTypePin, related_name='dev_1_pin', on_delete=models.CASCADE)
    #The device index should match the index in TestbedHardwareList model
    dev_2_index = models.IntegerField()
    dev_2_pin = models.ForeignKey(HardwareTypePin, related_name='dev_2_pin', on_delete=models.CASCADE)


class Course(models.Model):
    FALL = 0
    WINTER = 1
    SPRING = 2
    SUMMER = 3
    QUARTER_TYPES = (
        (FALL, 'Fall'),
        (WINTER, 'Winter'),
        (SPRING, 'Spring'),
        (SUMMER, 'Summer'),
    )

    # Django does not support years field by default. So this is a hack to get a list of valid years.
    YEAR_CHOICES = []
    for r in range(2015, (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append((r,r))

    course_code = models.CharField(max_length = 10, default = '')
    name = models.CharField(max_length=100, default='')
    description = models.TextField(default='', null=True, blank=True)
    quarter = models.IntegerField(choices=QUARTER_TYPES, default=FALL)
    year = models.IntegerField(choices=YEAR_CHOICES, default=datetime.datetime.now().year)

    def __str__(self):
        return '%s: %s %s %d' % (self.course_code, self.name, self.get_quarter_display(), self.year)

    class Meta:
        permissions = (
            ('view_course', 'View course'),
            ('modify_course', 'Modify course'),
            ('create_course', 'Create course'),
            ('view_membership', 'View membership'),
            ('create_assignment', 'Create assignment'),
            ('view_assignment', 'View assignment'),
            ('modify_assignment', 'Modify assignment'),

        )

ROLE_SUPER_USER = 0
ROLE_INSTRUCTOR = 10
ROLE_TA = 11
ROLE_GRADER = 12
ROLE_STUDENT = 20

class CourseUserList(models.Model):
    USER_ROLES = (
            (ROLE_SUPER_USER, 'Super user'),
            (ROLE_INSTRUCTOR, 'Instructor'),
            (ROLE_TA, 'TA'),
            (ROLE_GRADER, 'Grader'),
            (ROLE_STUDENT, 'Student'),
    )

    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    #TODO: try not give a default value especially it's permission related
    role = models.IntegerField(choices=USER_ROLES, default=ROLE_STUDENT)

    def __str__(self):
        return '%s, %s' % (self.course_id.name, self.user_id)


class Assignment(models.Model):
    # basic information
    course_id = models.ForeignKey(Course, on_delete = models.CASCADE)
    name = models.CharField(max_length=50)
    release_time = models.DateTimeField()
    deadline = models.DateTimeField()
    problem_statement = RichTextUploadingField()

    # testbed related
    testbed_type_id = models.ForeignKey(TestbedType, on_delete=models.CASCADE, default=None, null=True)
    # Testbenches are reserved using AssignmentTestBenches table
    num_testbeds = models.IntegerField(default=None, null=True)

    assignent_task_file_schema = models.CharField(default=None, null=True, max_length=500, help_text="Use ; to separate multiple schema names.")
    task_grading_schema = models.CharField(default=None, null=True, max_length=500, help_text="Use ; to separate multiple schema names.")
    submission_file_schema = models.CharField(default=None, null=True, max_length=500, help_text="Use ; to separate multiple schema names.")

    def __str__(self):
        return self.name

    VIEWING_SCOPE_NO = 0  # nothing can be seen
    VIEWING_SCOPE_PARTIAL = 1  # problem statement, public & feedback cases
    VIEWING_SCOPE_FULL = 2  # problem statement, all cases
    def viewing_scope_by_user(self, user):
        # who can create the assignment (i.e., instructor) can see the test input
        if user.has_perm('create_assignment', self.course_id):
            return Assignment.VIEWING_SCOPE_FULL

        # students cannot see test input if homework is not released yet
        now = timezone.now()
        if now < self.release_time:
            return Assignment.VIEWING_SCOPE_NO

        # students can see everything after deadline
        if now >= self.deadline:
            return Assignment.VIEWING_SCOPE_FULL

        # during the homework session (before deadline), students can only see some cases
        return VIEWING_SCOPE_PARTIAL

    def is_released(self):
        return timezone.now() > self.release_time

    def is_deadline_passed(self):
        return timezone.now() >= self.deadline


class AssignmentTask(models.Model):
    MODE_PUBLIC = 0
    MODE_FEEDBACK = 1
    MODE_HIDDEN = 2
    EVAL_MODES = (
        (MODE_PUBLIC, 'Public'),
        (MODE_FEEDBACK, 'Feedback'),
        (MODE_HIDDEN, 'Hidden'),
    )

    assignment_id = models.ForeignKey(Assignment, on_delete = models.CASCADE)
    brief_description = models.CharField(max_length=100, null=True, blank=True)
    mode = models.IntegerField(choices=EVAL_MODES)
    points = models.FloatField(validators=[MinValueValidator(0.0)])
    description = models.TextField(null=True, blank=True)

    execution_duration = models.FloatField(validators=[MinValueValidator(0.0)])
    #TODO: try to find a way that skip the file not selected check when the file is already in
    #      the database
    #      (http://stackoverflow.com/questions/42063074/how-should-i-allow-a-filefield-not-need-to-upload-a-new-file-when-the-existed-in)
    grading_script = models.FileField(upload_to='AssignmentTask_grading_script')

    def __str__(self):
        return self.brief_description

    def can_access_test_input_by_user(self, user):
        viewing_scope = self.assignment_id.viewing_scope_by_user(user)
        if viewing_scope == Assignment.VIEWING_SCOPE_NO:
            return False
        elif viewing_scope == Assignment.VIEWING_SCOPE_FULL:
            return True
        else:
            if self.mode == MODE_HIDDEN:
                return False
            return True

    def can_access_grading_script_by_user(self, user):
        return user.has_perm('create_assignment', self.assignment_id.course_id)


class AssignmentTaskFileSchema(models.Model):
    class Meta:
        unique_together = ('assignment_id', 'field')

    assignment_id = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    field = models.CharField(max_length=100)


class AssignmentTaskFile(models.Model):
    class Meta:
        unique_together = ('assignment_task_id', 'file_schema_id')

    assignment_task_id = models.ForeignKey(AssignmentTask, on_delete=models.CASCADE)
    file_schema_id = models.ForeignKey(AssignmentTaskFileSchema, on_delete=models.CASCADE)
    file = models.FileField(upload_to='AssignmentTaskFile_file')


class Submission(models.Model):
    STAT_RECEIVED = 0
    STAT_GRADING = 10
    STAT_REGRADING = 11
    STAT_GRADED = 20
    SUBMISSION_STATES = (
            (STAT_RECEIVED, "Received"),
            (STAT_GRADING, "Grading"),
            (STAT_REGRADING, "Rejudging"),
            (STAT_GRADED, "Result is ready"),
    )

    student_id = models.ForeignKey(User, on_delete=models.CASCADE)
    assignment_id = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    submission_time = models.DateTimeField()
    grading_result = models.FloatField()
    status = models.IntegerField(choices = SUBMISSION_STATES, default=STAT_RECEIVED)

    def __str__(self):
        return self.student_id.first_name + " " + self.student_id.last_name + ", " + str(self.id)

    def can_access_file_by_user(self, user):
        return (user.has_perm('modify_assignment', self.assignment_id.course_id)
                or user == self.student_id)

    def retrieve_task_grading_status_and_score_sum(self, include_hidden):
        """
        Paremeter:
          - include_hidden: boolean, set true if to include task grading status of hidden test
                cases.
        Return:
          (task_grading_status_list, sum_student_score, sum_total_score)
        """
        task_grading_status_list = TaskGradingStatus.objects.filter(
                submission_id=self).order_by('assignment_task_id')
        if not include_hidden:
            task_grading_status_list = [t for t in task_grading_status_list
                    if t.assignment_task_id.mode != ASSIGNMENT_TASK_HIDDEN]

        sum_student_score = 0.
        sum_total_score = 0.
        for grading_status in task_grading_status_list:
            if grading_status.grading_status != TaskGradingStatus.STAT_FINISH:
                grading_status.points = 0.
            sum_total_score += grading_status.assignment_task_id.points
            sum_student_score += grading_status.points
        return (task_grading_status_list, sum_student_score, sum_total_score)


class SubmissionFileSchema(models.Model):
    class Meta:
        unique_together = ('assignment_id', 'field')

    assignment_id = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    field = models.CharField(max_length=100)


class SubmissionFile(models.Model):
    class Meta:
        unique_together = ('submission_id', 'file_schema_id')

    submission_id = models.ForeignKey(Submission, on_delete=models.CASCADE)
    file_schema_id = models.ForeignKey(SubmissionFileSchema, on_delete=models.CASCADE)
    file = models.FileField(upload_to='SubmissionFile_file')


class TaskGradingStatus(models.Model):
    class Meta:
        unique_together = ('submission_id', 'assignment_task_id')

    STAT_PENDING = 0
    STAT_EXECUTING = 10
    STAT_OUTPUT_TO_BE_CHECKED = 100
    STAT_FINISH = 110
    STAT_INTERNAL_ERROR = -1
    STAT_SKIPPED = -2

    EXEC_UNKNOWN = -1
    EXEC_OK = 0
    EXEC_SEG_FAULT = 1

    GRADING_STATES = (
            (STAT_PENDING, 'Pending'),
            (STAT_EXECUTING, 'Executing'),
            (STAT_OUTPUT_TO_BE_CHECKED, 'Checking output'),
            (STAT_FINISH, 'Finished'),
            (STAT_INTERNAL_ERROR, 'Please contact PI'),
            (STAT_SKIPPED, 'Skipped'),
    )
    EXECUTION_STATUS = (
            (EXEC_UNKNOWN, 'Haven\'t executed yet'),
            (EXEC_OK, 'Successful execution'),
            (EXEC_SEG_FAULT, 'Segmentation fault'),
    )

    submission_id = models.ForeignKey(Submission, on_delete=models.CASCADE)
    assignment_task_id = models.ForeignKey(AssignmentTask, on_delete=models.CASCADE)
    grading_status = models.IntegerField(choices=GRADING_STATES, default=STAT_PENDING)
    execution_status = models.IntegerField(choices=EXECUTION_STATUS, default=EXECUTION_STATUS)
    status_update_time = models.DateTimeField()

    points = models.FloatField(default=0.0)
    grading_detail = models.FileField(upload_to='TaskGradingStatus_grading_detail',
            null=True, blank=True)

    def can_access_output_file_by_user(self, user):
        # If the user is an instructor, she can see the output file
        if user.has_perm('create_assignment', self.assignment_task_id.assignment_id.course_id):
            return True

        # Otherwise, the user is a student. We need to make sure the user is the owner
        # of this output file
        if user != self.submission_id.student_id:
            return False

        # Now, is the output ready to download? Depends on the mode of the task.
        # Fortunately, the accessibility of an input file and an output file within the
        # same task should be the same. We can simply ask the permission of the input file.
        return self.assignment_task_id.can_access_test_input_by_user(user)

    def can_detail_be_viewed_by_user(self, user):
        assignment = self.assignment_task_id.assignment_id
        return assignment.viewing_scope_by_user(user) == Assignment.VIEWING_SCOPE_FULL


class TaskGradingStatusFileSchema(models.Model):
    class Meta:
        unique_together = ('assignment_id', 'field')

    assignment_id = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    field = models.CharField(max_length=100)


class TaskGradingStatusFile(models.Model):
    class Meta:
        unique_together = ('task_grading_status_id', 'file_schema_id')

    task_grading_status_id = models.ForeignKey(TaskGradingStatus, on_delete=models.CASCADE)
    file_schema_id = models.ForeignKey(TaskGradingStatusFileSchema, on_delete=models.CASCADE)
    file = models.FileField(upload_to='TaskGradingStatusFile_file', null=True, blank=True)


class Testbed(models.Model):
    #STATUS_RESERVED = 0
    STATUS_AVAILABLE = 1
    STATUS_BUSY = 2
    STATUS_OFFLINE = -1
    STATUS_UNKNOWN = -2

    TESTBED_STATUS = (
        #(STATUS_RESERVED, 'Reserved'),
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_BUSY, 'Busy'),
        (STATUS_OFFLINE, 'Offline'),
    )
    REPORT_STATUS = (
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_BUSY, 'Busy'),
        (STATUS_UNKNOWN, 'Unknown'),
    )

    testbed_type_id = models.ForeignKey(TestbedType, on_delete=models.CASCADE)

    #IP Address. Only allowing IPv4 as the testers are internal
    #TODO: see whether we should switch back to IPAddressField
    #ip_address = models.GenericIPAddressField(protocol='IPv4')
    ip_address = models.CharField(max_length=25)
    unique_hardware_id = models.CharField(max_length=30, unique=True)
    task_being_graded = models.ForeignKey(TaskGradingStatus, null=True, on_delete=models.SET_NULL)
    grading_deadline = models.DateTimeField()

    # internal
    status = models.IntegerField(choices=TESTBED_STATUS)

    # report message
    report_time = models.DateTimeField()
    report_status = models.IntegerField(choices=REPORT_STATUS)


class HardwareDevice(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete = models.CASCADE,
    )

    testbed = models.ForeignKey(Testbed, on_delete=models.CASCADE)
