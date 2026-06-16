import datetime
from django.db import models


class CartaoAprovado(models.Model):
    BANDEIRA = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('elo', 'Elo'),
        ('amex', 'American Express'),
        ('hipercard', 'Hipercard'),
        ('outro', 'Outro'),
    ]
    STATUS = [
        ('aprovado', 'Aprovado'),
        ('pendente', 'Pendente'),
        ('cancelado', 'Cancelado'),
        ('recusado', 'Recusado'),
        ('contestado', 'Contestado'),
    ]
    PARCELAS = [(i, f'{i}x') for i in range(1, 13)]

    data        = models.DateField('Data', default=datetime.date.today)
    bandeira    = models.CharField('Bandeira', max_length=20, choices=BANDEIRA)
    titular     = models.CharField('Titular', max_length=120)
    numero      = models.CharField('Número do Cartão', max_length=19)
    validade    = models.CharField('Validade', max_length=7, help_text='MM/AAAA')
    valor       = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    cid         = models.CharField('CID', max_length=4)
    parcelas    = models.PositiveSmallIntegerField('Parcelas', choices=PARCELAS, default=1)
    origem      = models.CharField('Origem', max_length=120)
    destino     = models.CharField('Destino', max_length=120)
    status      = models.CharField('Status', max_length=20, choices=STATUS, default='aprovado')
    comprovante = models.FileField('Comprovante (PDF)', upload_to='cartoes/comprovantes/', null=True, blank=True)
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cartão Aprovado'
        verbose_name_plural = 'Cartões Aprovados'
        ordering = ['-data', '-registrado_em']

    def __str__(self):
        return f'{self.get_bandeira_display()} — {self.titular} — R$ {self.valor}'
