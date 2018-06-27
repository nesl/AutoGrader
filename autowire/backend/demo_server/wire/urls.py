from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^configure_device', views.configure_device, name='configure_device'),
    url(r'^$', views.index, name='index'),
]