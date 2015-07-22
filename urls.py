from django.conf.urls import patterns, url

from deepdreams import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^begindream', views.begindream, name='begindream'),
    url(r'^checkdream', views.checkdream, name='checkdream'),
)
