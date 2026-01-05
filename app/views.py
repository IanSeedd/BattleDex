import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from .models import Pokemon, Time, TimePokemon
import requests
from django.db import transaction
from .forms import CriarPokemonForm


POKEAPI = "https://pokeapi.co/api/v2"
# --- Tratamento de formas ---
# Formas permitidas
ALLOWED_FORMS = (
    "-mega", "-gmax", "-alola", "-galar",
    "-hisui", "-paldea", "-battle-bond","-primal",
)

# Formas proibidas
BLOCKED_FORMS = (
    "-ash",
    "-totem",
    "-cap"
)

def home(request):
    context = {} 
    
    return render(request, 'home.html', context)


def pokedex(request):
    try:
        # O limite 1025 garante que pegar até o fim da 9ª geração (Pecharunt)
        response = requests.get('https://pokeapi.co/api/v2/pokemon-species?limit=1025')
        data = response.json()
        
        pokemons = []
        for pokemon in data['results']:
            # Extraímos a entrada da pokedex da URL, criando um int.
            pokemon_id = int(pokemon['url'].split('/')[-2]) # A cada / o texto é separado e no final ele pega a posição -2 da lista criada e transforma em INT
            
            # Limpa o nome tirando os "-"
            display_name = pokemon['name'].replace('-', ' ').title()
            
            # Apenas deixa os nomes com hifén (casos especiais)
            if display_name == "Ho Oh": display_name = "Ho-Oh"
            if display_name == "Porygon Z": display_name = "Porygon-Z"

            pokemons.append({
                'id': pokemon_id, # Número da pokedex
                'name': display_name, # Nome fora do formato slug
                'url_name': pokemon['name'] # Tratamento de url para futura pagina de detalhes 
            })
        
        # Ordena por entrada da pokedex
        pokemons.sort(key=lambda x: x['id']) # Lambda para otimizar o codigo sem criar uma função extra para ordenar (Os "x": 1°- Pokémon(parametro), 2°-ID(return da func))
        
        context = {
            'pokemons': pokemons,
            'total': len(pokemons)
        }
        return render(request, 'pokedex.html', context)
        
    except Exception as e: # Só para erros
        return render(request, 'pokedex.html', {'pokemons': [], 'error': str(e)})

    
def detalhe_pokemon(request, pokemon_id):
    try:
        pokemon_res = requests.get(f"{POKEAPI}/pokemon/{pokemon_id}")
        pokemon_data = pokemon_res.json()

        species_res = requests.get(pokemon_data["species"]["url"])
        species_data = species_res.json()

        filtered_varieties = []
        for v in species_data["varieties"]:
            name = v["pokemon"]["name"]
            # Extrair ID da URL: https://pokeapi.co/api/v2/pokemon/10033/ -> 10033
            v_id = v["pokemon"]["url"].split('/')[-2]

            # 1. Bloqueia formas proibidas
            if any(block in name for block in BLOCKED_FORMS):
                continue

            # 2. Se for a forma padrão OU uma das permitidas, adiciona
            if v["is_default"] or any(allowed in name for allowed in ALLOWED_FORMS):
                filtered_varieties.append({
                    "id": v_id,
                    "name": name,
                    "is_default": v["is_default"]
                })

        context = {
            "pokemon_id": pokemon_id,
            "species_name": species_data["name"],
            "varieties": filtered_varieties, # Enviando a lista filtrada
        }
        return render(request, "detalhe_pokemon.html", context)
    except Exception as e:
        return render(request, "detalhe_pokemon.html", {"pokemon_id": pokemon_id, "error": str(e)})
@login_required
def box_view(request):
    user = request.user
    
    # 1. Pega ou cria um time ativo
    time_ativo = Time.objects.filter(dono_user=user).first()
    if not time_ativo:
        time_ativo = Time.objects.create(dono_user=user, nome="Time Principal")

    # 2. Prepara os 6 Slots do Time (Lógica Nova)
    # Cria uma lista com 6 espaços vazios (None)
    team_slots_list = [None] * 6 
    
    # Preenche os slots ocupados
    slots_ocupados = TimePokemon.objects.filter(time=time_ativo).select_related('pokemon')
    ids_no_time = []
    
    for tp in slots_ocupados:
        ids_no_time.append(tp.pokemon.id)
        if 1 <= tp.slot <= 6:
            # Coloca o pokemon na posição correta da lista (slot 1 vira index 0)
            team_slots_list[tp.slot - 1] = tp.pokemon

    # 3. Identifica Pokémons na Box
    pokemons_box = Pokemon.objects.filter(dono_user=user).exclude(id__in=ids_no_time)

    # 4. Walkers Aleatórios
    random_walkers = [random.randint(1, 898) for _ in range(15)]

    return render(request, 'box.html', {
        'time': time_ativo,
        'team_slots_list': team_slots_list, # <--- Nova Variável Simples
        'pokemons_box': pokemons_box,
        'random_walkers': random_walkers,
    })
@login_required
@require_POST
def update_team_slot(request):
    try:
        data = json.loads(request.body)
        pokemon_id = int(data.get('pokemon_id'))
        # Se slot vier, converte pra int, senão fica None
        slot = int(data.get('slot')) if data.get('slot') else None
        
        # Pega o time principal do usuário
        time_ativo = Time.objects.filter(dono_user=request.user).first()
        if not time_ativo:
            time_ativo = Time.objects.create(dono_user=request.user, nome="Principal")

        pokemon = Pokemon.objects.get(id=pokemon_id, dono_user=request.user)

        # USAMOS TRANSACTION PARA GARANTIR QUE NADA SUMA
        with transaction.atomic():
            # 1. Remove esse pokémon de onde ele estiver nesse time (limpa duplicatas)
            TimePokemon.objects.filter(time=time_ativo, pokemon=pokemon).delete()

            if slot:
                # 2. Se estiver indo para um slot (1-6)
                # Remove quem estava nesse slot antes (vai pra box automaticamente)
                TimePokemon.objects.filter(time=time_ativo, slot=slot).delete()
                
                # 3. Adiciona o Pokémon no slot novo
                TimePokemon.objects.create(time=time_ativo, pokemon=pokemon, slot=slot)
            
            # Se slot for None (arrastou pra box), a gente só fez o passo 1 e parou,
            # o que efetivamente joga ele pra box.

        return JsonResponse({'status': 'success'})

    except Pokemon.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pokémon não encontrado.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def criar_pokemon_view(request):
    # Cria uma instância temporária já com o dono definido para evitar o erro de validação
    pokemon_instance = Pokemon(dono_user=request.user)

    if request.method == 'POST':
        # Passamos a instância para o formulário saber que o dono já existe
        form = CriarPokemonForm(request.POST, instance=pokemon_instance)
        if form.is_valid():
            pokemon = form.save(commit=False)
            pokemon.level = 100 # Level fixo
            pokemon.save()
            return redirect('box')
    else:
        form = CriarPokemonForm(instance=pokemon_instance)

    return render(request, 'criar_pokemon.html', {'form': form})
