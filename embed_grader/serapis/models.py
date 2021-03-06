import datetime

from django.contrib.auth.models import User, Group

from django.db import models
from django.db import IntegrityError
from django.db import transaction

from django.core.validators import MinValueValidator

from django.utils import timezone

from guardian.compat import get_user_model
from guardian.shortcuts import assign_perm

from ckeditor_uploader.fields import RichTextUploadingField


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

    # The value assigned to quarters are based the appearing order in a year
    QUARTER_WINTER = 0
    QUARTER_SPRING = 1
    QUARTER_SUMMER = 2
    QUARTER_FALL = 3
    QUARTER_DICT = {
            QUARTER_WINTER: 'Winter',
            QUARTER_SPRING: 'Spring',
            QUARTER_SUMMER: 'Summer',
            QUARTER_FALL: 'Fall',
    }
    QUARTER_TYPES = (
        (QUARTER_WINTER, QUARTER_DICT[QUARTER_WINTER]),
        (QUARTER_SPRING, QUARTER_DICT[QUARTER_SPRING]),
        (QUARTER_SUMMER, QUARTER_DICT[QUARTER_SUMMER]),
        (QUARTER_FALL, QUARTER_DICT[QUARTER_FALL]),
    )

    course_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    year = models.IntegerField()
    quarter = models.IntegerField(choices=QUARTER_TYPES)

    def __str__(self):
        return '%s: %s %s %d' % (self.course_code, self.name, self.get_quarter_display(), self.year)


class CourseUserList(models.Model):
    class Meta:
        unique_together = ('course_fk', 'user_fk')

    ROLE_SUPER_USER = 0
    ROLE_INSTRUCTOR = 10
    ROLE_TA = 11
    ROLE_GRADER = 12
    ROLE_STUDENT = 20
    USER_ROLES = (
            (ROLE_SUPER_USER, 'Super user'),
            (ROLE_INSTRUCTOR, 'Instructor'),
            (ROLE_TA, 'TA'),
            (ROLE_GRADER, 'Grader'),
            (ROLE_STUDENT, 'Student'),
    )

    course_fk = models.ForeignKey(Course, on_delete=models.CASCADE)
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.IntegerField(choices=USER_ROLES)

    def __str__(self):
        return '%s, %s' % (self.course_fk.name, self.user_fk)


class Assignment(models.Model):
    SUBMISSION_LIMIT_INFINITE = 999999

    # basic information
    course_fk = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    release_time = models.DateTimeField()
    deadline = models.DateTimeField()
    problem_statement = RichTextUploadingField(blank=True)
    max_num_team_members = models.IntegerField()
    max_num_submissions = models.IntegerField(validators=[MinValueValidator(1)])

    # testbed related
    testbed_type_fk = models.ForeignKey(TestbedType, null=True, blank=True)
    num_testbeds = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name

    def retrieve_assignment_tasks_and_score_sum(self, include_hidden):
        """
        Paremeter:
          - include_hidden: boolean, set true if to include hidden test cases.
        Return:
          (assignment_task_list, sum_score)
        """
        assignment_task_list = AssignmentTask.objects.filter(assignment_fk=self).order_by('id')
        if not include_hidden:
            assignment_task_list = [t for t in assignment_task_list
                    if t.mode != AssignmentTask.MODE_HIDDEN]

        sum_score = 0.
        for assignment_task in assignment_task_list:
            sum_score += assignment_task.points
        return (assignment_task_list, sum_score)

    def retrieve_assignment_tasks_by_accumulative_scope(self, most_powerful_mode):
        """
        Paremeter:
          - most_powerful_mode: int, should be one of AssignmentTask.MODE_*.
        Return:
          assignment_task_list
        """
        return AssignmentTask.objects.filter(
                assignment_fk=self, mode__lte=most_powerful_mode).order_by('id')

    def get_assignment_task_total_scores(self):
        """
        Return:
          (total_score_without_hidden, total_score_with_hidden)
        """
        assignment_task_list = AssignmentTask.objects.filter(assignment_fk=self)

        total_score_without_hidden = 0.
        total_score_with_hidden = 0.
        for assignment_task in assignment_task_list:
            if assignment_task.mode != AssignmentTask.MODE_HIDDEN:
                total_score_without_hidden += assignment_task.points
            total_score_with_hidden += assignment_task.points

        return (total_score_without_hidden, total_score_with_hidden)

    VIEWING_SCOPE_NO = 0  # nothing can be seen
    VIEWING_SCOPE_PARTIAL = 1  # problem statement, public & feedback cases
    VIEWING_SCOPE_FULL = 2  # problem statement, all cases
    def viewing_scope_by_user(self, user):
        # who can create the assignment (i.e., instructor) can see the test input
        if user.has_perm('create_assignment', self.course_fk):
            return Assignment.VIEWING_SCOPE_FULL

        # students cannot see test input if homework is not released yet
        now = timezone.now()
        if now < self.release_time or (not user.has_perm('view_assignment', self.course_fk)):
            return Assignment.VIEWING_SCOPE_NO

        # students can see everything after deadline
        if now >= self.deadline:
            return Assignment.VIEWING_SCOPE_FULL

        # during the homework session (before deadline), students can only see some cases
        return Assignment.VIEWING_SCOPE_PARTIAL

    def is_released(self):
        return timezone.now() > self.release_time

    def is_deadline_passed(self):
        return timezone.now() >= self.deadline


