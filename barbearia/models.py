from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from urllib.parse import quote

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATORS
# ─────────────────────────────────────────────────────────────────────────────

_tel_validator = RegexValidator(
    regex=r'^\(?\d{2}\)?[\s\-]?9?\d{4}[\s\-]?\d{4}$',
    message='Informe um número válido. Ex: (83) 99999-9999',
)

# ─────────────────────────────────────────────────────────────────────────────
# CHOICES
# ─────────────────────────────────────────────────────────────────────────────

STATUS_AGENDAMENTO = [
    ('agendado', 'Agendado'),
    ('confirmado', 'Confirmado'),
    ('em_atendimento', 'Em Atendimento'),
    ('concluido', 'Concluído'),
    ('cancelado', 'Cancelado'),
    ('faltou', 'Faltou'),
]

CATEGORIA_SAIDA = [
    ('aluguel', 'Aluguel'),
    ('produtos', 'Produtos'),
    ('salario', 'Salário'),
    ('equipamentos', 'Equipamentos'),
    ('outros', 'Outros'),
]

TIPO_NOTIFICACAO = [
    ('novo_agendamento', 'Novo Agendamento'),
    ('cancelamento', 'Cancelamento'),
    ('pendencia', 'Pendência'),
    ('aviso', 'Aviso'),
]

DIA_SEMANA_CHOICES = [
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo'),
]


# ─────────────────────────────────────────────────────────────────────────────
# PLANO DE ASSINATURA
# ─────────────────────────────────────────────────────────────────────────────

class Plano(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2)
    servicos = models.ManyToManyField('Servico', blank=True, related_name='planos')
    cor = models.CharField(max_length=7, default='#FFD700')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['preco_mensal']

    def __str__(self):
        return f"{self.nome} — R$ {self.preco_mensal}/mês"

    def num_clientes_ativos(self):
        return self.clientes.count()

    def receita_mensal_esperada(self):
        return self.preco_mensal * self.num_clientes_ativos()


# ─────────────────────────────────────────────────────────────────────────────
# BARBEIRO  (modelo próprio — separado do login Django)
# ─────────────────────────────────────────────────────────────────────────────

