from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class NPC(models.Model): # WORK IN PROGRESS
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Pokemon(models.Model):
    pokeapi_id = models.PositiveIntegerField()
    random = models.BooleanField( # Se o pokemon é randomico
        default=False,
    )
    # --- DONO: ---
    dono_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    dono_npc = models.ForeignKey(
        NPC,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    

    # --- IDENTIDADE/DEFINIÇÕES_DO_USUÁRIO ---
    apelido = models.CharField(max_length=50, blank=True)
    level = models.PositiveSmallIntegerField(default=100)
    shiny = models.BooleanField(default=False)
    genero = models.CharField(
    max_length=10,
    choices=[
        ("male", "Male"),
        ("female", "Female"),
        ("genderless", "Genderless"),
    ],
    default="male"
    )
    # --- MOVES ---
    move_1 = models.PositiveIntegerField(null=True, blank=True) # Eles são IDs do pokeAPI
    move_2 = models.PositiveIntegerField(null=True, blank=True)
    move_3 = models.PositiveIntegerField(null=True, blank=True)
    move_4 = models.PositiveIntegerField(null=True, blank=True)
    # --- Natures ---
    NATURE_CHOICES = [
        ("hardy", "Hardy"),
        ("lonely", "Lonely"),
        ("brave", "Brave"),
        ("adamant", "Adamant"),
        ("naughty", "Naughty"),

        ("bold", "Bold"),
        ("docile", "Docile"),
        ("relaxed", "Relaxed"),
        ("impish", "Impish"),
        ("lax", "Lax"),

        ("timid", "Timid"),
        ("hasty", "Hasty"),
        ("serious", "Serious"),
        ("jolly", "Jolly"),
        ("naive", "Naive"),

        ("modest", "Modest"),
        ("mild", "Mild"),
        ("quiet", "Quiet"),
        ("bashful", "Bashful"),
        ("rash", "Rash"),

        ("calm", "Calm"),
        ("gentle", "Gentle"),
        ("sassy", "Sassy"),
        ("careful", "Careful"),
        ("quirky", "Quirky"),
    ]

    nature = models.CharField(
        max_length=20,
        choices=NATURE_CHOICES,
        default="hardy"
    )
    # --- Item --- 
    item_id = models.PositiveIntegerField( # Funiona por ID
        null=True,
        blank=True,
    )
    # --- IVs ---
    iv_hp = models.PositiveSmallIntegerField(default=31)
    iv_atk = models.PositiveSmallIntegerField(default=31)
    iv_def = models.PositiveSmallIntegerField(default=31)
    iv_spa = models.PositiveSmallIntegerField(default=31)
    iv_spd = models.PositiveSmallIntegerField(default=31)
    iv_spe = models.PositiveSmallIntegerField(default=31)
    # --- EVs ---
    ev_hp = models.PositiveSmallIntegerField(default=0)
    ev_atk = models.PositiveSmallIntegerField(default=0)
    ev_def = models.PositiveSmallIntegerField(default=0)
    ev_spa = models.PositiveSmallIntegerField(default=0)
    ev_spd = models.PositiveSmallIntegerField(default=0)
    ev_spe = models.PositiveSmallIntegerField(default=0)
    # VALIDAÇÃO DE IVS E EVS:
    def clean(self): # OBS: clean é um metódo de validação do django
        # Validador de moves, verifica se não há mais de 4 moves
        moves = [
            self.move_1,
            self.move_2,
            self.move_3,
            self.move_4,
        ]

        moves = [m for m in moves if m is not None]

        if len(set(moves)) != len(moves):
            raise ValidationError("Moves duplicados não são permitidos.")

        # Limite individual de EV
        evs = [
            self.ev_hp,
            self.ev_atk,
            self.ev_def,
            self.ev_spa,
            self.ev_spd,
            self.ev_spe,
        ]

        if any(ev > 252 for ev in evs): # Limite singular
            raise ValidationError("Nenhum EV pode ultrapassar 252.") # OBS: Raise interrompe a execução caso ocorra um erro

        # Limite total de EV
        if sum(evs) > 508:
            raise ValidationError("A soma total dos EVs não pode ultrapassar 508.")

        # Limite de IV
        ivs = [
            self.iv_hp,
            self.iv_atk,
            self.iv_def,
            self.iv_spa,
            self.iv_spd,
            self.iv_spe,
        ]

        # ---------- DONO (XOR) ---------- eXclusive OR
        if bool(self.dono_user) == bool(self.dono_npc):
            raise ValidationError(
                "Pokémon deve pertencer a UM usuário OU UM NPC (nunca ambos)."
            )

        if any(iv > 31 for iv in ivs):
            raise ValidationError("IVs devem estar entre 0 e 31.")
        

    # Se um move for o mesmo ele muda esse move para o ultimo slot no qual ele foi colocado
    def move_duplicado(self, move_id, slot):
        slots = [
            self.move_1_id,
            self.move_2_id,
            self.move_3_id,
            self.move_4_id,
        ]

        # Remove duplicado
        for i, move in enumerate(slots):
            if move == move_id:
                slots[i] = None

        # Coloca no slot desejado
        slots[slot - 1] = move_id

        (
            self.move_1_id,
            self.move_2_id,
            self.move_3_id,
            self.move_4_id,
        ) = slots

        
    def __str__(self):
        return self.apelido or f"Pokémon #{self.pokeapi_id}"
    
class Time(models.Model):
    nome = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default="Time Indefinido"
    )
    dono_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    dono_npc = models.ForeignKey(
        NPC,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    def clean(self):
        if bool(self.dono_user) == bool(self.dono_npc):
            raise ValidationError("Um time não pode pertecer a um jogador e a um NPC ao mesmo tempo.")

    def __str__(self):
        return f"Time #{self.id}"
    

class TimePokemon(models.Model): # Intermediário entre time e pokemon (resumindo os slots do time)
    time = models.ForeignKey(
        Time,
        on_delete=models.CASCADE,
    )

    pokemon = models.ForeignKey(
        Pokemon,
        on_delete=models.CASCADE, # Se um pokemon é deletado ele some dos times 
    )

    slot = models.PositiveSmallIntegerField()  # 1 a 6

    class Meta:
        constraints = [ # Regra do banco de dados, situações que nunca devem acontecer
            # Um Pokémon não pode se repetir no mesmo time
            models.UniqueConstraint(
                fields=["time", "pokemon"],
                name="unique_pokemon_per_time" # Nome decorativo, no caso serve para erros
            ),
            # Um slot só pode ter um Pokémon
            models.UniqueConstraint(
                fields=["time", "slot"],
                name="unique_slot_per_time"
            ),
        ]

    def clean(self):
        if not 1 <= self.slot <= 6: # Valores possíveis para um slot
            raise ValidationError("Slot deve estar entre 1 e 6.")

    def __str__(self):
        return f"{self.pokemon} no slot {self.slot}"