class AssignmentTask(models.Model):
    MODE_DEBUG = 0
    MODE_PUBLIC = 1
    MODE_FEEDBACK = 2
    MODE_HIDDEN = 3
    EVAL_MODES = (
        (MODE_DEBUG, 'Debug'),
        (MODE_PUBLIC, 'Public'),
        (MODE_FEEDBACK, 'Feedback'),
        (MODE_HIDDEN, 'Hidden'),
    )

    assignment_fk = models.ForeignKey(Assignment, on_delete = models.CASCADE)
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

    def can_access_grading_details_by_user(self, user):
        """
        The grading details here include input and output files, grading feedback, and scores.
        """
        viewing_scope = self.assignment_fk.viewing_scope_by_user(user)
        if viewing_scope == Assignment.VIEWING_SCOPE_NO:
            return False
        elif viewing_scope == Assignment.VIEWING_SCOPE_FULL:
            return True
        else:
            return self.mode in [self.MODE_PUBLIC, self.MODE_DEBUG]

    def can_access_grading_script_by_user(self, user):
        return user.has_perm('create_assignment', self.assignment_fk.course_fk)

    def retrieve_assignment_task_files_url(self, user):
        assign_task_file_list = self.retrieve_assignment_task_files(user)
        assign_task_file_url_list = [f.file.url for f in assign_task_file_list]
        return assign_task_file_url_list

    def retrieve_assignment_task_files(self, user):
        viewing_scope = self.assignment_fk.viewing_scope_by_user(user)
        assign_task_file_list = AssignmentTaskFile.objects.filter(assignment_task_fk=self.id)

        if viewing_scope == Assignment.VIEWING_SCOPE_NO:
            return []
        elif viewing_scope == Assignment.VIEWING_SCOPE_FULL:
            return assign_task_file_list
        else:
            if self.mode in [self.MODE_DEBUG, self.MODE_PUBLIC]:
                return assign_task_file_list
            else:
                return []

class AssignmentTaskFileSchema(models.Model):
    class Meta:
        unique_together = ('assignment_fk', 'field')

    assignment_fk = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    field = models.CharField(max_length=100)


class AssignmentTaskFile(models.Model):
    class Meta:
        unique_together = ('assignment_task_fk', 'file_schema_fk')

    assignment_task_fk = models.ForeignKey(AssignmentTask, on_delete=models.CASCADE)
    file_schema_fk = models.ForeignKey(AssignmentTaskFileSchema, on_delete=models.CASCADE)
    file = models.FileField(upload_to='AssignmentTaskFile_file')


class Team(models.Model):
    assignment_fk = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    passcode = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.id)


