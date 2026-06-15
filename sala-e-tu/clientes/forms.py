from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'cpf', 'passaporte', 'validade_passaporte', 'data_nascimento', 'email', 'cidade']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'validade_passaporte': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('cpf') and not cleaned.get('passaporte'):
            raise forms.ValidationError('Informe ao menos um documento: CPF ou Passaporte.')
        return cleaned
