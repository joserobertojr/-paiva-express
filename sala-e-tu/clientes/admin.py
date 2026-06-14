from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'cpf', 'passaporte', 'cidade', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'cpf', 'passaporte')
