from django.contrib import admin
from .models import Vendedor


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'ativo', 'criado_em')
    search_fields = ('nome',)