class TeamMember(models.Model):
    class Meta:
        unique_together = ('assignment_fk', 'user_fk')

    assignment_fk = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    team_fk = models.ForeignKey(Team, on_delete=models.CASCADE)
    user_fk = models.ForeignKey(User, on_delete=models.CASCADE)
    is_leader = models.BooleanField()

    def __str__(self):
        return 'team%d-%s' % (self.team_fk.id, self.user_fk)


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

    student_fk = models.ForeignKey(User, on_delete=models.CASCADE)
    team_fk = models.ForeignKey(Team, on_delete=models.CASCADE)
    assignment_fk = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    submission_time = models.DateTimeField()
    grading_result = models.FloatField()
    status = models.IntegerField(choices=SUBMISSION_STATES, default=STAT_RECEIVED)
    task_scope = models.IntegerField()  # enum of AssignmentTask.EVAL_MODES
    num_graded_tasks = models.IntegerField()
    num_total_tasks = models.IntegerField()

    def __str__(self):
        return self.student_fk.first_name + " " + self.student_fk.last_name + ", " + str(self.id)

    def retrieve_task_grading_status_and_score_sum(self, include_hidden):
        """
        Paremeter:
          - include_hidden: boolean, set true if to include task grading status of hidden test
                cases.
        Return:
          (task_grading_status_list, sum_student_score, sum_total_score)
        """
        task_grading_status_list = TaskGradingStatus.objects.filter(
                submission_fk=self).order_by('assignment_task_fk')
        if not include_hidden:
            task_grading_status_list = [t for t in task_grading_status_list
                    if t.assignment_task_fk.mode != AssignmentTask.MODE_HIDDEN]

        sum_student_score = 0.
        sum_total_score = 0.
        for grading_status in task_grading_status_list:
            if grading_status.grading_status != TaskGradingStatus.STAT_FINISH:
                grading_status.points = 0.
            sum_total_score += grading_status.assignment_task_fk.points
            sum_student_score += grading_status.points
        return (task_grading_status_list, sum_student_score, sum_total_score)

    def is_fully_graded(self, include_hidden):
        """
        Paremeter:
          - include_hidden: boolean, set true if to include task grading status of hidden test
                cases.
        Return:
          True if all tasks are graded (task_grading_status shows okay)
        """
        (task_grading_status_list, _, _) = self.retrieve_task_grading_status_and_score_sum(
                include_hidden)
        return all([t.is_grading_done() for t in task_grading_status_list])


class SubmissionFileSchema(models.Model):
    class Meta:
        unique_together = ('assignment_fk', 'field')

    assignment_fk = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    field = models.CharField(max_length=100)


class SubmissionFile(models.Model):
    class Meta:
        unique_together = ('submission_fk', 'file_schema_fk')

    submission_fk = models.ForeignKey(Submission, on_delete=models.CASCADE)
    file_schema_fk = models.ForeignKey(SubmissionFileSchema, on_delete=models.CASCADE)
    file = models.FileField(upload_to='SubmissionFile_file')


class TaskGradingStatus(models.Model):
    class Meta:
        unique_together = ('submission_fk', 'assignment_task_fk')

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

    submission_fk = models.ForeignKey(Submission, on_delete=models.CASCADE)
    assignment_task_fk = models.ForeignKey(AssignmentTask, on_delete=models.CASCADE)
    grading_status = models.IntegerField(choices=GRADING_STATES, default=STAT_PENDING)
    execution_status = models.IntegerField(choices=EXECUTION_STATUS, default=EXECUTION_STATUS)
    status_update_time = models.DateTimeField()

    points = models.FloatField(default=0.0)
    grading_detail = models.FileField(upload_to='TaskGradingStatus_grading_detail',
            null=True, blank=True)

    def is_grading_done(self):
        return self.grading_status in [
                TaskGradingStatus.STAT_FINISH, TaskGradingStatus.STAT_INTERNAL_ERROR]


class TaskGradingStatusFileSchema(models.Model):
    class Meta:
        unique_together = ('assignment_fk', 'field')

    assignment_fk = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    field = models.CharField(max_length=100)


class TaskGradingStatusFile(models.Model):
    class Meta:
        unique_together = ('task_grading_status_fk', 'file_schema_fk')

    task_grading_status_fk = models.ForeignKey(TaskGradingStatus, on_delete=models.CASCADE)
    file_schema_fk = models.ForeignKey(TaskGradingStatusFileSchema, on_delete=models.CASCADE)
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

    testbed_type_fk = models.ForeignKey(TestbedType, on_delete=models.CASCADE)

    #IP Address. Only allowing IPv4 as the testers are internal
    #TODO: see whether we should switch back to IPAddressField
    #ip_address = models.GenericIPAddressField(protocol='IPv4')
    ip_address = models.CharField(max_length=25, unique=True)
    task_being_graded = models.ForeignKey(TaskGradingStatus, null=True, on_delete=models.SET_NULL)
    grading_deadline = models.DateTimeField()

    # internal
    status = models.IntegerField(choices=TESTBED_STATUS)

    # report message
    report_time = models.DateTimeField()
    report_status = models.IntegerField(choices=REPORT_STATUS)

    # status of the foreign testbed
    secret_code = models.CharField(max_length=100)

class HardwareDevice(models.Model):
    hardware_type = models.ForeignKey(
        HardwareType,
        on_delete = models.CASCADE,
    )

    testbed = models.ForeignKey(Testbed, on_delete=models.CASCADE)

class GradingSchedulerFootprint(models.Model):
    pid = models.IntegerField()
    woke_time = models.DateTimeField()
    watchdog_time = models.DateTimeField()

    def get_elapsed_time(self):
        return self.watchdog_time - self.woke_time
