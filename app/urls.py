from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pokedex/', views.pokedex, name='pokedex'),
    path('pokedex/<int:pokemon_id>/', views.detalhe_pokemon, name='detalhe_pokemon'),
]