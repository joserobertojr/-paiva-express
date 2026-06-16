from django import forms
from .models import CartaoAprovado


class CartaoAprovadoForm(forms.ModelForm):
    class Meta:
        model = CartaoAprovado
        fields = [
            'data', 'bandeira', 'titular', 'numero', 'validade',
            'valor', 'cid', 'parcelas', 'origem', 'destino', 'status', 'comprovante',
        ]
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
        }
