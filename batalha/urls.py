from django.urls import path
from . import views

urlpatterns = [
    path('', views.batalha_view, name='batalha'),
]