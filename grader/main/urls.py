from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'main/login.html'}, name= 'login'),
    url(r'^homepage/$', views.homepage, name='homepage'),
    url(r'^password_reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^registration/$', views.registration, name='registration')
    ]

