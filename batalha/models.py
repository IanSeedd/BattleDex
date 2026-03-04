from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from app.models import Pokemon, Time, NPC 

class Battle(models.Model): # A batalha em si, só cria o models quando a batalha é de fato confirmada
    """Modelo principal que representa uma batalha"""
    is_random = models.BooleanField(default=False) # Indica se a batalha é aleatória (com pokemons aleátorios)
    BATTLE_STATUS = [ # Pendente não vai existir para evitar falhas e muitas requisições então a batalha só vai ser criada quando for aceita. 
        ('active', 'Em Andamento'),
        ('completed', 'Concluída'),
        ('cancelled', 'Interrompida'), # No caso de desistencias ou outras falhas
    ]
    
    BATTLE_TYPE = [
        ('trainer', 'Batalha contra Treinador'),
        ('bot', 'Batalha contra NPC'),
    ]
    
    # ------------------------ Participantes ------------------------
    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='battles_as_player'
    )
    opponent_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='battles_as_opponent'
    )
    opponent_npc = models.ForeignKey(
        NPC,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='battles_as_npc'
    )
    
    # ------------------------ Informações da batalha ------------------------
    battle_type = models.CharField(max_length=20, choices=BATTLE_TYPE)
    status = models.CharField(max_length=20, choices=BATTLE_STATUS, default='active')
    winner_content_type = models.ForeignKey(
        ContentType, # Simplesmente ajuda a identificar o tipo do vencedor (User ou NPC)
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'model__in': ('user', 'npc')} # Restringe a User ou NPC
    )
    winner_id = models.PositiveIntegerField(null=True, blank=True)
    winner = GenericForeignKey('winner_content_type', 'winner_id')
    winner_side = models.CharField(
        max_length=10, 
        choices=[('player', 'Jogador'), ('opponent', 'Oponente')],
        null=True, 
        blank=True
    )
    
    # ------------------------ Times ------------------------
    player_team = models.ForeignKey(
        Time,
        on_delete=models.CASCADE,
        related_name='player_battles'
    )
    opponent_team = models.ForeignKey(
        Time,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='opponent_battles'
    )
    
    # ------------------------ Metadados ------------------------
    created_at = models.DateTimeField(auto_now_add=True) # Data de inicio
    ended_at = models.DateTimeField(null=True, blank=True) # Data de término 
    turns_count = models.PositiveIntegerField(default=0) # Número de turnos
    def __str__(self):
        return f"Batalha #{self.id} - {self.player} vs {self.get_opponent_name()}"
    
    # ------------------------ Extra ------------------------
    is_ranked = models.BooleanField(default=False) # Por enquanto não implementado por conta de não existir PvP 
    
    def get_opponent_name(self):
        """Retorna o nome do oponente"""
        if self.opponent_user:
            return self.opponent_user.username
        elif self.opponent_npc:
            return self.opponent_npc.name
        return "Desafiante"
    
    def is_player_turn(self):
        """Determina de quem é o turno (simplificado - implementar lógica real)"""
        # Lógica básica: alterna por turno, se o turno é par é do jogador, se é ímpar é do oponente.
        return self.turns_count % 2 == 0
    
    def get_active_pokemon(self, side='player'):
        """Retorna o Pokémon ativo de um lado"""
        return BattlePokemon.objects.filter(
            battle=self,
            side=side,
            is_active=True,
            is_fainted=False
        ).first()
    
    # ------------------------ Condições de vitória ------------------------
    def check_battle_end(self): 
        player_count = self.battle_pokemons.filter(side='player', is_fainted=False).count()
        opponent_count = self.battle_pokemons.filter(side='opponent', is_fainted=False).count()
        
        if player_count == 0:
            self.set_winner('opponent')
            return 'opponent'
        if opponent_count == 0:
            self.set_winner('player')
            return 'player'
        return None
    def forfeit(self, user_who_left):
        """Encerra a batalha por desistência"""
        if self.status != 'active':
            return False, "Batalha não está ativa"
        
        if user_who_left == self.player:
            self.set_winner('opponent')
        elif user_who_left == self.opponent_user:
            self.set_winner('player')
        else:
            return False, "Usuário não está nesta batalha"
        
        # Criar um log especial de desistência
        BattleLog.objects.create(
            battle=self,
            level='defeat' if user_who_left == self.player else 'victory',
            message=f"{user_who_left.username} desistiu da batalha!"
        )
        
        return True, "Desistência processada"
    def set_winner(self, side):
        self.status = 'completed'
        self.ended_at = timezone.now()
        self.winner_side = side
        if side == 'player':
            self.winner = self.player
        else:
            self.winner = self.opponent_user or self.opponent_npc
        self.save()


    @property
    def duration(self):
        """Calcula a duração da batalha"""
        if self.created_at and self.ended_at:
            return self.ended_at - self.created_at
        return None
    def clean(self):
        """Validação completa da batalha"""
        from django.core.exceptions import ValidationError
        
        # Valida XOR para opponent_user e opponent_npc
        has_user_opponent = bool(self.opponent_user)
        has_npc_opponent = bool(self.opponent_npc)
        
        if has_user_opponent and has_npc_opponent:
            raise ValidationError("A batalha só pode ter um oponente (User OU NPC).")
        
        # Valida que não se pode batalhar contra si mesmo
        if self.opponent_user and self.opponent_user == self.player:
            raise ValidationError("Você não pode batalhar contra si mesmo.")
        
        # Na criação, valida time ativo
        if not self.pk:  # Se a batalha está sendo criada AGORA
            if not self.player_team.ativo:
                raise ValidationError("Você só pode iniciar uma batalha com seu time ativo.")
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class BattlePokemon(models.Model):
    """Representa um Pokémon em uma batalha específica"""
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name='battle_pokemons')
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    
    SIDE_CHOICES = [
        ('player', 'Jogador'),
        ('opponent', 'Oponente'),
    ]
    
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    position = models.PositiveSmallIntegerField()  # Posição no time (1-6)
    
    # Status de batalha
    current_hp = models.PositiveIntegerField()
    max_hp = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)
    is_fainted = models.BooleanField(default=False)
    is_confused = models.BooleanField(default=False)

    # Status conditions
    status_condition = models.CharField(
        max_length=20,
        choices=[
            ('none', 'Nenhum'),
            ('paralyzed', 'Paralisado'),
            ('poisoned', 'Envenenado'),
            ('badly_poisoned', 'Gravemente Envenenado'),
            ('burned', 'Queimado'),
            ('frozen', 'Congelado'),
            ('asleep', 'Dormindo'),
        ],
        default='none'
    )
    
    # Stat changes (estágios de -6 a +6)
    attack_stage = models.SmallIntegerField(default=0)
    defense_stage = models.SmallIntegerField(default=0)
    special_attack_stage = models.SmallIntegerField(default=0)
    special_defense_stage = models.SmallIntegerField(default=0)
    speed_stage = models.SmallIntegerField(default=0)
    accuracy_stage = models.SmallIntegerField(default=0)
    evasion_stage = models.SmallIntegerField(default=0)
    
    # Moves com PP atual
    move_1_pp = models.PositiveSmallIntegerField(default=0)
    move_2_pp = models.PositiveSmallIntegerField(default=0)
    move_3_pp = models.PositiveSmallIntegerField(default=0)
    move_4_pp = models.PositiveSmallIntegerField(default=0)
    
    # Contadores de batalha
    confusion_turns = models.PositiveSmallIntegerField(default=0)
    sleep_turns = models.PositiveSmallIntegerField(default=0)
    toxic_counter = models.PositiveSmallIntegerField(default=0)

    # Flags de batalha
    is_protected = models.BooleanField(default=False)
    is_switching = models.BooleanField(default=False)
    last_move_used = models.PositiveIntegerField(null=True, blank=True)  # ID do move
    
    class Meta:
        ordering = ['side', 'position']
        unique_together = ['battle', 'side', 'position']
    
    def __str__(self):
        return f"{self.pokemon} em {self.battle} ({self.side})"
    
    def take_damage(self, damage):
        """Aplica dano ao Pokémon"""
        self.current_hp = max(0, self.current_hp - damage)
        if self.current_hp == 0:
            self.is_fainted = True
            self.is_active = False
        self.save()
    
    def heal(self, amount):
        """Cura o Pokémon"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        self.save()
    
    def get_stat_multiplier(self, stage):
        """Calcula o multiplicador de stat baseado no estágio"""
        multipliers = {
            -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
            0: 2/2,
            1: 3/2, 2: 4/2, 3: 5/2, 4: 6/2, 5: 7/2, 6: 8/2
        }
        return multipliers.get(stage, 1.0)

class BattleTurn(models.Model):
    """Registra um turno completo da batalha"""
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name='turns')
    turn_number = models.PositiveIntegerField()
    
    # Ações do jogador
    player_action = models.CharField(max_length=20, choices=[
        ('move', 'Usar Movimento'),
        ('switch', 'Trocar Pokémon'),
    ])
    
    player_move_id = models.PositiveIntegerField(null=True, blank=True)
    player_target = models.CharField(max_length=10, null=True, blank=True)  # 'opponent' ou 'self'
    player_switch_to = models.ForeignKey(
        BattlePokemon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='turns_switched_in'
    )
    
    # Ações do oponente (NPC ou outro jogador)
    opponent_action = models.CharField(max_length=20, null=True, blank=True)
    opponent_move_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Resultados
    damage_dealt = models.PositiveIntegerField(default=0)
    damage_taken = models.PositiveIntegerField(default=0)
    
    status_applied = models.CharField(max_length=20, null=True, blank=True)
    stat_changes = models.JSONField(default=dict)  # Ex: {'player_attack': 1, 'opponent_speed': -1}
    # Verifica se há uma vitória
    def process_turn_results(self):
        """Lógica disparada após cada ação de dano"""
        winner_side = self.check_battle_end()
        if winner_side:
            self.battle.set_winner(winner_side)
            return True
        return False

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    execution_order = models.JSONField(default=list)  # Ordem de execução das ações
    
    def __str__(self):
        return f"Turno {self.turn_number} - Batalha #{self.battle.id}"

class BattleLog(models.Model):
    """Log de eventos da batalha (para histórico)"""
    LOG_LEVELS = [
        ('damage', 'Dano'),
        ('status', 'Status'),
        ('switch', 'Troca'),
        ('victory', 'Vitória'),
        ('defeat', 'Derrota'),
    ]
    
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name='logs')
    turn = models.ForeignKey(BattleTurn, null=True, blank=True, on_delete=models.SET_NULL)
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    
    # Dados adicionais
    pokemon = models.ForeignKey(BattlePokemon, null=True, blank=True, on_delete=models.SET_NULL)
    move_id = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}..."

class BattleQueue(models.Model): # Por enquanto não será implementado, mas é a base para o matchmaking PvP
    """Fila para batalhas PvP (matchmaking)"""
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    player_team = models.ForeignKey(Time, on_delete=models.CASCADE)
    
    QUEUE_STATUS = [
        ('waiting', 'Esperando'),
        ('matched', 'Encontrado'),
        ('cancelled', 'Cancelado'),
    ]
    
    status = models.CharField(max_length=10, choices=QUEUE_STATUS, default='waiting')
    min_rating = models.PositiveIntegerField(default=0)
    max_rating = models.PositiveIntegerField(default=3000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Queue #{self.id} - {self.player}"