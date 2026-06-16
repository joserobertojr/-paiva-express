from django.db import models


class Cliente(models.Model):
    nome = models.CharField('Nome', max_length=120)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    cpf = models.CharField('CPF', max_length=20, blank=True, default='')
    passaporte = models.CharField('Passaporte', max_length=30, blank=True, default='')
    validade_passaporte = models.DateField('Validade do Passaporte', null=True, blank=True)
    data_nascimento = models.DateField('Data de Nascimento', null=True, blank=True)
    email = models.EmailField('E-mail', blank=True)
    cidade = models.CharField('Cidade', max_length=80, blank=True)
    foto = models.ImageField('Foto', upload_to='clientes/fotos/', null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def doc_formatado(self):
        if self.cpf:
            d = self.cpf.replace('.', '').replace('-', '')
            if len(d) == 11:
                return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}'
            return self.cpf
        return self.passaporte or '—'

    @property
    def docs_resumo(self):
        partes = []
        if self.cpf:
            partes.append(f'CPF: {self.doc_formatado}')
        if self.passaporte:
            partes.append(f'Passaporte: {self.passaporte}')
        return ' / '.join(partes) or '—'
