from django import forms
from .models import Pacote


class PacoteForm(forms.ModelForm):
    class Meta:
        model = Pacote
        fields = [
            'titulo', 'destino', 'descricao',
            'data_saida', 'data_retorno', 'valor',
            'vagas_totais', 'vagas_disponiveis',
            'inclui', 'nao_inclui', 'imagem', 'ativo',
        ]
        widgets = {
            'data_saida': forms.DateInput(attrs={'type': 'date'}),
            'data_retorno': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'inclui': forms.Textarea(attrs={'rows': 3}),
            'nao_inclui': forms.Textarea(attrs={'rows': 3}),
        }
