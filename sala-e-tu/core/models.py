from django.db import models
from django.contrib.auth.models import User

ROLE_ADMIN = 'admin'
ROLE_VENDEDOR = 'vendedor'

ROLES = [
    (ROLE_ADMIN, 'Administrador'),
    (ROLE_VENDEDOR, 'Vendedor'),
]

SECOES = [
    ('clientes',      'Clientes'),
    ('reservas',      'Reservas'),
    ('pagamentos',    'Pagamentos'),
    ('cartoes',       'Cartões Aprovados'),
    ('pacotes',       'Pacotes'),
    ('vendedores',    'Vendedores'),
    ('relatorios',    'Relatórios'),
    ('configuracoes', 'Configurações'),
]


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    role = models.CharField('Perfil', max_length=20, choices=ROLES, default=ROLE_VENDEDOR)

    # Permissões granulares (ignoradas quando role=admin)
    perm_clientes      = models.BooleanField('Clientes', default=True)
    perm_reservas      = models.BooleanField('Reservas', default=True)
    perm_pagamentos    = models.BooleanField('Pagamentos', default=True)
    perm_cartoes       = models.BooleanField('Cartões Aprovados', default=False)
    perm_pacotes       = models.BooleanField('Pacotes', default=False)
    perm_vendedores    = models.BooleanField('Vendedores', default=False)
    perm_relatorios    = models.BooleanField('Relatórios', default=False)
    perm_configuracoes = models.BooleanField('Configurações', default=False)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def eh_admin(self):
        return self.role == ROLE_ADMIN or self.user.is_superuser

    def pode(self, secao):
        if self.eh_admin:
            return True
        return bool(getattr(self, f'perm_{secao}', False))

    def perms_dict(self):
        if self.eh_admin:
            return {s: True for s, _ in SECOES}
        return {s: getattr(self, f'perm_{s}', False) for s, _ in SECOES}


class AuditLog(models.Model):
    ACAO_LOGIN   = 'login'
    ACAO_CRIAR   = 'criar'
    ACAO_EDITAR  = 'editar'
    ACAO_EXCLUIR = 'excluir'
    ACAO_ACESSO  = 'acesso'

    ACOES = [
        (ACAO_LOGIN,   'Login'),
        (ACAO_CRIAR,   'Criação'),
        (ACAO_EDITAR,  'Edição'),
        (ACAO_EXCLUIR, 'Exclusão'),
        (ACAO_ACESSO,  'Acesso'),
    ]

    usuario   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acao      = models.CharField(max_length=20, choices=ACOES)
    modulo    = models.CharField(max_length=60)
    descricao = models.TextField()
    ip        = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.usuario} — {self.acao} — {self.modulo}'
