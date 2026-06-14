from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pacote
from .forms import PacoteForm


@login_required
def lista(request):
    pacotes = Pacote.objects.filter(ativo=True)
    return render(request, 'pacotes/lista.html', {'pacotes': pacotes})


@login_required
def criar(request):
    form = PacoteForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pacote criado com sucesso!')
        return redirect('pacotes:lista')
    return render(request, 'pacotes/form.html', {'form': form, 'titulo': 'Novo Pacote'})


@login_required
def editar(request, pk):
    pacote = get_object_or_404(Pacote, pk=pk)
    form = PacoteForm(request.POST or None, request.FILES or None, instance=pacote)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pacote atualizado!')
        return redirect('pacotes:lista')
    return render(request, 'pacotes/form.html', {'form': form, 'titulo': f'Editar: {pacote.titulo}'})


@login_required
def excluir(request, pk):
    pacote = get_object_or_404(Pacote, pk=pk)
    pacote.ativo = False
    pacote.save()
    messages.success(request, 'Pacote desativado.')
    return redirect('pacotes:lista')
