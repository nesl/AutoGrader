from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from serapis.views import homepages
from serapis.views import registrations
from serapis.views import courses
from serapis.views import assignments
from serapis.views import tasks
from serapis.views import submissions
from serapis.views import testbeds
from serapis.views import hardware
from . import services
from . import media_controls


urlpatterns = [
    ## Log in / log out
    url(r'^login/$', auth_views.login, {'template_name': 'serapis/login.html'}, name= 'login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),

    ## Homepage related
    url(r'^$', homepages.homepage, name='homepage'),
    url(r'^about/$', homepages.about, name='about'),

    ## Registration and Password related pages
    url(r'^registration/$', registrations.registration, name='registration'),
    url(r'^password_reset/$', auth_views.password_reset, {'template_name': 'serapis/password_reset_form.html', 'email_template_name': 'serapis/password_reset_email.html'}, name='password_reset'),
    url(r'^password_reset_done/$', auth_views.password_reset_done, {'template_name': 'serapis/password_reset_done.html'}, name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, {'template_name': 'serapis/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^password_reset_complete/$', auth_views.password_reset_complete, {'template_name': 'serapis/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^activate/(?P<key>.+)$', registrations.activation, name='activation'),
    url(r'^new_activation/(?P<user_id>\d+)/$', registrations.new_activation, name='new_activation'),

    ## Course pages
    url(r'^course/(?P<course_id>[0-9]+)/$', courses.course, name='course'),
    url(r'^course/(?P<course_id>[0-9]+)/membership/$', courses.membership, name='membership'),
    url(r'^create-course/$', courses.create_course, name='create-course'),
    url(r'^modify-course/(?P<course_id>[0-9]+)/$', courses.modify_course, name='modify-course'),
    url(r'^enroll-course/$', courses.enroll_course, name='enroll-course'),
    url(r'^unenroll-course/(?P<course_id>[0-9]+)/$', courses.unenroll_course, name='unenroll-course'),

    ## Assignment pages
    url(r'^assignment/(?P<assignment_id>[0-9]+)/$', assignments.assignment, name='assignment'),
    url(r'^assignment/(?P<assignment_id>[0-9]+)/(?P<final_grade>.*)/$', assignments.assignment, name='assignment'),
    url(r'^create-assignment/(?P<course_id>[0-9]+)/$', assignments.create_assignment, name='create-assignment'),
    url(r'^modify-assignment/(?P<assignment_id>[0-9]+)/$', assignments.modify_assignment, name='modify-assignment'),
    url(r'^create-assignment-task/(?P<assignment_id>[0-9]+)/$', tasks.create_assignment_task, name='create-assignment-task'),
    url(r'^modify-assignment-task/(?P<task_id>[0-9]+)/$', tasks.modify_assignment_task, name='modify-assignment-task'),

    ## Submissions
    url(r'^submission/(?P<submission_id>[0-9]+)/$', submissions.submission, name='submission'),
    url(r'^submissions_full_log/$', submissions.submissions_full_log, name='submissions_full_log'),
    url(r'^student_submission_full_log/$', submissions.student_submission_full_log, name='student_submission_full_log'),
    url(r'^task-grading-detail/(?P<task_grading_id>[0-9]+)/$', submissions.task_grading_detail, name='task-grading-detail'),
    url(r'^regrade/(?P<assignment_id>[0-9]+)/$', submissions.regrade, name='regrade'),

    ## Testbed and Hardware pages
    url(r'^testbed-type-list/$', testbeds.testbed_type_list, name='testbed-type-list'),
    url(r'^testbed-type/(?P<testbed_type_id>[0-9]+)/$', testbeds.testbed_type, name='testbed-type'),
    url(r'^create-testbed-type/$', testbeds.create_testbed_type, name='create-testbed-type'),
    url(r'^hardware-type-list/$', hardware.hardware_type_list, name='hardware-type-list'),
    url(r'^hardware-type/(?P<hardware_type_id>[0-9]+)/$', hardware.hardware_type, name='hardware-type'),
    url(r'^create-hardware-type/$', hardware.create_hardware_type, name='create-hardware-type'),
    url(r'^modify-hardware-type/(?P<hardware_type_id>[0-9]+)/$', hardware.modify_hardware_type, name='modify-hardware-type'),

    ## Report from testbeds
    url(r'^tb/send-summary/$', services.testbed_show_summary_report, name='tb-show-summary'),
    url(r'^tb/send-status/$', services.testbed_show_status_report, name='tb-show-status'),
    url(r'^tb/send-dut-output/$', services.testbed_return_dut_output, name='testbed-return-dut-output'),

    ## Media access
    url(r'^media/HardwareType_pinout/.*/$', media_controls.hardware_type_pinout, name='media-hardware-type-pinout'),
    url(r'^media/TestbedHardwareList_firmware/.*/$', media_controls.testbed_hardware_list_firmware, name='media-testbed-hardware-list-firmware'),
    url(r'^media/AssignmentTask_grading_script/.*/$', media_controls.assignment_task_grading_script, name='media-assignment-task-grading-script'),
    url(r'^media/TaskGradingStatus_grading_detail/.*/$', media_controls.task_grading_status_grading_detail, name='media-task-grading-status-grading-detail'),
    
    url(r'^media/SubmissionFile_file/.*/$', media_controls.submission_file_file, name='media-submission-file2'),
    url(r'^media/TaskGradingStatusFile_file/.*/$', media_controls.task_grading_status_file_file, name='media-task-grading-status-file'),
    url(r'^media/AssignmentTaskFile_file/.*/$', media_controls.assignment_task_file_file, name='assignment-task-file'),

    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^media/Content_images/.*/$', media_controls.content_images, name='content-images')
]
