from django import forms
from .models import Funcionario, Documento, Entregador

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        # O '__all__' diz para o Django pegar todos os campos do models.py, exceto a data_cadastro
        exclude = ['data_cadastro'] 
        
        widgets = {
            'registro_interno': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            # Define o campo de data com um seletor de calendário (type="date")
            'data_admissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            
            # Endereço
            'cep': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_cep'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_endereco'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_estado'}),
            
            # Dados Bancários
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['funcionario', 'titulo', 'arquivo']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class EntregadorForm(forms.ModelForm):
    class Meta:
        model = Entregador
        exclude = ['data_cadastro']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            # Usamos os mesmos IDs para o Javascript já aplicar a máscara!
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_cpf'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_telefone'}),
            'cnh': forms.TextInput(attrs={'class': 'form-control'}),
            'veiculo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Moto Honda CG 160'}),
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }