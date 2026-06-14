from django.contrib import admin
from .models import Pagamento


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'forma', 'valor', 'registrado_em')
    list_filter = ('forma',)
