from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', auth_views.login, {'template_name': 'serapis/login.html'}, name= 'login'),
    url(r'^homepage/$', views.homepage, name='homepage'),
    url(r'^registration/$', views.registration, name='registration'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
]
