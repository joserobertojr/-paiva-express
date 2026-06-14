from django import forms
from .models import Pagamento


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ['forma', 'parcelas', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }
