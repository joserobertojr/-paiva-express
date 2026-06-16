from django.db import models
from clientes.models import Cliente
from pacotes.models import Pacote


class Reserva(models.Model):
    STATUS = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('concluida', 'Concluída'),
    ]

    pacote = models.ForeignKey(Pacote, on_delete=models.PROTECT, related_name='reservas', verbose_name='Pacote')
    vendedor = models.ForeignKey(
        'vendedores.Vendedor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reservas', verbose_name='Vendedor'
    )
    num_passageiros = models.PositiveIntegerField('Nº de Passageiros', default=1)
    valor_total = models.DecimalField('Valor Total', max_digits=10, decimal_places=2, default=0)
    status = models.CharField('Status', max_length=15, choices=STATUS, default='pendente')
    observacoes = models.TextField('Observações', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-criado_em']

    def __str__(self):
        return f'Reserva #{self.pk} — {self.pacote.titulo}'

    @property
    def passageiro_principal(self):
        return self.passageiros.filter(principal=True).select_related('cliente').first()

    @property
    def total_pago(self):
        from django.db.models import Sum
        return self.pagamentos.exclude(forma='gratuito').aggregate(s=Sum('valor'))['s'] or 0

    @property
    def eh_gratuito(self):
        return self.pagamentos.filter(forma='gratuito').exists()

    @property
    def saldo_devedor(self):
        if self.eh_gratuito:
            return 0
        return self.valor_total - self.total_pago


class PassageiroReserva(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='passageiros')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='passagens')
    principal = models.BooleanField('Passageiro Principal', default=False)

    class Meta:
        verbose_name = 'Passageiro'
        verbose_name_plural = 'Passageiros'
        ordering = ['-principal', 'cliente__nome']

    def __str__(self):
        return f'{self.cliente.nome} {"(Principal)" if self.principal else ""}'
