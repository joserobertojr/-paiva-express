from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rh import views

urlpatterns = [
    path('barbearia/', include('barbearia.urls', namespace='barbearia')),

    path('admin/', admin.site.urls),
    path('contas/', include('django.contrib.auth.urls')),
    
    # O caminho vazio '' agora abre o HUB
    path('', views.hub, name='hub'),
    # A lista de funcionários ganhou um endereço próprio
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('entregadores/', views.lista_entregadores, name='lista_entregadores'),
    path('entregadores/novo/', views.cadastrar_entregador, name='cadastrar_entregador'),
    path('entregadores/<int:id>/', views.ver_entregador, name='ver_entregador'),
    path('entregadores/<int:id>/editar/', views.editar_entregador, name='editar_entregador'),
    path('entregadores/<int:id>/excluir/', views.excluir_entregador, name='excluir_entregador'),
    
    path('cadastrar-funcionario/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('upload-documento/', views.upload_documento, name='upload_documento'),
    
    # NOVAS ROTAS AQUI:
    path('funcionario/<int:id>/', views.ver_funcionario, name='ver_funcionario'),
    path('funcionario/<int:id>/editar/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionario/<int:id>/excluir/', views.excluir_funcionario, name='excluir_funcionario'),
    path('funcionario/<int:funcionario_id>/anexar/', views.anexar_documento, name='anexar_documento'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)