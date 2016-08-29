from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^login/$', auth_views.login, {'template_name': 'serapis/login.html'}, name= 'login'),
    url(r'^registration/$', views.registration, name='registration'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
    url(r'^homepage/$', views.homepage, name='homepage'),
    url(r'^create-course/$', views.create_course, name='create-course'),
    url(r'^enroll-course/$', views.enroll_course, name='enroll-course'),
    url(r'^course/([0-9]+)/$', views.course, name='course'),
    url(r'^modify-course/([0-9]+)/$', views.modify_course, name='modify-course'),
    url(r'^create-assignment/([0-9]+)/$', views.create_assignment, name='create-assignment'),
    url(r'^assignment/([0-9]+)/$', views.assignment, name='assignment'),
    url(r'^modify-assignment/([0-9]+)/$', views.modify_assignment, name='modify-assignment'),
    url(r'^testbed-type-list/$', views.testbed_type_list, name='testbed-type-list'),
    url(r'^testbed-type/([0-9]+)/$', views.testbed_type, name='testbed-type'),
    url(r'^create-testbed-type/$', views.create_testbed_type, name='create-testbed-type'),
    url(r'^hardware-type-list/$', views.hardware_type_list, name='hardware-type-list'),
    url(r'^hardware-type/([0-9]+)/$', views.hardware_type, name='hardware-type'),
    url(r'^create-hardware-type/$', views.create_hardware_type, name='create-hardware-type'),
    url(r'^modify-hardware-type/([0-9]+)$', views.modify_hardware_type, name='modify-hardware-type'),
    url(r'^create-assignment-task/([0-9]+)$', views.create_assignment_task, name='create-assignment-task'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
