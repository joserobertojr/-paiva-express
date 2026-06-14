from django import forms
from .models import Reserva
from clientes.models import Cliente
from pacotes.models import Pacote


class ReservaForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(ativo=True),
        label='Cliente',
        empty_label='-- Selecione um cliente --',
    )
    pacote = forms.ModelChoiceField(
        queryset=Pacote.objects.filter(ativo=True, vagas_disponiveis__gt=0),
        label='Pacote',
        empty_label='-- Selecione um pacote --',
    )

    class Meta:
        model = Reserva
        fields = ['cliente', 'pacote', 'num_passageiros', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
