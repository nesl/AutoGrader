from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^login/$', auth_views.login, {'template_name': 'serapis/login.html'}, name= 'login'),
    url(r'^registration/$', views.registration, name='registration'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
    url(r'^homepage/$', views.homepage, name='homepage'),
    url(r'^create-course/$', views.create_course, name='create-course'),
    url(r'^course/([0-9]+)/$', views.course, name='course'),
    url(r'^create-assignment/([0-9]+)/$', views.create_assignment, name='create-assignment'),
    url(r'^assignment/([0-9]+)/$', views.assignment, name='assignment'),
    url(r'^modify-assignment/([0-9]+)/$', views.modify_assignment, name='modify-assignment'),
]
