import datetime
from django.db import models
from reservas.models import Reserva


class BancoPix(models.Model):
    nome = models.CharField('Nome do Banco', max_length=100)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Banco PIX'
        verbose_name_plural = 'Bancos PIX'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Pagamento(models.Model):
    FORMA = [
        ('pix', 'PIX'),
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('gratuito', 'Gratuito'),
    ]
    PARCELAS = [(i, f'{i}x') for i in range(1, 13)]

    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagamentos')
    forma = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA)
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    parcelas = models.PositiveSmallIntegerField('Parcelas', choices=PARCELAS, default=1, null=True, blank=True)
    banco_pix = models.ForeignKey(
        BancoPix, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pagamentos', verbose_name='Banco PIX'
    )
    vendedor = models.ForeignKey(
        'vendedores.Vendedor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pagamentos_recebidos', verbose_name='Vendedor Responsável'
    )
    desconto = models.DecimalField('Desconto (R$)', max_digits=10, decimal_places=2, default=0)
    observacoes = models.TextField('Observações', blank=True)
    data_pagamento = models.DateField('Data do Pagamento', default=datetime.date.today)
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['registrado_em']

    def __str__(self):
        return f'{self.get_forma_display()} — R$ {self.valor}'
