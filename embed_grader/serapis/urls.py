from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from . import views
from . import services


urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^login/$', auth_views.login, {'template_name': 'serapis/login.html'}, name= 'login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
    
    ##Registration and Password related pages
    url(r'^registration/$', views.registration, name='registration'),
    url(r'^password_reset/$', auth_views.password_reset, {'template_name': 'serapis/password_reset_form.html', 'email_template_name': 'serapis/password_reset_email.html'}, name='password_reset'),
    url(r'^password_reset_done/$', auth_views.password_reset_done, {'template_name': 'serapis/password_reset_done.html'}, name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, {'template_name': 'serapis/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^password_reset_complete/$', auth_views.password_reset_complete, {'template_name': 'serapis/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^activate/(?P<key>.+)$', views.activation, name='activation'),
    url(r'^new_activation/(?P<user_id>\d+)/$', views.new_activation, name='new_activation'),
    
    ##Course pages
    url(r'^homepage/$', views.homepage, name='homepage'),
    url(r'^course/(?P<course_id>[0-9]+)/$', views.course, name='course'),
    url(r'^course/(?P<course_id>[0-9]+)/membership/$', views.membership, name='membership'),
    url(r'^create-course/$', views.create_course, name='create-course'),
    url(r'^modify-course/(?P<course_id>[0-9]+)/$', views.modify_course, name='modify-course'),
    url(r'^enroll-course/$', views.enroll_course, name='enroll-course'),
    
    ##Assignment pages
    url(r'^assignment/(?P<assignment_id>[0-9]+)/$', views.assignment, name='assignment'),
    url(r'^create-assignment/(?P<course_id>[0-9]+)/$', views.create_assignment, name='create-assignment'),
    url(r'^modify-assignment/(?P<assignment_id>[0-9]+)/$', views.modify_assignment, name='modify-assignment'),
    url(r'^create-assignment-task/(?P<assignment_id>[0-9]+)/$', views.create_assignment_task, name='create-assignment-task'),
    
    ##Testbed and Hardware pages
    url(r'^testbed-type-list/$', views.testbed_type_list, name='testbed-type-list'),
    url(r'^testbed-type/(?P<testbed_type_id>[0-9]+)/$', views.testbed_type, name='testbed-type'),
    url(r'^create-testbed-type/$', views.create_testbed_type, name='create-testbed-type'),
    url(r'^hardware-type-list/$', views.hardware_type_list, name='hardware-type-list'),
    url(r'^hardware-type/(?P<hardware_type_id>[0-9]+)/$', views.hardware_type, name='hardware-type'),
    url(r'^create-hardware-type/$', views.create_hardware_type, name='create-hardware-type'),
    url(r'^modify-hardware-type/(?P<hardware_type_id>[0-9]+)/$', views.modify_hardware_type, name='modify-hardware-type'),
    
    url(r'^debug-task-grading-status/$', views.debug_task_grading_status, name='debug-task-grading-status'),

    url(r'^tb/summary/$', services.testbed_summary_report, name='tb-summary'),
    url(r'^tb/status/$', services.testbed_status_report, name='tb-status'),
    url(r'^tb/waveform/$', services.testbed_return_output_waveform, name='testbed-return-output-waveform'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
