from django.contrib import admin
from .models import Reserva, PassageiroReserva


class PassageiroInline(admin.TabularInline):
    model = PassageiroReserva
    extra = 0


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'num_passageiros', 'valor_total', 'criado_em')
    list_filter = ('status',)
    inlines = [PassageiroInline]
