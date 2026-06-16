from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CartaoAprovado
from .forms import CartaoAprovadoForm


@login_required
def lista(request):
    origem = request.GET.get('origem', '')
    cartoes = CartaoAprovado.objects.all()
    if origem:
        cartoes = cartoes.filter(origem__icontains=origem)
    form = CartaoAprovadoForm()
    if request.method == 'POST' and 'novo' in request.POST:
        form = CartaoAprovadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cartão registrado com sucesso!')
            return redirect('cartoes:lista')
    return render(request, 'cartoes/lista.html', {'cartoes': cartoes, 'form': form, 'origem': origem})


@login_required
def editar(request, pk):
    cartao = get_object_or_404(CartaoAprovado, pk=pk)
    form = CartaoAprovadoForm(
        request.POST or None,
        request.FILES if request.method == 'POST' else None,
        instance=cartao,
    )
    if form.is_valid():
        form.save()
        messages.success(request, 'Registro atualizado!')
        return redirect('cartoes:lista')
    return render(request, 'cartoes/form.html', {'form': form, 'titulo': 'Editar Cartão', 'cartao': cartao})


@login_required
def excluir(request, pk):
    cartao = get_object_or_404(CartaoAprovado, pk=pk)
    if request.method == 'POST':
        cartao.delete()
        messages.success(request, 'Registro removido.')
    return redirect('cartoes:lista')
