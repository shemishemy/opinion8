# app/urls.py

from django.urls import path
from . import views


app_name = 'app'

urlpatterns = [
        path('index/', views.index, name='index'),
        path('detail/<int:pk>/', views.detail, name='detail'),
        path('', views.upload, name='upload'),
]