from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import (Agendamento, Barbeiro, Cliente, GradeHorario,
                     HorarioBloqueado, Plano, Saida, Servico)

_fc = {'class': 'form-control'}
_fs = {'class': 'form-select'}
_fcsm = {'class': 'form-control form-control-sm'}
_fssm = {'class': 'form-select form-select-sm'}


# ─────────────────────────────────────────────────────────────────────────────
# BARBEIRO (modelo próprio — não é User do Django)
# ─────────────────────────────────────────────────────────────────────────────

class BarbeiroForm(forms.ModelForm):
    class Meta:
        model = Barbeiro
        fields = ['nome', 'whatsapp', 'data_nascimento', 'foto_perfil', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs=_fc),
            'whatsapp': forms.TextInput(attrs={**_fc, 'placeholder': '(83) 99999-9999'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', **_fc}),
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_nascimento'].required = False
        self.fields['foto_perfil'].required = False


# ─────────────────────────────────────────────────────────────────────────────
# GRADE DE HORÁRIOS (InlineFormSet vinculado a Barbeiro)
# ─────────────────────────────────────────────────────────────────────────────

GradeHorarioFormSet = inlineformset_factory(
    Barbeiro,
    GradeHorario,
    fields=['dia_semana', 'hora_inicio', 'hora_fim', 'ativo'],
    extra=7,
    can_delete=True,
    widgets={
        'dia_semana': forms.Select(attrs=_fssm),
        'hora_inicio': forms.TimeInput(attrs={'type': 'time', **_fcsm}),
        'hora_fim': forms.TimeInput(attrs={'type': 'time', **_fcsm}),
        'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input mt-2'}),
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# AGENDAMENTO
# ─────────────────────────────────────────────────────────────────────────────

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['cliente', 'barbeiro', 'servico', 'data_hora', 'valor_cobrado', 'observacoes']
        widgets = {
            'data_hora': forms.DateTimeInput(
                attrs={'type': 'datetime-local', **_fc}, format='%Y-%m-%dT%H:%M',
            ),
            'cliente': forms.Select(attrs=_fs),
            'barbeiro': forms.Select(attrs=_fs),
            'servico': forms.Select(attrs={**_fs, 'id': 'id_servico'}),
            'valor_cobrado': forms.NumberInput(attrs={**_fc, 'step': '0.01', 'id': 'id_valor_cobrado'}),
            'observacoes': forms.Textarea(attrs={**_fc, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['barbeiro'].queryset = Barbeiro.objects.filter(ativo=True)
        self.fields['data_hora'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['valor_cobrado'].required = False
        self.fields['observacoes'].required = False


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE  — campos: nome, telefone, data_nascimento, plano
# ─────────────────────────────────────────────────────────────────────────────

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'data_nascimento', 'plano']
        widgets = {
            'nome': forms.TextInput(attrs=_fc),
            'telefone': forms.TextInput(attrs={**_fc, 'placeholder': '(83) 99999-9999'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', **_fc}),
            'plano': forms.Select(attrs=_fs),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plano'].queryset = Plano.objects.filter(ativo=True)
        self.fields['plano'].required = False
        self.fields['data_nascimento'].required = False


# ─────────────────────────────────────────────────────────────────────────────
# PLANO
# ─────────────────────────────────────────────────────────────────────────────

class PlanoForm(forms.ModelForm):
    class Meta:
        model = Plano
        fields = ['nome', 'descricao', 'preco_mensal', 'servicos', 'cor', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs=_fc),
            'descricao': forms.Textarea(attrs={**_fc, 'rows': 3}),
            'preco_mensal': forms.NumberInput(attrs={**_fc, 'step': '0.01', 'min': '0'}),
            'servicos': forms.CheckboxSelectMultiple(),
            'cor': forms.TextInput(attrs={**_fc, 'type': 'color', 'style': 'height:44px;'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicos'].queryset = Servico.objects.filter(ativo=True)
        self.fields['servicos'].required = False


# ─────────────────────────────────────────────────────────────────────────────
# SERVIÇO
# ─────────────────────────────────────────────────────────────────────────────

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'preco', 'duracao_minutos', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs=_fc),
            'descricao': forms.Textarea(attrs={**_fc, 'rows': 3}),
            'preco': forms.NumberInput(attrs={**_fc, 'step': '0.01', 'min': '0'}),
            'duracao_minutos': forms.NumberInput(attrs={**_fc, 'min': '5', 'step': '5'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────────────────────────────────────────

class SaidaForm(forms.ModelForm):
    class Meta:
        model = Saida
        fields = ['descricao', 'valor', 'data', 'categoria', 'observacoes']
        widgets = {
            'descricao': forms.TextInput(attrs=_fc),
            'valor': forms.NumberInput(attrs={**_fc, 'step': '0.01'}),
            'data': forms.DateInput(attrs={'type': 'date', **_fc}),
            'categoria': forms.Select(attrs=_fs),
            'observacoes': forms.Textarea(attrs={**_fc, 'rows': 3}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUEIO DE HORÁRIO
# ─────────────────────────────────────────────────────────────────────────────

class HorarioBloqueadoForm(forms.ModelForm):
    class Meta:
        model = HorarioBloqueado
        fields = ['barbeiro', 'data_inicio', 'data_fim', 'motivo']
        widgets = {
            'barbeiro': forms.Select(attrs=_fs),
            'data_inicio': forms.DateTimeInput(
                attrs={'type': 'datetime-local', **_fc}, format='%Y-%m-%dT%H:%M',
            ),
            'data_fim': forms.DateTimeInput(
                attrs={'type': 'datetime-local', **_fc}, format='%Y-%m-%dT%H:%M',
            ),
            'motivo': forms.TextInput(attrs=_fc),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['barbeiro'].queryset = Barbeiro.objects.filter(ativo=True)
        self.fields['data_inicio'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['data_fim'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['motivo'].required = False


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES — USUÁRIOS DO SISTEMA (permissões por funcionalidade)
# ─────────────────────────────────────────────────────────────────────────────

# Lista de (campo, label, descrição curta) para as permissões
FUNCIONALIDADES = [
    ('master',        'Master',        'Acesso total ao sistema'),
    ('agenda',        'Agenda',        'Ver e criar agendamentos'),
    ('clientes',      'Clientes',      'Gerenciar clientes'),
    ('barbeiros',     'Barbeiros',     'Gerenciar equipe de barbeiros'),
    ('servicos',      'Serviços',      'Gerenciar catálogo de serviços'),
    ('financeiro',    'Financeiro',    'Entradas, despesas e saldo'),
    ('planos',        'Planos',        'Gerenciar planos de assinatura'),
    ('relatorios',    'Relatórios',    'Relatório de clientes por plano'),
    ('configuracoes', 'Configurações', 'Gerenciar usuários do sistema'),
]

_chk = {'class': 'form-check-input'}


def _perm_fields():
    """Retorna fields de BooleanField para cada funcionalidade."""
    fields = {}
    for campo, label, _ in FUNCIONALIDADES:
        default_on = campo in ('agenda', 'clientes', 'barbeiros', 'servicos')
        fields[campo] = forms.BooleanField(
            required=False, label=label,
            initial=default_on,
            widget=forms.CheckboxInput(attrs={**_chk, 'data-perm': campo}),
        )
    return fields


class SistemaUsuarioForm(forms.Form):
    username = forms.CharField(
        max_length=150, label='Login',
        widget=forms.TextInput(attrs={**_fc, 'placeholder': 'Ex: ana_recepcao', 'autocomplete': 'off'}),
    )
    password = forms.CharField(
        label='Senha', min_length=6,
        widget=forms.PasswordInput(attrs={**_fc, 'placeholder': 'Mínimo 6 caracteres', 'autocomplete': 'new-password'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, field in _perm_fields().items():
            self.fields[nome] = field

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este login já está em uso.')
        return username


class EditarSistemaUsuarioForm(forms.Form):
    nova_senha = forms.CharField(
        required=False, label='Nova senha (deixar em branco para manter)',
        min_length=6, widget=forms.PasswordInput(attrs={**_fc, 'autocomplete': 'new-password'}),
    )
    ativo = forms.BooleanField(
        required=False, label='Usuário ativo',
        widget=forms.CheckboxInput(attrs=_chk),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, field in _perm_fields().items():
            self.fields[nome] = field


# ─────────────────────────────────────────────────────────────────────────────
# PORTAL DO CLIENTE
# ─────────────────────────────────────────────────────────────────────────────

class ClienteRegistroForm(forms.Form):
    nome = forms.CharField(
        max_length=150, label='Nome Completo',
        widget=forms.TextInput(attrs={**_fc, 'placeholder': 'Seu nome completo'}),
    )
    telefone = forms.CharField(
        max_length=20, label='WhatsApp',
        widget=forms.TextInput(attrs={**_fc, 'placeholder': '(83) 99999-9999'}),
    )
    username = forms.CharField(
        max_length=150, label='Nome de usuário',
        widget=forms.TextInput(attrs={**_fc, 'placeholder': 'Ex: joao123'}),
    )
    password = forms.CharField(
        label='Senha', min_length=6,
        widget=forms.PasswordInput(attrs={**_fc, 'placeholder': 'Mínimo 6 caracteres'}),
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={**_fc, 'placeholder': 'Repita a senha'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            self.add_error('password2', 'As senhas não coincidem.')
        return cleaned


class PerfilClienteForm(forms.Form):
    nome = forms.CharField(max_length=150, label='Nome Completo', widget=forms.TextInput(attrs=_fc))
    telefone = forms.CharField(max_length=20, label='WhatsApp', widget=forms.TextInput(attrs=_fc))
    senha_atual = forms.CharField(
        required=False, label='Senha Atual (para alterar)',
        widget=forms.PasswordInput(attrs={**_fc, 'autocomplete': 'current-password'}),
    )
    nova_senha = forms.CharField(
        required=False, label='Nova Senha',
        widget=forms.PasswordInput(attrs={**_fc, 'autocomplete': 'new-password'}),
    )
    nova_senha2 = forms.CharField(
        required=False, label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs=_fc),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('nova_senha') and cleaned.get('nova_senha') != cleaned.get('nova_senha2'):
            self.add_error('nova_senha2', 'As senhas não coincidem.')
        return cleaned


class AgendamentoClienteForm(forms.Form):
    servico = forms.ModelChoiceField(
        queryset=Servico.objects.filter(ativo=True),
        label='Serviço', empty_label='— Selecione um serviço —',
        widget=forms.Select(attrs={**_fs, 'id': 'svc-select'}),
    )
    barbeiro = forms.ModelChoiceField(
        queryset=Barbeiro.objects.filter(ativo=True),
        label='Barbeiro', empty_label='— Selecione um barbeiro —',
        widget=forms.Select(attrs={**_fs, 'id': 'barb-select'}),
    )
    data_hora = forms.DateTimeField(
        label='Horário Selecionado',
        widget=forms.HiddenInput(attrs={'id': 'id_data_hora'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True,
    )
    observacoes = forms.CharField(
        required=False, label='Observações',
        widget=forms.Textarea(attrs={**_fc, 'rows': 2, 'placeholder': 'Alguma preferência?'}),
    )
