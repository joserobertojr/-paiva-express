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
    pags_financeiros = pagamentos.exclude(forma='gratuito')
    totals = pags_financeiros.aggregate(s=Sum('valor'), d=Sum('desconto'))
    total_pago = totals['s'] or Decimal('0')
    total_desconto = totals['d'] or Decimal('0')
    tem_gratuito = pagamentos.filter(forma='gratuito').exists()
    saldo = Decimal('0') if tem_gratuito else reserva.valor_total - total_pago - total_desconto
    percentual = int(((total_pago + total_desconto) / reserva.valor_total * 100)) if reserva.valor_total > 0 else 0
    if tem_gratuito:
        percentual = 100
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

        comprovante = request.FILES.get('comprovante') or None

        if forma == 'gratuito':
            # Quita a reserva sem valor financeiro
            Pagamento.objects.create(
                reserva=reserva,
                forma='gratuito',
                valor=Decimal('0'),
                data_pagamento=data_pagamento,
                vendedor_id=vendedor_id,
                observacoes=observacoes or 'Gratuito',
                comprovante=comprovante,
            )
            reserva.status = 'confirmada'
            reserva.save()
            audit_log(request, AuditLog.ACAO_CRIAR, 'Pagamentos',
                      f'Marcou reserva #{reserva.pk} como gratuita')
            messages.success(request, 'Reserva marcada como gratuita e confirmada!')

        elif forma and valor > 0:
            valor_efetivo = min(valor, saldo)
            Pagamento.objects.create(
                reserva=reserva,
                forma=forma,
                valor=valor_efetivo,
                parcelas=parcelas,
                banco_pix_id=banco_pix_id,
                vendedor_id=vendedor_id,
                observacoes=observacoes,
                data_pagamento=data_pagamento,
                desconto=desconto,
                comprovante=comprovante,
            )
            audit_log(request, AuditLog.ACAO_CRIAR, 'Pagamentos',
                      f'Registrou pagamento R$ {valor_efetivo:.2f} ({FORMA_LABELS.get(forma, forma)}) '
                      f'na reserva #{reserva.pk}')
            novo = reserva.pagamentos.exclude(forma='gratuito').aggregate(s=Sum('valor'), d=Sum('desconto'))
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


@login_required
def pagamento_editar(request, pk):
    pagamento = get_object_or_404(Pagamento.objects.select_related('reserva'), pk=pk)
    reserva = pagamento.reserva
    bancos_pix = BancoPix.objects.filter(ativo=True)
    vendedores = Vendedor.objects.filter(ativo=True)

    if request.method == 'POST':
        forma = request.POST.get('forma', pagamento.forma)
        raw = request.POST.get('valor', '0').replace(',', '.')
        try:
            valor = Decimal(raw)
        except InvalidOperation:
            valor = pagamento.valor

        parcelas = pagamento.parcelas
        if forma == 'cartao_credito':
            try:
                parcelas = int(request.POST.get('parcelas', 1))
            except (ValueError, TypeError):
                parcelas = 1
        else:
            parcelas = None

        banco_pix_id = None
        if forma == 'pix':
            banco_pix_id = request.POST.get('banco_pix') or None

        data_raw = request.POST.get('data_pagamento', '')
        try:
            data_pagamento = datetime.date.fromisoformat(data_raw) if data_raw else pagamento.data_pagamento
        except ValueError:
            data_pagamento = pagamento.data_pagamento

        try:
            desconto = Decimal(request.POST.get('desconto', '0').replace(',', '.'))
            if desconto < 0:
                desconto = Decimal('0')
        except InvalidOperation:
            desconto = pagamento.desconto

        pagamento.forma = forma
        pagamento.valor = valor if forma != 'gratuito' else Decimal('0')
        pagamento.parcelas = parcelas
        pagamento.banco_pix_id = banco_pix_id
        pagamento.vendedor_id = request.POST.get('vendedor') or None
        pagamento.observacoes = request.POST.get('observacoes', '')
        pagamento.data_pagamento = data_pagamento
        pagamento.desconto = desconto if forma != 'gratuito' else Decimal('0')

        if 'comprovante' in request.FILES:
            pagamento.comprovante = request.FILES['comprovante']

        pagamento.save()
        audit_log(request, AuditLog.ACAO_EDITAR, 'Pagamentos',
                  f'Editou pagamento #{pagamento.pk} da reserva #{reserva.pk}')
        messages.success(request, 'Pagamento atualizado.')
        return redirect('pagamentos:checkout', pk=reserva.pk)

    return render(request, 'pagamentos/editar.html', {
        'pagamento': pagamento,
        'reserva': reserva,
        'bancos_pix': bancos_pix,
        'vendedores': vendedores,
    })


@login_required
def pagamento_excluir(request, pk):
    pagamento = get_object_or_404(Pagamento.objects.select_related('reserva'), pk=pk)
    reserva = pagamento.reserva
    if request.method == 'POST':
        pagamento.delete()
        # Se a reserva não tem mais pagamentos gratuitos e saldo > 0, volta p/ pendente
        if not reserva.pagamentos.filter(forma='gratuito').exists():
            pags = reserva.pagamentos.exclude(forma='gratuito').aggregate(s=Sum('valor'), d=Sum('desconto'))
            total = (pags['s'] or Decimal('0')) + (pags['d'] or Decimal('0'))
            if total < reserva.valor_total:
                reserva.status = 'pendente'
                reserva.save()
        audit_log(request, AuditLog.ACAO_EXCLUIR, 'Pagamentos',
                  f'Excluiu pagamento #{pk} da reserva #{reserva.pk}')
        messages.success(request, 'Pagamento excluído.')
        return redirect('pagamentos:checkout', pk=reserva.pk)

    return render(request, 'pagamentos/confirmar_exclusao.html', {
        'pagamento': pagamento,
        'reserva': reserva,
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

    qs = Pagamento.objects.exclude(forma='gratuito').select_related('reserva__pacote', 'vendedor', 'banco_pix').prefetch_related(
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
