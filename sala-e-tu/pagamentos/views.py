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
    pagamentos = reserva.pagamentos.select_related('vendedor', 'banco_pix').all()
    totals = pagamentos.aggregate(s=Sum('valor'), d=Sum('desconto'))
    total_pago = totals['s'] or Decimal('0')
    total_desconto = totals['d'] or Decimal('0')
    saldo = reserva.valor_total - total_pago - total_desconto
    percentual = int(((total_pago + total_desconto) / reserva.valor_total * 100)) if reserva.valor_total > 0 else 0
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
        try:
            desconto = Decimal(request.POST.get('desconto', '0').replace(',', '.'))
            if desconto < 0:
                desconto = Decimal('0')
        except InvalidOperation:
            desconto = Decimal('0')

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
                desconto=desconto,
            )
            audit_log(request, AuditLog.ACAO_CRIAR, 'Pagamentos',
                      f'Registrou pagamento R$ {valor_efetivo:.2f} ({FORMA_LABELS.get(forma, forma)}) '
                      f'na reserva #{reserva.pk}')
            novo = reserva.pagamentos.aggregate(s=Sum('valor'), d=Sum('desconto'))
            novo_total = (novo['s'] or Decimal('0')) + (novo['d'] or Decimal('0'))
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


MESES_PT = {
    1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril',
    5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto',
    9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro',
}

@login_required
def lista(request):
    # Anos disponíveis
    anos = sorted(
        {p.year for p in Pagamento.objects.dates('data_pagamento', 'year')},
        reverse=True,
    )

    def _int(val, default=0):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    ano_sel = _int(request.GET.get('ano'), 0)
    mes_sel = _int(request.GET.get('mes'), 0)
    dia_sel = _int(request.GET.get('dia'), 0)

    # Queryset filtrado
    qs = Pagamento.objects.select_related(
        'reserva__pacote', 'vendedor', 'banco_pix'
    ).prefetch_related('reserva__passageiros__cliente')

    if ano_sel:
        qs = qs.filter(data_pagamento__year=ano_sel)
    if mes_sel:
        qs = qs.filter(data_pagamento__month=mes_sel)
    if dia_sel:
        qs = qs.filter(data_pagamento__day=dia_sel)

    qs = qs.order_by('-data_pagamento', '-registrado_em')

    from django.db.models import Sum as _Sum
    total = qs.aggregate(t=_Sum('valor'))['t'] or 0

    return render(request, 'pagamentos/lista.html', {
        'pagamentos': qs,
        'anos': anos,
        'ano_sel': ano_sel,
        'mes_sel': mes_sel,
        'dia_sel': dia_sel,
        'total': total,
        'meses_lista': list(MESES_PT.items()),
        'dias': range(1, 32),
    })


@login_required
@admin_required
def relatorios(request):
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    qs = Pagamento.objects.select_related('reserva__pacote', 'vendedor', 'banco_pix').prefetch_related(
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
