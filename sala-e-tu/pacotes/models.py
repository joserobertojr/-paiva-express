from django.db import models


class Pacote(models.Model):
    titulo = models.CharField('Título', max_length=120)
    destino = models.CharField('Destino', max_length=100)
    descricao = models.TextField('Descrição')
    data_saida = models.DateField('Data de Saída')
    data_retorno = models.DateField('Data de Retorno')
    valor = models.DecimalField('Valor (R$)', max_digits=10, decimal_places=2)
    vagas_totais = models.PositiveIntegerField('Vagas Totais', default=20)
    vagas_disponiveis = models.PositiveIntegerField('Vagas Disponíveis', default=20)
    inclui = models.TextField('O que inclui', blank=True)
    nao_inclui = models.TextField('Não inclui', blank=True)
    imagem = models.ImageField('Imagem', upload_to='pacotes/', blank=True, null=True)
    ativo = models.BooleanField('Ativo', default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pacote'
        verbose_name_plural = 'Pacotes'
        ordering = ['data_saida']

    def __str__(self):
        return f'{self.titulo} → {self.destino}'

    @property
    def duracao_dias(self):
        return (self.data_retorno - self.data_saida).days

    @property
    def lotado(self):
        return self.vagas_disponiveis <= 0
