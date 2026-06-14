from django.db import models
from django.contrib.auth.models import User


class Vendedor(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vendedor', verbose_name='Usuário do sistema'
    )
    nome = models.CharField('Nome', max_length=100)
    telefone = models.CharField('Telefone', max_length=20)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def tem_acesso(self):
        return self.user_id is not None
