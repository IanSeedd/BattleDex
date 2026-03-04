from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models import Time, TimePokemon, Pokemon
import random
@login_required
def batalha_view(request):
    # AGORA SIM! Usando o seu próprio método maravilhoso do models.py
    # Ele garante que vai pegar o seu time e forçar ele a ficar Ativo
    time_ativo = Time.get_active_for_user(request.user)
    
    team_pokemons = []
    
    if time_ativo:
        # Pega as relações e extrai os Pokémons reias ordenados pelo slot da sua box!
        relacoes = TimePokemon.objects.filter(time=time_ativo).order_by('slot').select_related('pokemon')
        team_pokemons = [rel.pokemon for rel in relacoes]

    # Se você literalmente não colocou nenhum Pokémon no time lá na Box
    if not team_pokemons:
        return render(request, 'batalha.html', {
            'error_message': 'Seu time está vazio! Vá para a Box e arraste pelo menos um Pokémon para a Equipe Atual.'
        })

    # O seu primeiro Pokémon do slot é o que entra em campo
    active_pokemon = team_pokemons[0]

    # Adversário selvagem
    wild_id = random.randint(1, 649)
    
    context = {
        'active_pokemon': active_pokemon,
        'team_pokemons': team_pokemons, 
        'wild_id': wild_id,
    }
    
    return render(request, 'batalha.html', context)