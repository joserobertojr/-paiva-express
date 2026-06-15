import datetime
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from reservas.models import Reserva
from vendedores.models import Vendedor
from core.decorators import admin_required
from core.audit import log as audit_log
from core.models import AuditLog
from .models import Pagamento, BancoPix

FORMA_LABELS = {
    'pix': 'PIX',
    'dinheiro': 'Dinheiro',
    'cartao_credito': 'Cartão de Crédito',
}


@login_required
def checkout(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    pagamentos = reserva.pagamentos.select_related('vendedor').all()
    total_pago = pagamentos.aggregate(s=Sum('valor'))['s'] or Decimal('0')
    saldo = reserva.valor_total - total_pago
    percentual = int((total_pago / reserva.valor_total * 100)) if reserva.valor_total > 0 else 0
    vendedores = Vendedor.objects.filter(ativo=True)
    bancos_pix = BancoPix.objects.filter(ativo=True)

    if request.method == 'POST':
        forma = request.POST.get('forma')
        raw = request.POST.get('valor', '0').replace(',', '.')
        try:
            valor = Decimal(raw)
        except InvalidOperation:
            valor = Decimal('0')

        parcelas = None
        if forma == 'cartao_credito':
            try:
                parcelas = int(request.POST.get('parcelas', 1))
            except (ValueError, TypeError):
                parcelas = 1

        banco_pix_id = None
        if forma == 'pix':
            banco_pix_id = request.POST.get('banco_pix') or None

        data_raw = request.POST.get('data_pagamento', '')
        try:
            data_pagamento = datetime.date.fromisoformat(data_raw) if data_raw else datetime.date.today()
        except ValueError:
            data_pagamento = datetime.date.today()

        vendedor_id = request.POST.get('vendedor') or None
        observacoes = request.POST.get('observacoes', '')

        if forma and valor > 0:
            valor_efetivo = min(valor, saldo)
            pag = Pagamento.objects.create(
                reserva=reserva,
                forma=forma,
                valor=valor_efetivo,
                parcelas=parcelas,
                banco_pix_id=banco_pix_id,
                vendedor_id=vendedor_id,
                observacoes=observacoes,
                data_pagamento=data_pagamento,
            )
            audit_log(request, AuditLog.ACAO_CRIAR, 'Pagamentos',
                      f'Registrou pagamento R$ {valor_efetivo:.2f} ({FORMA_LABELS.get(forma, forma)}) '
                      f'na reserva #{reserva.pk}')
            novo_total = reserva.pagamentos.aggregate(s=Sum('valor'))['s'] or Decimal('0')
            if novo_total >= reserva.valor_total:
                reserva.status = 'confirmada'
                reserva.save()
                messages.success(request, 'Reserva quitada e confirmada!')
            else:
                messages.success(request, f'Pagamento de R$ {valor_efetivo:.2f} registrado.')
        else:
            messages.error(request, 'Selecione a forma de pagamento e informe um valor válido.')

        return redirect('pagamentos:checkout', pk=reserva.pk)

    passageiros = reserva.passageiros.select_related('cliente').all()

    return render(request, 'pagamentos/checkout.html', {
        'reserva': reserva,
        'passageiros': passageiros,
        'pagamentos': pagamentos,
        'vendedores': vendedores,
        'bancos_pix': bancos_pix,
        'total_pago': total_pago,
        'saldo': saldo,
        'percentual': min(percentual, 100),
        'hoje': datetime.date.today().isoformat(),
    })


@login_required
def recibo(request, pk):
    pagamento = get_object_or_404(Pagamento.objects.select_related(
        'reserva__pacote', 'vendedor'
    ), pk=pk)
    passageiro_principal = pagamento.reserva.passageiro_principal
    return render(request, 'pagamentos/recibo.html', {
        'pagamento': pagamento,
        'reserva': pagamento.reserva,
        'passageiro_principal': passageiro_principal,
        'data_impressao': timezone.now(),
    })


@login_required
def lista(request):
    pagamentos = Pagamento.objects.select_related(
        'reserva__pacote', 'vendedor'
    ).prefetch_related(
        'reserva__passageiros__cliente'
    ).order_by('-registrado_em')
    return render(request, 'pagamentos/lista.html', {'pagamentos': pagamentos})


@login_required
@admin_required
def relatorios(request):
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    qs = Pagamento.objects.select_related('reserva__pacote', 'vendedor').prefetch_related(
        'reserva__passageiros__cliente'
    )

    if data_inicio:
        qs = qs.filter(registrado_em__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(registrado_em__date__lte=data_fim)

    total_geral = qs.aggregate(s=Sum('valor'))['s'] or Decimal('0')

    totais_forma = qs.values('forma').annotate(
        total=Sum('valor'), quantidade=Count('id')
    ).order_by('-total')

    totais_vendedor = qs.values('vendedor__nome').annotate(
        total=Sum('valor'), quantidade=Count('id')
    ).order_by('-total')

    pagamentos = qs.order_by('-registrado_em')

    return render(request, 'relatorios/index.html', {
        'pagamentos': pagamentos,
        'totais_forma': totais_forma,
        'totais_vendedor': totais_vendedor,
        'total_geral': total_geral,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'FORMA_LABELS': FORMA_LABELS,
    })
