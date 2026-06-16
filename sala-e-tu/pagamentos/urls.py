from django.urls import path
from . import views

app_name = 'pagamentos'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('checkout/<int:pk>/', views.checkout, name='checkout'),
    path('recibo/<int:pk>/', views.recibo, name='recibo'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('<int:pk>/editar/', views.pagamento_editar, name='editar'),
    path('<int:pk>/excluir/', views.pagamento_excluir, name='excluir'),
]
