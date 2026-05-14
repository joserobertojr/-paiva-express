from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Funcionario, Documento, Entregador
from .forms import FuncionarioForm, DocumentoForm, EntregadorForm

# NOVA PÁGINA INICIAL (HUB)
@login_required
def hub(request):
    return render(request, 'rh/hub.html')

# ANTIGA 'home' AGORA SE CHAMA 'lista_funcionarios'
@login_required
def lista_funcionarios(request):
    busca = request.GET.get('busca')
    if busca:
        funcionarios = Funcionario.objects.filter(
            Q(nome__icontains=busca) | Q(cpf__icontains=busca)
        )
    else:
        funcionarios = Funcionario.objects.all()
        
    documentos = Documento.objects.all() 
    # Repare que aqui nós continuamos carregando o arquivo home.html de antes
    return render(request, 'rh/home.html', {'funcionarios': funcionarios, 'documentos': documentos})

@login_required
def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios') # <-- Atualizamos o redirecionamento
    else:
        form = FuncionarioForm()
    return render(request, 'rh/cadastrar_funcionario.html', {'form': form})

@login_required
def upload_documento(request):
    if request.method == 'POST':
        # ATENÇÃO AQUI: o request.FILES é obrigatório para pegar o arquivo de verdade!
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_funcionarios')
    else:
        form = DocumentoForm()

    return render(request, 'rh/upload_documento.html', {'form': form})

@login_required
def ver_funcionario(request, id):
    # Busca o funcionário pelo ID. Se não achar, mostra erro 404.
    funcionario = get_object_or_404(Funcionario, id=id)
    # Busca também os documentos ligados apenas a este funcionário
    documentos = Documento.objects.filter(funcionario=funcionario)
    return render(request, 'rh/ver_funcionario.html', {'funcionario': funcionario, 'documentos': documentos})

@login_required
def editar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, id=id)
    if request.method == 'POST':
        # Carrega o formulário com os dados novos que vieram da tela e salva
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('ver_funcionario', id=funcionario.id)
    else:
        # Carrega o formulário preenchido com os dados atuais do banco
        form = FuncionarioForm(instance=funcionario)
    
    return render(request, 'rh/editar_funcionario.html', {'form': form, 'funcionario': funcionario})

@login_required
def excluir_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, id=id)
    if request.method == 'POST':
        funcionario.delete()
        return redirect('lista_funcionarios')

    return render(request, 'rh/excluir_funcionario.html', {'funcionario': funcionario})

@login_required
def anexar_documento(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.funcionario = funcionario  # Vincula automaticamente
            documento.save()
            return redirect('ver_funcionario', id=funcionario.id)
    else:
        # Iniciamos o formulário ocultando o campo funcionário, pois já sabemos quem é
        form = DocumentoForm(initial={'funcionario': funcionario})
    
    return render(request, 'rh/anexar_documento.html', {'form': form, 'funcionario': funcionario})

@login_required
def lista_entregadores(request):
    busca = request.GET.get('busca')
    if busca:
        entregadores = Entregador.objects.filter(
            Q(nome__icontains=busca) | Q(cpf__icontains=busca)
        )
    else:
        entregadores = Entregador.objects.all()
        
    return render(request, 'rh/lista_entregadores.html', {'entregadores': entregadores})

@login_required
def cadastrar_entregador(request):
    if request.method == 'POST':
        # OLHA A MÁGICA AQUI: Adicionamos o request.FILES
        form = EntregadorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_entregadores') 
    else:
        form = EntregadorForm()
    
    return render(request, 'rh/cadastrar_entregador.html', {'form': form})

@login_required
def ver_entregador(request, id):
    # Busca o entregador pelo ID ou retorna erro 404 se não achar
    entregador = get_object_or_404(Entregador, id=id)
    return render(request, 'rh/ver_entregador.html', {'entregador': entregador})

@login_required
def editar_entregador(request, id):
    entregador = get_object_or_404(Entregador, id=id)
    if request.method == 'POST':
        # AQUI TAMBÉM: Adicionamos o request.FILES
        form = EntregadorForm(request.POST, request.FILES, instance=entregador)
        if form.is_valid():
            form.save()
            return redirect('ver_entregador', id=entregador.id)
    else:
        form = EntregadorForm(instance=entregador)
    
    return render(request, 'rh/editar_entregador.html', {'form': form, 'entregador': entregador})

@login_required
def excluir_entregador(request, id):
    entregador = get_object_or_404(Entregador, id=id)
    if request.method == 'POST':
        entregador.delete()
        return redirect('lista_entregadores')
    
    return render(request, 'rh/excluir_entregador.html', {'entregador': entregador})