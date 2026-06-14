from django.urls import path
from . import views

app_name = 'vendedores'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('novo/', views.cadastrar, name='cadastrar'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/excluir/', views.excluir, name='excluir'),
]
