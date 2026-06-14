from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.audit import log as audit_log
from core.models import AuditLog
from .models import Cliente
from .forms import ClienteForm


@login_required
def lista(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(ativo=True)
    if q:
        clientes = clientes.filter(nome__icontains=q)
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'q': q})


@login_required
def cadastrar(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        cliente = form.save()
        audit_log(request, AuditLog.ACAO_CRIAR, 'Clientes', f'Cadastrou cliente: {cliente.nome}')
        messages.success(request, 'Cliente cadastrado com sucesso!')
        return redirect('clientes:lista')
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Novo Cliente'})


@login_required
def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        audit_log(request, AuditLog.ACAO_EDITAR, 'Clientes', f'Editou cliente: {cliente.nome}')
        messages.success(request, 'Cliente atualizado!')
        return redirect('clientes:lista')
    return render(request, 'clientes/form.html', {'form': form, 'titulo': f'Editar: {cliente.nome}'})


@login_required
def excluir(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    nome = cliente.nome
    cliente.ativo = False
    cliente.save()
    audit_log(request, AuditLog.ACAO_EXCLUIR, 'Clientes', f'Removeu cliente: {nome}')
    messages.success(request, 'Cliente removido.')
    return redirect('clientes:lista')


def buscar_ajax(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(nome__icontains=q, ativo=True)[:10]
    data = []
    for c in clientes:
        data.append({
            'id': c.id,
            'nome': c.nome,
            'documento': c.doc_formatado,
            'cidade': c.cidade,
            'telefone': c.telefone,
        })
    return JsonResponse({'clientes': data})
