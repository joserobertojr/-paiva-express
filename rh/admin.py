from django.contrib import admin
from .models import Funcionario, Documento, Entregador


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('registro_interno', 'nome', 'cargo', 'data_admissao', 'cidade')
    list_filter = ('cargo', 'cidade', 'estado')
    search_fields = ('nome', 'cpf', 'registro_interno', 'email')
    ordering = ('nome',)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'funcionario', 'data_upload')
    list_filter = ('data_upload',)
    search_fields = ('titulo', 'funcionario__nome')
    ordering = ('-data_upload',)


@admin.register(Entregador)
class EntregadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'veiculo', 'placa', 'cnh', 'ativo')
    list_filter = ('ativo', 'veiculo')
    search_fields = ('nome', 'cpf', 'placa')
    ordering = ('nome',)
