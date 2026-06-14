from django.contrib import admin
from .models import Pacote


@admin.register(Pacote)
class PacoteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'destino', 'data_saida', 'data_retorno', 'valor', 'vagas_disponiveis', 'ativo')
    list_filter = ('ativo', 'data_saida')
    search_fields = ('titulo', 'destino')