class Barbeiro(models.Model):
    nome = models.CharField(max_length=150)
    whatsapp = models.CharField(max_length=20, validators=[_tel_validator])
    data_nascimento = models.DateField(null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='barbearia/barbeiros/', blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Barbeiro'
        verbose_name_plural = 'Barbeiros'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def whatsapp_limpo(self):
        return ''.join(filter(str.isdigit, self.whatsapp))

    def link_whatsapp(self):
        num = self.whatsapp_limpo()
        if not num.startswith('55'):
            num = '55' + num
        return f"https://wa.me/{num}"


# ─────────────────────────────────────────────────────────────────────────────
# GRADE DE HORÁRIOS  (dias e turnos de trabalho do barbeiro)
# ─────────────────────────────────────────────────────────────────────────────

class GradeHorario(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='grade_horarios')
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Grade de Horário'
        verbose_name_plural = 'Grades de Horários'
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['barbeiro', 'dia_semana']

    def __str__(self):
        return (
            f"{self.barbeiro.nome} — "
            f"{self.get_dia_semana_display()}: {self.hora_inicio:%H:%M}–{self.hora_fim:%H:%M}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SERVIÇO
# ─────────────────────────────────────────────────────────────────────────────

class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField(default=30)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} — R$ {self.preco}"


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE
# ─────────────────────────────────────────────────────────────────────────────

class Cliente(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, validators=[_tel_validator])
    data_nascimento = models.DateField(null=True, blank=True)
    plano = models.ForeignKey(
        Plano, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='clientes',
    )
    # Vínculo opcional com Django User para acesso ao portal do cliente
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cliente_perfil',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def telefone_limpo(self):
        return ''.join(filter(str.isdigit, self.telefone))

    def tem_plano(self):
        return self.plano is not None


# ─────────────────────────────────────────────────────────────────────────────
# AGENDAMENTO
# ─────────────────────────────────────────────────────────────────────────────

class Agendamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    barbeiro = models.ForeignKey(
        Barbeiro, on_delete=models.SET_NULL, null=True, related_name='agendamentos',
    )
    servico = models.ForeignKey(Servico, on_delete=models.SET_NULL, null=True, related_name='agendamentos')
    data_hora = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_AGENDAMENTO, default='agendado')
    valor_cobrado = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    observacoes = models.TextField(blank=True)
    lembrete_enviado = models.BooleanField(default=False)
    lembrete_enviado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.cliente.nome} — {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.valor_cobrado and self.servico:
            if self.servico_coberto_pelo_plano():
                self.valor_cobrado = 0
            else:
                self.valor_cobrado = self.servico.preco
        super().save(*args, **kwargs)

    def servico_coberto_pelo_plano(self):
        if not self.servico or not self.cliente_id:
            return False
        plano = getattr(self.cliente, 'plano', None)
        if not plano:
            return False
        return plano.servicos.filter(pk=self.servico_id).exists()

    def valor_efetivo(self):
        if self.servico_coberto_pelo_plano():
            return 0
        return self.valor_cobrado or (self.servico.preco if self.servico else 0)

    def gerar_link_whatsapp(self):
        telefone = self.cliente.telefone_limpo()
        if not telefone.startswith('55'):
            telefone = '55' + telefone
        data_fmt = self.data_hora.strftime('%d/%m/%Y')
        hora_fmt = self.data_hora.strftime('%H:%M')
        mensagem = (
            f"Olá {self.cliente.nome}, confirmamos seu horário na Boss Barbearia "
            f"para o dia {data_fmt} às {hora_fmt}. Podemos confirmar sua presença?"
        )
        return f"https://wa.me/{telefone}?text={quote(mensagem)}"

    def gerar_link_lembrete(self):
        telefone = self.cliente.telefone_limpo()
        if not telefone.startswith('55'):
            telefone = '55' + telefone
        primeiro_nome = self.cliente.nome.split()[0]
        data_fmt = self.data_hora.strftime('%d/%m')
        hora_fmt = self.data_hora.strftime('%H:%M')
        servico_nome = self.servico.nome if self.servico else 'serviço'
        barbeiro_nome = self.barbeiro.nome if self.barbeiro else 'nosso barbeiro'
        mensagem = (
            f"Olá, *{primeiro_nome}*! 👋\n\n"
            f"Lembramos do seu horário amanhã na *Boss Barbearia* 💈\n\n"
            f"📅 *{data_fmt}* às *{hora_fmt}h*\n"
            f"✂️ {servico_nome}\n"
            f"👨‍💼 Barbeiro: {barbeiro_nome}\n\n"
            f"Te esperamos! Se precisar cancelar, acesse o portal ou responda esta mensagem."
        )
        return f"https://wa.me/{telefone}?text={quote(mensagem)}"

    def status_css(self):
        return {
            'agendado': 'badge-agendado',
            'confirmado': 'badge-confirmado',
            'em_atendimento': 'badge-em_atendimento',
            'concluido': 'badge-concluido',
            'cancelado': 'badge-cancelado',
            'faltou': 'badge-faltou',
        }.get(self.status, '')


# ─────────────────────────────────────────────────────────────────────────────
# HORÁRIO BLOQUEADO
# ─────────────────────────────────────────────────────────────────────────────

class HorarioBloqueado(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='horarios_bloqueados')
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    motivo = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Horário Bloqueado'
        verbose_name_plural = 'Horários Bloqueados'
        ordering = ['data_inicio']

    def __str__(self):
        return (
            f"{self.barbeiro.nome} — "
            f"{self.data_inicio.strftime('%d/%m %H:%M')} a {self.data_fim.strftime('%H:%M')}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# DESPESA (SAÍDA)
# ─────────────────────────────────────────────────────────────────────────────

class Saida(models.Model):
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    categoria = models.CharField(max_length=30, choices=CATEGORIA_SAIDA, default='outros')
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-data']

    def __str__(self):
        return f"{self.descricao} — R$ {self.valor}"


# ─────────────────────────────────────────────────────────────────────────────
# PERMISSÃO DE USUÁRIO DO SISTEMA
# ─────────────────────────────────────────────────────────────────────────────

class PermissaoUsuario(models.Model):
    """
    Controla quais funcionalidades cada usuário do sistema pode acessar.
    'master=True' concede acesso total, equivalente a superusuário no sistema.
    """
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='permissao',
    )
    master = models.BooleanField(default=False, verbose_name='Master (acesso total)')

    # Funcionalidades individuais
    agenda = models.BooleanField(default=True, verbose_name='Agenda')
    clientes = models.BooleanField(default=True, verbose_name='Clientes')
    barbeiros = models.BooleanField(default=True, verbose_name='Barbeiros')
    servicos = models.BooleanField(default=True, verbose_name='Serviços')
    financeiro = models.BooleanField(default=False, verbose_name='Financeiro')
    planos = models.BooleanField(default=False, verbose_name='Planos')
    relatorios = models.BooleanField(default=False, verbose_name='Relatórios')
    configuracoes = models.BooleanField(default=False, verbose_name='Configurações')

    class Meta:
        verbose_name = 'Permissão de Usuário'
        verbose_name_plural = 'Permissões de Usuários'

    def __str__(self):
        return f"Permissões de {self.usuario.username}"

    def tem_acesso(self, funcionalidade: str) -> bool:
        """True se master ou se a funcionalidade específica está habilitada."""
        if self.master:
            return True
        return bool(getattr(self, funcionalidade, False))

    def lista_acessos(self) -> list[str]:
        """Retorna nomes das funcionalidades liberadas."""
        if self.master:
            return ['master']
        campos = ['agenda', 'clientes', 'barbeiros', 'servicos',
                  'financeiro', 'planos', 'relatorios', 'configuracoes']
        return [c for c in campos if getattr(self, c)]


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICAÇÃO (para usuários do sistema — admin/funcionário)
# ─────────────────────────────────────────────────────────────────────────────

class Notificacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes_barbearia')
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    tipo = models.CharField(max_length=30, choices=TIPO_NOTIFICACAO, default='aviso')
    link = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.usuario.username}: {self.mensagem[:60]}"

    def icone(self):
        return {
            'novo_agendamento': 'fa-calendar-plus',
            'cancelamento': 'fa-calendar-times',
            'pendencia': 'fa-exclamation-triangle',
            'aviso': 'fa-bell',
        }.get(self.tipo, 'fa-bell')
