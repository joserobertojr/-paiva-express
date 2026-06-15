from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import (Agendamento, Barbeiro, Cliente, GradeHorario,
                     HorarioBloqueado, Notificacao, Plano, Saida, Servico)


# ─────────────────────────────────────────────────────────────────────────────
# INLINE: Grade de horários dentro do Admin de Barbeiro
# ─────────────────────────────────────────────────────────────────────────────

class GradeHorarioInline(admin.TabularInline):
    model = GradeHorario
    extra = 0
    fields = ['dia_semana', 'hora_inicio', 'hora_fim', 'ativo']
    verbose_name = 'Turno'
    verbose_name_plural = 'Grade de Horários'


# ─────────────────────────────────────────────────────────────────────────────
# BARBEIRO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Barbeiro)
class BarbeiroAdmin(admin.ModelAdmin):
    list_display = ['nome', 'whatsapp', 'data_nascimento', 'foto_thumb', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'whatsapp']
    list_editable = ['ativo']
    inlines = [GradeHorarioInline]

    @admin.display(description='Foto')
    def foto_thumb(self, obj):
        if obj.foto_perfil:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">',
                obj.foto_perfil.url,
            )
        return format_html(
            '<span style="display:inline-block;width:36px;height:36px;border-radius:50%;'
            'background:#FFD700;text-align:center;line-height:36px;font-weight:700;color:#000;">'
            '{}</span>', obj.nome[0].upper()
        )


# ─────────────────────────────────────────────────────────────────────────────
# GRADE DE HORÁRIOS (acesso independente para filtros avançados)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(GradeHorario)
class GradeHorarioAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'dia_semana_label', 'hora_inicio', 'hora_fim', 'ativo']
    list_filter = ['barbeiro', 'ativo', 'dia_semana']
    list_editable = ['ativo']

    @admin.display(description='Dia', ordering='dia_semana')
    def dia_semana_label(self, obj):
        return obj.get_dia_semana_display()


# ─────────────────────────────────────────────────────────────────────────────
# PLANO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco_mensal', 'cor_preview', 'num_servicos', 'num_clientes', 'ativo']
    list_filter = ['ativo']
    filter_horizontal = ['servicos']
    search_fields = ['nome']

    @admin.display(description='Cor')
    def cor_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:24px;height:24px;border-radius:4px;'
            'background:{};border:1px solid #ccc;"></span>', obj.cor
        )

    @admin.display(description='Nº Serviços')
    def num_servicos(self, obj):
        return obj.servicos.count()

    @admin.display(description='Clientes')
    def num_clientes(self, obj):
        return obj.clientes.count()


# ─────────────────────────────────────────────────────────────────────────────
# SERVIÇO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao_minutos', 'em_planos', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']

    @admin.display(description='Planos que incluem')
    def em_planos(self, obj):
        nomes = ', '.join(obj.planos.values_list('nome', flat=True))
        return nomes or '—'


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTE — colunas: Nome | Telefone | Plano
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    # Requisito: apenas Nome | Telefone | Plano
    list_display = ['nome', 'telefone', 'plano_nome']
    search_fields = ['nome', 'telefone']
    list_filter = ['plano']

    @admin.display(description='Plano', ordering='plano__nome')
    def plano_nome(self, obj):
        if not obj.plano:
            return format_html('<span style="color:#aaa;">Não</span>')
        return format_html(
            '<span style="background:{};color:#000;padding:2px 8px;'
            'border-radius:10px;font-size:.75rem;font-weight:700;">{}</span>',
            obj.plano.cor, obj.plano.nome,
        )

    fieldsets = (
        ('Dados do Cliente', {'fields': ('nome', 'telefone', 'data_nascimento')}),
        ('Plano de Assinatura', {'fields': ('plano',)}),
        ('Acesso ao Portal', {'fields': ('usuario',), 'classes': ('collapse',)}),
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGENDAMENTO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'barbeiro', 'servico', 'data_hora', 'status', 'valor_cobrado', 'coberto_plano']
    list_filter = ['status', 'barbeiro', 'data_hora']
    search_fields = ['cliente__nome', 'barbeiro__nome']
    date_hierarchy = 'data_hora'
    list_editable = ['status']

    @admin.display(description='Plano?', boolean=True)
    def coberto_plano(self, obj):
        return obj.servico_coberto_pelo_plano()


# ─────────────────────────────────────────────────────────────────────────────
# HORÁRIO BLOQUEADO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(HorarioBloqueado)
class HorarioBloqueadoAdmin(admin.ModelAdmin):
    list_display = ['barbeiro', 'data_inicio', 'data_fim', 'motivo']
    list_filter = ['barbeiro']


# ─────────────────────────────────────────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Saida)
class SaidaAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'valor', 'data', 'categoria', 'registrado_por']
    list_filter = ['categoria', 'data']
    date_hierarchy = 'data'


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'mensagem', 'lida', 'criado_em']
    list_filter = ['lida', 'tipo']
    list_editable = ['lida']


# ─────────────────────────────────────────────────────────────────────────────
# USUÁRIOS DO SISTEMA (Django Admin nativo — sem alterações)
# A gestão de usuários e grupos é feita pelo módulo Configurações do sistema.
# ─────────────────────────────────────────────────────────────────────────────
