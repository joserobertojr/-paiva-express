from django.urls import path
from . import views

app_name = 'barbearia'

urlpatterns = [
    # ── AUTH ───────────────────────────────────────────────────────────────────
    path('login/', views.login_barbearia, name='login'),
    path('logout/', views.logout_barbearia, name='logout'),

    # ── DASHBOARD ──────────────────────────────────────────────────────────────
    path('', views.dashboard, name='dashboard'),

    # ── AGENDA ─────────────────────────────────────────────────────────────────
    path('agenda/', views.agenda, name='agenda'),
    path('agenda/novo/', views.novo_agendamento, name='novo_agendamento'),
    path('agenda/<int:pk>/editar/', views.editar_agendamento, name='editar_agendamento'),
    path('agenda/<int:pk>/excluir/', views.excluir_agendamento, name='excluir_agendamento'),
    path('agenda/<int:pk>/status/<str:novo_status>/', views.alterar_status, name='alterar_status'),

    # ── CLIENTES ───────────────────────────────────────────────────────────────
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/novo/', views.novo_cliente, name='novo_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),

    # ── SERVIÇOS ───────────────────────────────────────────────────────────────
    path('servicos/', views.servicos, name='servicos'),
    path('servicos/novo/', views.novo_servico, name='novo_servico'),
    path('servicos/<int:pk>/editar/', views.editar_servico, name='editar_servico'),
    path('servicos/<int:pk>/excluir/', views.excluir_servico, name='excluir_servico'),

    # ── FINANCEIRO ─────────────────────────────────────────────────────────────
    path('financeiro/', views.financeiro, name='financeiro'),
    path('financeiro/nova-saida/', views.nova_saida, name='nova_saida'),
    path('financeiro/saida/<int:pk>/excluir/', views.excluir_saida, name='excluir_saida'),

    # ── BARBEIROS ──────────────────────────────────────────────────────────────
    path('barbeiros/', views.barbeiros, name='barbeiros'),
    path('barbeiros/cadastrar/', views.cadastrar_barbeiro, name='cadastrar_barbeiro'),
    path('barbeiros/<int:pk>/editar/', views.editar_barbeiro, name='editar_barbeiro'),
    path('barbeiros/<int:pk>/excluir/', views.excluir_barbeiro, name='excluir_barbeiro'),

    # ── PLANOS ─────────────────────────────────────────────────────────────────
    path('planos/', views.planos, name='planos'),
    path('planos/novo/', views.novo_plano, name='novo_plano'),
    path('planos/<int:pk>/editar/', views.editar_plano, name='editar_plano'),
    path('planos/<int:pk>/excluir/', views.excluir_plano, name='excluir_plano'),
    path('planos/relatorio/', views.relatorio_planos, name='relatorio_planos'),

    # ── NOTIFICAÇÕES ───────────────────────────────────────────────────────────
    path('notificacoes/', views.notificacoes, name='notificacoes'),
    path('notificacoes/<int:pk>/lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),

    # ── BLOQUEIOS ──────────────────────────────────────────────────────────────
    path('bloquear-horario/', views.bloquear_horario, name='bloquear_horario'),
    path('bloquear-horario/<int:pk>/excluir/', views.excluir_bloqueio, name='excluir_bloqueio'),

    # ── CONFIGURAÇÕES — Usuários do Sistema ────────────────────────────────────
    path('configuracoes/usuarios/', views.configuracoes_usuarios, name='configuracoes_usuarios'),
    path('configuracoes/usuarios/novo/', views.configuracoes_novo_usuario, name='configuracoes_novo_usuario'),
    path('configuracoes/usuarios/<int:pk>/editar/', views.configuracoes_editar_usuario, name='configuracoes_editar_usuario'),
    path('configuracoes/usuarios/<int:pk>/excluir/', views.configuracoes_excluir_usuario, name='configuracoes_excluir_usuario'),

    # ── LEMBRETES ──────────────────────────────────────────────────────────────
    path('lembretes/', views.lembretes, name='lembretes'),
    path('lembretes/<int:pk>/marcar-enviado/', views.marcar_lembrete_enviado, name='marcar_lembrete_enviado'),

    # ── APIs JSON ──────────────────────────────────────────────────────────────
    path('api/servico/<int:pk>/preco/', views.api_preco_servico, name='api_preco_servico'),
    path('api/eventos/', views.api_eventos_calendario, name='api_eventos'),
    path('api/horarios/', views.api_horarios_disponiveis, name='api_horarios'),

    # ── PORTAL DO CLIENTE ──────────────────────────────────────────────────────
    path('cliente/login/', views.cliente_login, name='cliente_login'),
    path('cliente/registro/', views.cliente_registro, name='cliente_registro'),
    path('cliente/logout/', views.cliente_logout, name='cliente_logout'),
    path('cliente/', views.cliente_dashboard, name='cliente_dashboard'),
    path('cliente/agendar/', views.cliente_agendar, name='cliente_agendar'),
    path('cliente/meus-agendamentos/', views.cliente_meus_agendamentos, name='cliente_meus_agendamentos'),
    path('cliente/meus-agendamentos/<int:pk>/cancelar/', views.cliente_cancelar_agendamento, name='cliente_cancelar'),
    path('cliente/perfil/', views.cliente_perfil, name='cliente_perfil'),
    path('cliente/planos/', views.cliente_planos, name='cliente_planos'),
]
