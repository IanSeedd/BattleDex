from django.urls import path
from . import views

urlpatterns = [
    path('', views.pokedex, name='pokedex'),
]