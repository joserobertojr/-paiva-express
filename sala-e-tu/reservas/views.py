import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.utils import timezone
from clientes.models import Cliente
from pacotes.models import Pacote
from vendedores.models import Vendedor
from .models import Reserva, PassageiroReserva


def _clientes_json():
    return json.dumps(list(
        [{'id': c.id, 'nome': c.nome, 'documento': c.doc_formatado, 'cidade': c.cidade, 'telefone': c.telefone}
         for c in Cliente.objects.filter(ativo=True)]
    ))


# ── Lista: só os cards de pacote ─────────────────────────────────────────────

@login_required
def lista(request):
    pacotes = Pacote.objects.filter(
        reservas__status__in=['pendente', 'confirmada', 'concluida']
    ).distinct().order_by('data_saida').prefetch_related(
        Prefetch('reservas',
                 queryset=Reserva.objects.exclude(status='cancelada').prefetch_related('passageiros'))
    )
    return render(request, 'reservas/lista.html', {'pacotes': pacotes})


# ── Gestão do pacote: página dedicada ────────────────────────────────────────

@login_required
def gestao_pacote(request, pk):
    pacote = get_object_or_404(Pacote, pk=pk)
    reservas = Reserva.objects.filter(pacote=pacote).exclude(status='cancelada').prefetch_related(
        Prefetch('passageiros', queryset=PassageiroReserva.objects.select_related('cliente'))
    )
    return render(request, 'reservas/gestao_pacote.html', {
        'pacote': pacote,
        'reservas': reservas,
        'clientes_json': _clientes_json(),
    })


# ── Impressão unificada do pacote ────────────────────────────────────────────

@login_required
def lista_impressao_pacote(request, pk):
    pacote = get_object_or_404(Pacote, pk=pk)
    reservas = Reserva.objects.filter(
        pacote=pacote
    ).exclude(status='cancelada').prefetch_related(
        Prefetch(
            'passageiros',
            queryset=PassageiroReserva.objects.select_related('cliente').order_by('-principal', 'cliente__nome')
        )
    ).order_by('pk')
    return render(request, 'reservas/lista_impressao.html', {
        'pacote': pacote,
        'reservas': reservas,
        'data_impressao': timezone.now(),
    })


# ── Criar reserva ────────────────────────────────────────────────────────────

@login_required
def criar(request, pacote_pk=None):
    pacotes = Pacote.objects.filter(ativo=True, vagas_disponiveis__gt=0).order_by('data_saida')
    vendedores = Vendedor.objects.filter(ativo=True)
    pacote_inicial = get_object_or_404(Pacote, pk=pacote_pk) if pacote_pk else None

    if request.method == 'POST':
        pacote_id = request.POST.get('pacote')
        vendedor_id = request.POST.get('vendedor') or None
        num_passageiros = max(1, int(request.POST.get('num_passageiros', 1)))
        observacoes = request.POST.get('observacoes', '')
        pacote = get_object_or_404(Pacote, pk=pacote_id)

        cliente_ids = [
            request.POST.get(f'cliente_{i}', '').strip()
            for i in range(1, num_passageiros + 1)
        ]
        cliente_ids = [c for c in cliente_ids if c]

        if not cliente_ids:
            messages.error(request, 'Selecione ao menos um passageiro.')
            return render(request, 'reservas/form.html', {
                'pacotes': pacotes, 'vendedores': vendedores,
                'clientes_json': _clientes_json(), 'pacote_inicial': pacote_inicial,
            })

        reserva = Reserva.objects.create(
            pacote=pacote,
            vendedor_id=vendedor_id,
            num_passageiros=len(cliente_ids),
            valor_total=pacote.valor * len(cliente_ids),
            observacoes=observacoes,
        )
        for i, cid in enumerate(cliente_ids):
            try:
                PassageiroReserva.objects.create(
                    reserva=reserva, cliente_id=int(cid), principal=(i == 0)
                )
            except Exception:
                pass

        pacote.vagas_disponiveis -= len(cliente_ids)
        pacote.save()
        messages.success(request, f'Reserva #{reserva.pk} criada!')
        return redirect('pagamentos:checkout', pk=reserva.pk)

    return render(request, 'reservas/form.html', {
        'pacotes': pacotes,
        'vendedores': vendedores,
        'clientes_json': _clientes_json(),
        'pacote_inicial': pacote_inicial,
    })


# ── Cancelar reserva ─────────────────────────────────────────────────────────

@login_required
def cancelar(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    pacote_pk = reserva.pacote.pk
    reserva.pacote.vagas_disponiveis += reserva.num_passageiros
    reserva.pacote.save()
    reserva.status = 'cancelada'
    reserva.save()
    messages.warning(request, f'Reserva #{pk} cancelada.')
    return redirect('reservas:gestao_pacote', pk=pacote_pk)


# ── Gerenciar passageiros ────────────────────────────────────────────────────

@login_required
def adicionar_passageiro(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        cid = request.POST.get('cliente_id', '').strip()
        if cid:
            try:
                PassageiroReserva.objects.create(
                    reserva=reserva, cliente_id=int(cid), principal=False
                )
                reserva.num_passageiros = reserva.passageiros.count()
                reserva.valor_total = reserva.pacote.valor * reserva.num_passageiros
                reserva.save()
                reserva.pacote.vagas_disponiveis = max(0, reserva.pacote.vagas_disponiveis - 1)
                reserva.pacote.save()
                messages.success(request, 'Passageiro adicionado!')
            except Exception as e:
                messages.error(request, f'Erro: {e}')
        else:
            messages.error(request, 'Selecione um cliente.')
    return redirect('reservas:gestao_pacote', pk=reserva.pacote.pk)


@login_required
def remover_passageiro(request, pk):
    pax = get_object_or_404(PassageiroReserva, pk=pk)
    reserva = pax.reserva
    pacote_pk = reserva.pacote.pk
    if reserva.passageiros.count() <= 1:
        messages.error(request, 'A reserva deve ter ao menos um passageiro.')
        return redirect('reservas:gestao_pacote', pk=pacote_pk)
    if pax.principal:
        proximo = reserva.passageiros.exclude(pk=pk).first()
        if proximo:
            proximo.principal = True
            proximo.save()
    reserva.pacote.vagas_disponiveis += 1
    reserva.pacote.save()
    pax.delete()
    reserva.num_passageiros = reserva.passageiros.count()
    reserva.valor_total = reserva.pacote.valor * reserva.num_passageiros
    reserva.save()
    messages.success(request, 'Passageiro removido.')
    return redirect('reservas:gestao_pacote', pk=pacote_pk)


# ── Impressão por reserva individual (usada no checkout) ─────────────────────

@login_required
def lista_impressao(request, pk):
    reserva = get_object_or_404(Reserva.objects.select_related('pacote'), pk=pk)
    passageiros = reserva.passageiros.select_related('cliente').order_by('-principal', 'cliente__nome')
    return render(request, 'reservas/lista_impressao.html', {
        'reserva': reserva,
        'passageiros': passageiros,
        'data_impressao': timezone.now(),
    })
