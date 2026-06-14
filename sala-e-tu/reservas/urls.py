from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nova/', views.criar, name='criar'),
    path('nova/pacote/<int:pacote_pk>/', views.criar, name='criar_para_pacote'),
    path('pacote/<int:pk>/', views.gestao_pacote, name='gestao_pacote'),
    path('pacote/<int:pk>/imprimir/', views.lista_impressao_pacote, name='lista_impressao_pacote'),
    path('<int:pk>/cancelar/', views.cancelar, name='cancelar'),
    path('<int:pk>/adicionar-passageiro/', views.adicionar_passageiro, name='adicionar_passageiro'),
    path('passageiro/<int:pk>/remover/', views.remover_passageiro, name='remover_passageiro'),
    path('<int:pk>/lista-impressao/', views.lista_impressao, name='lista_impressao'),
]
