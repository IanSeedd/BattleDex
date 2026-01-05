from django import forms
from .models import Pokemon

class CriarPokemonForm(forms.ModelForm):
    class Meta:
        model = Pokemon
        # Incluímos todos os campos editáveis
        fields = [
            'pokeapi_id', 'apelido', 'shiny', 'genero', 'nature', 'item_id',
            'move_1', 'move_2', 'move_3', 'move_4',
            'iv_hp', 'iv_atk', 'iv_def', 'iv_spa', 'iv_spd', 'iv_spe',
            'ev_hp', 'ev_atk', 'ev_def', 'ev_spa', 'ev_spd', 'ev_spe',
        ]
        widgets = {
            # Escondemos o ID da API pois será preenchido via JS ao escolher o pokémon visualmente
            'pokeapi_id': forms.HiddenInput(),
            'item_id': forms.HiddenInput(),
            'move_1': forms.HiddenInput(),
            'move_2': forms.HiddenInput(),
            'move_3': forms.HiddenInput(),
            'move_4': forms.HiddenInput(),
        }

    def clean(self):
        # A validação principal (soma de EVs, duplicatas) já está no Model.clean()
        # O Django chama o model.clean() automaticamente ao salvar.
        return super().clean()