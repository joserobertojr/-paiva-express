from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('configuracoes/usuario/novo/', views.conf_novo_usuario, name='conf_novo_usuario'),
    path('configuracoes/usuario/<int:vendedor_pk>/editar/', views.conf_editar_usuario, name='conf_editar_usuario'),
    path('configuracoes/usuario/<int:vendedor_pk>/excluir/', views.conf_excluir_usuario, name='conf_excluir_usuario'),
    path('configuracoes/logs/', views.conf_logs, name='conf_logs'),
    path('configuracoes/bancos/novo/', views.conf_banco_novo, name='conf_banco_novo'),
    path('configuracoes/bancos/<int:pk>/editar/', views.conf_banco_editar, name='conf_banco_editar'),
    path('configuracoes/bancos/<int:pk>/excluir/', views.conf_banco_excluir, name='conf_banco_excluir'),
]
