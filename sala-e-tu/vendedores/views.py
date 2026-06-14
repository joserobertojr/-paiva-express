from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vendedor
from .forms import VendedorForm


@login_required
def lista(request):
    vendedores = Vendedor.objects.filter(ativo=True)
    return render(request, 'vendedores/lista.html', {'vendedores': vendedores})


@login_required
def cadastrar(request):
    form = VendedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Vendedor cadastrado com sucesso!')
        return redirect('vendedores:lista')
    return render(request, 'vendedores/form.html', {'form': form, 'titulo': 'Cadastrar Vendedor'})


@login_required
def editar(request, pk):
    v = get_object_or_404(Vendedor, pk=pk)
    form = VendedorForm(request.POST or None, instance=v)
    if form.is_valid():
        form.save()
        messages.success(request, 'Vendedor atualizado!')
        return redirect('vendedores:lista')
    return render(request, 'vendedores/form.html', {'form': form, 'titulo': f'Editar: {v.nome}'})


@login_required
def excluir(request, pk):
    v = get_object_or_404(Vendedor, pk=pk)
    v.ativo = False
    v.save()
    messages.success(request, 'Vendedor removido.')
    return redirect('vendedores:lista')
