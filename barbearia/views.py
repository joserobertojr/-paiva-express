import calendar
import json
from datetime import date, datetime, timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import (FUNCIONALIDADES, AgendamentoClienteForm, AgendamentoForm,
                    BarbeiroForm, ClienteForm, ClienteRegistroForm,
                    EditarSistemaUsuarioForm, GradeHorarioFormSet,
                    HorarioBloqueadoForm, PerfilClienteForm, PlanoForm,
                    SaidaForm, ServicoForm, SistemaUsuarioForm)
from .models import (Agendamento, Barbeiro, Cliente, GradeHorario,
                     HorarioBloqueado, Notificacao, PermissaoUsuario, Plano,
                     Saida, Servico)
from .utils import gerar_slots_disponiveis


# ─────────────────────────────────────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────────────────────────────────────

def _get_perm(user) -> 'PermissaoUsuario | None':
    """Retorna PermissaoUsuario do usuário, ou None se superusuário/não tem."""
    if user.is_superuser:
        return None  # superusuário tem tudo, bypassa verificação
    try:
        return user.permissao
    except Exception:
        return False  # False indica sem permissão alguma


def _is_sistema(user) -> bool:
    """True para superusuário ou usuário com PermissaoUsuario cadastrado."""
    if user.is_superuser:
        return True
    return hasattr(user, 'permissao')


def _tem_acesso(user, funcionalidade: str) -> bool:
    """True se o usuário tem acesso à funcionalidade específica."""
    if user.is_superuser:
        return True
    try:
        return user.permissao.tem_acesso(funcionalidade)
    except Exception:
        return False


def _staff_required(view):
    """Bloqueia usuários sem acesso ao sistema (nem superusuário nem PermissaoUsuario)."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('barbearia:login')
        if hasattr(request.user, 'cliente_perfil'):
            return redirect('barbearia:cliente_dashboard')
        if not _is_sistema(request.user):
            return redirect('barbearia:login')
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


def _perm_required(funcionalidade: str):
    """Decorator factory — exige permissão para a funcionalidade dada."""
    def decorator(view):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('barbearia:login')
            if hasattr(request.user, 'cliente_perfil'):
                return redirect('barbearia:cliente_dashboard')
            if not _is_sistema(request.user):
                return redirect('barbearia:login')
            if not _tem_acesso(request.user, funcionalidade):
                messages.error(request, 'Você não tem permissão para acessar esta seção.')
                return redirect('barbearia:dashboard')
            return view(request, *args, **kwargs)
        wrapper.__name__ = view.__name__
        return wrapper
    return decorator


def _admin_required(view):
    """Restringe ao acesso 'configuracoes' (master ou com permissão explícita)."""
    return _perm_required('configuracoes')(view)


def _cliente_required(view):
    """Apenas clientes com conta no portal."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('barbearia:cliente_login')
        if not hasattr(request.user, 'cliente_perfil'):
            return redirect('barbearia:dashboard')
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — SISTEMA
# ─────────────────────────────────────────────────────────────────────────────

def login_barbearia(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'cliente_perfil'):
            return redirect('barbearia:cliente_dashboard')
        if request.user.is_superuser or hasattr(request.user, 'permissao'):
            return redirect('barbearia:dashboard')
        logout(request)

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            if hasattr(user, 'cliente_perfil'):
                login(request, user)
                return redirect('barbearia:cliente_dashboard')
            if user.is_superuser or hasattr(user, 'permissao'):
                login(request, user)
                return redirect('barbearia:dashboard')
            messages.error(request, 'Seu usuário não tem permissão para acessar o sistema.')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    return render(request, 'barbearia/login.html')


def logout_barbearia(request):
    logout(request)
    return redirect('barbearia:login')


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@require_GET
def api_preco_servico(request, pk):
    svc = get_object_or_404(Servico, pk=pk, ativo=True)
    return JsonResponse({'preco': str(svc.preco), 'duracao_minutos': svc.duracao_minutos, 'nome': svc.nome})


@require_GET
def api_eventos_calendario(request):
    """FullCalendar JSON event source."""
    start_str = request.GET.get('start', '')
    end_str = request.GET.get('end', '')
    barbeiro_id = request.GET.get('barbeiro', '')

    try:
        start_d = date.fromisoformat(start_str[:10])
        end_d = date.fromisoformat(end_str[:10])
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)

    qs = Agendamento.objects.filter(
        data_hora__date__gte=start_d,
        data_hora__date__lte=end_d,
    ).exclude(status='cancelado').select_related('cliente', 'barbeiro', 'servico')

    if barbeiro_id:
        qs = qs.filter(barbeiro_id=barbeiro_id)

    CORES = {
        'agendado': '#1976d2',
        'confirmado': '#388e3c',
        'em_atendimento': '#f57c00',
        'concluido': '#FFD700',
        'faltou': '#7b1fa2',
    }
    events = []
    for ag in qs:
        dur = ag.servico.duracao_minutos if ag.servico else 30
        end_dt = ag.data_hora + timedelta(minutes=dur)
        cor = CORES.get(ag.status, '#888')
        events.append({
            'id': ag.pk,
            'title': f"{ag.data_hora.strftime('%H:%M')} {ag.cliente.nome}",
            'start': ag.data_hora.isoformat(),
            'end': end_dt.isoformat(),
            'backgroundColor': cor,
            'borderColor': cor,
            'textColor': '#fff' if ag.status != 'concluido' else '#000',
            'extendedProps': {
                'cliente': ag.cliente.nome,
                'servico': ag.servico.nome if ag.servico else '',
                'barbeiro': ag.barbeiro.nome if ag.barbeiro else '',
                'status': ag.get_status_display(),
                'valor': str(ag.valor_cobrado or ''),
                'whatsapp': ag.gerar_link_whatsapp(),
                'editar_url': reverse('barbearia:editar_agendamento', args=[ag.pk]),
            },
        })
    return JsonResponse(events, safe=False)


@require_GET
def api_horarios_disponiveis(request):
    """Slots disponíveis para o portal do cliente — aceita data única ou range start/end."""
    svc_id = request.GET.get('servico')
    barb_id = request.GET.get('barbeiro')
    # Suporta ?data=... (legado) ou ?start=...&end=... (range do FullCalendar)
    start_str = request.GET.get('start') or request.GET.get('data')
    end_str = request.GET.get('end')

    try:
        data_inicio = date.fromisoformat(start_str[:10])
        svc = Servico.objects.get(pk=svc_id, ativo=True)
    except (ValueError, TypeError, AttributeError, Servico.DoesNotExist):
        return JsonResponse([], safe=False)

    try:
        data_fim = date.fromisoformat(end_str[:10]) if end_str else data_inicio
    except (ValueError, TypeError):
        data_fim = data_inicio

    hoje = date.today()
    data_inicio = max(data_inicio, hoje)
    data_fim = min(data_fim, data_inicio + timedelta(days=30))  # máx 30 dias à frente

    if not barb_id:
        return JsonResponse([], safe=False)

    try:
        barbeiro = Barbeiro.objects.get(pk=barb_id, ativo=True)
    except Barbeiro.DoesNotExist:
        return JsonResponse([], safe=False)

    events = []
    cur = data_inicio
    while cur <= data_fim:
        for slot in gerar_slots_disponiveis(cur, barbeiro, svc):
            slot_aware = timezone.make_aware(slot)
            end_aware = slot_aware + timedelta(minutes=svc.duracao_minutos)
            events.append({
                'title': slot.strftime('%H:%M'),
                'start': slot_aware.isoformat(),
                'end': end_aware.isoformat(),
                'backgroundColor': '#FFD700',
                'borderColor': '#c9a800',
                'textColor': '#000',
                'extendedProps': {'slot': slot.strftime('%Y-%m-%dT%H:%M')},
            })
        cur += timedelta(days=1)

    return JsonResponse(events, safe=False)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def dashboard(request):
    hoje = date.today()
    mes, ano = hoje.month, hoje.year

    faturamento_mes = Agendamento.objects.filter(
        status='concluido', data_hora__month=mes, data_hora__year=ano,
    ).aggregate(total=Sum('valor_cobrado'))['total'] or 0

    total_agendamentos_mes = Agendamento.objects.filter(
        data_hora__month=mes, data_hora__year=ano,
    ).exclude(status='cancelado').count()

    saidas_mes = Saida.objects.filter(
        data__month=mes, data__year=ano,
    ).aggregate(total=Sum('valor'))['total'] or 0

    saldo_mes = faturamento_mes - saidas_mes

    # KPI: Planos Ativos no Mês — clientes vinculados a algum plano
    planos_ativos_mes = Cliente.objects.filter(plano__isnull=False).count()

    agendamentos_hoje = Agendamento.objects.filter(
        data_hora__date=hoje,
    ).exclude(status='cancelado').select_related('cliente', 'barbeiro', 'servico').order_by('data_hora')

    proximos = Agendamento.objects.filter(
        data_hora__gte=timezone.now(), status__in=['agendado', 'confirmado'],
    ).select_related('cliente', 'barbeiro', 'servico').order_by('data_hora')[:8]

    # Barbeiros — usando o novo modelo Barbeiro (não User)
    barbeiros_stats = Barbeiro.objects.filter(ativo=True).annotate(
        total_mes=Count(
            'agendamentos',
            filter=Q(
                agendamentos__status='concluido',
                agendamentos__data_hora__month=mes,
                agendamentos__data_hora__year=ano,
            ),
        ),
        fat_mes=Sum(
            'agendamentos__valor_cobrado',
            filter=Q(
                agendamentos__status='concluido',
                agendamentos__data_hora__month=mes,
                agendamentos__data_hora__year=ano,
            ),
        ),
    ).order_by('-fat_mes')

    faturamento_diario = (
        Agendamento.objects
        .filter(status='concluido', data_hora__month=mes, data_hora__year=ano)
        .annotate(dia=TruncDate('data_hora'))
        .values('dia')
        .annotate(total=Sum('valor_cobrado'))
        .order_by('dia')
    )

    context = {
        'faturamento_mes': faturamento_mes,
        'total_agendamentos_mes': total_agendamentos_mes,
        'saidas_mes': saidas_mes,
        'saldo_mes': saldo_mes,
        'planos_ativos_mes': planos_ativos_mes,
        'agendamentos_hoje': agendamentos_hoje,
        'proximos': proximos,
        'barbeiros_stats': barbeiros_stats,
        'labels_diario': json.dumps([str(f['dia'].day) for f in faturamento_diario]),
        'dados_diario': json.dumps([float(f['total']) for f in faturamento_diario]),
        'labels_barbeiros': json.dumps([b.nome for b in barbeiros_stats]),
        'dados_barbeiros': json.dumps([float(b.fat_mes or 0) for b in barbeiros_stats]),
        'mes_nome': f"{calendar.month_name[mes]} {ano}",
    }
    return render(request, 'barbearia/dashboard.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# AGENDA
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def agenda(request):
    data_filtro = request.GET.get('data', date.today().isoformat())
    barbeiro_filtro = request.GET.get('barbeiro', '')
    status_filtro = request.GET.get('status', '')

    try:
        data_sel = date.fromisoformat(data_filtro)
    except (ValueError, TypeError):
        data_sel = date.today()

    qs = Agendamento.objects.filter(
        data_hora__date=data_sel,
    ).select_related('cliente', 'barbeiro', 'servico').order_by('data_hora')

    if barbeiro_filtro:
        qs = qs.filter(barbeiro_id=barbeiro_filtro)
    if status_filtro:
        qs = qs.filter(status=status_filtro)

    barbeiros_lista = Barbeiro.objects.filter(ativo=True)
    bloqueados = HorarioBloqueado.objects.filter(data_inicio__date=data_sel).select_related('barbeiro')

    context = {
        'agendamentos': qs,
        'barbeiros': barbeiros_lista,
        'data_selecionada': data_sel,
        'data_anterior': (data_sel - timedelta(days=1)).isoformat(),
        'data_proxima': (data_sel + timedelta(days=1)).isoformat(),
        'barbeiro_filtro': barbeiro_filtro,
        'status_filtro': status_filtro,
        'status_choices': Agendamento._meta.get_field('status').choices,
        'horarios_bloqueados': bloqueados,
    }
    return render(request, 'barbearia/agenda.html', context)


@_staff_required
def novo_agendamento(request):
    form = AgendamentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ag = form.save()
        Notificacao.objects.create(
            usuario=request.user,
            mensagem=(
                f"Agendamento criado: {ag.cliente.nome} "
                f"com {ag.barbeiro.nome if ag.barbeiro else '—'} "
                f"em {ag.data_hora.strftime('%d/%m/%Y às %H:%M')}"
            ),
            tipo='novo_agendamento',
            link=reverse('barbearia:agenda') + f"?data={ag.data_hora.date()}",
        )
        messages.success(request, f"Agendamento para {ag.cliente.nome} criado!")
        return redirect(reverse('barbearia:agenda') + f"?data={ag.data_hora.date()}")
    return render(request, 'barbearia/form_agendamento.html', {'form': form, 'titulo': 'Novo Agendamento'})


@_staff_required
def editar_agendamento(request, pk):
    ag = get_object_or_404(Agendamento, pk=pk)
    form = AgendamentoForm(request.POST or None, instance=ag)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Agendamento atualizado!")
        return redirect('barbearia:agenda')
    return render(request, 'barbearia/form_agendamento.html', {
        'form': form, 'titulo': 'Editar Agendamento', 'agendamento': ag,
    })


@_staff_required
def excluir_agendamento(request, pk):
    ag = get_object_or_404(Agendamento, pk=pk)
    if request.method == 'POST':
        nome = ag.cliente.nome
        ag.delete()
        messages.success(request, f"Agendamento de {nome} excluído.")
    return redirect('barbearia:agenda')


@_staff_required
def alterar_status(request, pk, novo_status):
    ag = get_object_or_404(Agendamento, pk=pk)
    status_validos = [s[0] for s in Agendamento._meta.get_field('status').choices]
    if novo_status in status_validos:
        ag.status = novo_status
        ag.save()
        messages.success(request, f"Status: {ag.get_status_display()}")
    return redirect(request.META.get('HTTP_REFERER', reverse('barbearia:agenda')))


# ─────────────────────────────────────────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def clientes(request):
    q = request.GET.get('q', '')
    qs = Cliente.objects.select_related('plano').order_by('nome')
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(telefone__icontains=q))
    return render(request, 'barbearia/clientes.html', {'clientes': qs, 'q': q})


@_staff_required
def novo_cliente(request):
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save()
        messages.success(request, f"Cliente {c.nome} cadastrado!")
        return redirect('barbearia:clientes')
    return render(request, 'barbearia/form_cliente.html', {'form': form, 'titulo': 'Novo Cliente'})


@_staff_required
def editar_cliente(request, pk):
    c = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=c)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Cliente atualizado!")
        return redirect('barbearia:clientes')
    return render(request, 'barbearia/form_cliente.html', {'form': form, 'titulo': 'Editar Cliente', 'cliente': c})


@_staff_required
def excluir_cliente(request, pk):
    c = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        nome = c.nome
        c.delete()
        messages.success(request, f"Cliente {nome} excluído.")
    return redirect('barbearia:clientes')


# ─────────────────────────────────────────────────────────────────────────────
# FINANCEIRO
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def financeiro(request):
    hoje = date.today()
    # Filtro por intervalo de datas — padrão: primeiro ao último dia do mês atual
    try:
        data_inicio = date.fromisoformat(request.GET.get('data_inicio', ''))
    except (ValueError, TypeError):
        data_inicio = hoje.replace(day=1)

    try:
        data_fim = date.fromisoformat(request.GET.get('data_fim', ''))
    except (ValueError, TypeError):
        import calendar
        ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
        data_fim = hoje.replace(day=ultimo_dia)

    # Garante ordem correta
    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio

    entradas = Agendamento.objects.filter(
        status='concluido',
        data_hora__date__gte=data_inicio,
        data_hora__date__lte=data_fim,
    ).aggregate(total=Sum('valor_cobrado'))['total'] or 0

    saidas_qs = Saida.objects.filter(
        data__gte=data_inicio, data__lte=data_fim,
    ).order_by('-data')
    total_saidas = saidas_qs.aggregate(total=Sum('valor'))['total'] or 0

    agendamentos_periodo = Agendamento.objects.filter(
        status='concluido',
        data_hora__date__gte=data_inicio,
        data_hora__date__lte=data_fim,
    ).select_related('cliente', 'barbeiro', 'servico').order_by('-data_hora')

    saidas_por_categoria = (
        Saida.objects.filter(data__gte=data_inicio, data__lte=data_fim)
        .values('categoria')
        .annotate(total=Sum('valor'))
        .order_by('-total')
    )

    import calendar as _cal
    # Atalhos para botões rápidos no template
    hoje_primeiro = hoje.replace(day=1)
    hoje_ultimo = hoje.replace(day=_cal.monthrange(hoje.year, hoje.month)[1])
    dia_semana = hoje.weekday()  # 0=seg
    semana_inicio = hoje - timedelta(days=dia_semana)
    semana_fim = semana_inicio + timedelta(days=6)

    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'entradas': entradas,
        'total_saidas': total_saidas,
        'saldo': entradas - total_saidas,
        'saidas_qs': saidas_qs,
        'agendamentos_mes': agendamentos_periodo,
        'saidas_por_categoria': saidas_por_categoria,
        'hoje': hoje,
        'hoje_primeiro': hoje_primeiro,
        'hoje_ultimo': hoje_ultimo,
        'semana_inicio': semana_inicio,
        'semana_fim': semana_fim,
    }
    return render(request, 'barbearia/financeiro.html', context)


@_staff_required
def nova_saida(request):
    form = SaidaForm(request.POST or None, initial={'data': date.today()})
    if request.method == 'POST' and form.is_valid():
        s = form.save(commit=False)
        s.registrado_por = request.user
        s.save()
        messages.success(request, f"Despesa '{s.descricao}' registrada!")
        return redirect('barbearia:financeiro')
    return render(request, 'barbearia/form_saida.html', {'form': form, 'titulo': 'Nova Despesa'})


@_staff_required
def excluir_saida(request, pk):
    s = get_object_or_404(Saida, pk=pk)
    if request.method == 'POST':
        s.delete()
        messages.success(request, "Despesa excluída.")
    return redirect('barbearia:financeiro')


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def notificacoes(request):
    notifs = Notificacao.objects.filter(usuario=request.user).order_by('-criado_em')
    notifs.filter(lida=False).update(lida=True)
    return render(request, 'barbearia/notificacoes.html', {'notificacoes': notifs})


@_staff_required
def marcar_notificacao_lida(request, pk):
    notif = get_object_or_404(Notificacao, pk=pk, usuario=request.user)
    notif.lida = True
    notif.save()
    return JsonResponse({'ok': True})


# ─────────────────────────────────────────────────────────────────────────────
# BARBEIROS CRUD  (novo modelo Barbeiro — independente do User)
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def barbeiros(request):
    lista = Barbeiro.objects.annotate(
        total_geral=Count('agendamentos', filter=Q(agendamentos__status='concluido')),
        fat_total=Sum('agendamentos__valor_cobrado', filter=Q(agendamentos__status='concluido')),
    ).order_by('nome')
    return render(request, 'barbearia/barbeiros.html', {'barbeiros': lista})


@_staff_required
def cadastrar_barbeiro(request):
    form = BarbeiroForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        b = form.save()
        messages.success(request, f"Barbeiro {b.nome} cadastrado!")
        return redirect('barbearia:editar_barbeiro', pk=b.pk)
    return render(request, 'barbearia/cadastrar_barbeiro.html', {'form': form, 'titulo': 'Cadastrar Barbeiro'})


@_staff_required
def editar_barbeiro(request, pk):
    b = get_object_or_404(Barbeiro, pk=pk)
    form = BarbeiroForm(request.POST or None, request.FILES or None, instance=b)
    formset = GradeHorarioFormSet(request.POST or None, instance=b)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Barbeiro {b.nome} atualizado!")
            return redirect('barbearia:barbeiros')

    grades_atuais = GradeHorario.objects.filter(barbeiro=b).order_by('dia_semana')
    return render(request, 'barbearia/editar_barbeiro.html', {
        'form': form,
        'formset': formset,
        'barbeiro': b,
        'grades_atuais': grades_atuais,
        'titulo': f'Editar — {b.nome}',
    })


@_staff_required
def excluir_barbeiro(request, pk):
    b = get_object_or_404(Barbeiro, pk=pk)
    if request.method == 'POST':
        nome = b.nome
        b.delete()
        messages.success(request, f"Barbeiro {nome} removido.")
    return redirect('barbearia:barbeiros')


# ── PLANOS ────────────────────────────────────────────────────────────────────

@_staff_required
def planos(request):
    lista = Plano.objects.prefetch_related('servicos', 'clientes').order_by('preco_mensal')
    receita_total = sum(p.receita_mensal_esperada() for p in lista if p.ativo)
    return render(request, 'barbearia/planos.html', {'planos': lista, 'receita_total': receita_total})


@_staff_required
def novo_plano(request):
    form = PlanoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        p = form.save()
        messages.success(request, f"Plano '{p.nome}' criado!")
        return redirect('barbearia:planos')
    return render(request, 'barbearia/form_plano.html', {'form': form, 'titulo': 'Novo Plano'})


@_staff_required
def editar_plano(request, pk):
    p = get_object_or_404(Plano, pk=pk)
    form = PlanoForm(request.POST or None, instance=p)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Plano '{p.nome}' atualizado!")
        return redirect('barbearia:planos')
    return render(request, 'barbearia/form_plano.html', {'form': form, 'titulo': f'Editar — {p.nome}', 'plano': p})


@_staff_required
def excluir_plano(request, pk):
    p = get_object_or_404(Plano, pk=pk)
    if request.method == 'POST':
        nome = p.nome
        p.delete()
        messages.success(request, f"Plano '{nome}' excluído.")
    return redirect('barbearia:planos')


@_staff_required
def relatorio_planos(request):
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))

    planos_stats = Plano.objects.prefetch_related('servicos', 'clientes').filter(ativo=True).annotate(
        num_ativos=Count('clientes'),
    )
    receita_planos = sum(p.preco_mensal * p.num_ativos for p in planos_stats)

    ags_mes = (
        Agendamento.objects.filter(status='concluido', data_hora__month=mes, data_hora__year=ano)
        .select_related('cliente__plano', 'servico')
    )
    total_avulso = sum(float(ag.valor_cobrado or 0) for ag in ags_mes if not ag.servico_coberto_pelo_plano())
    total_coberto = sum(
        float(ag.servico.preco or 0) for ag in ags_mes if ag.servico_coberto_pelo_plano() and ag.servico
    )

    context = {
        'planos_stats': planos_stats,
        'receita_planos': receita_planos,
        'total_avulso': total_avulso,
        'total_coberto': total_coberto,
        'receita_total_esperada': float(receita_planos) + total_avulso,
        'mes': mes, 'ano': ano,
        'meses': [(i, f"{i:02d}") for i in range(1, 13)],
        'anos': list(range(2024, date.today().year + 2)),
    }
    return render(request, 'barbearia/relatorio_planos.html', context)


# ── BLOQUEIOS ─────────────────────────────────────────────────────────────────

@_staff_required
def bloquear_horario(request):
    form = HorarioBloqueadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Horário bloqueado!")
        return redirect('barbearia:agenda')
    return render(request, 'barbearia/form_bloqueio.html', {'form': form, 'titulo': 'Bloquear Horário'})


@_staff_required
def excluir_bloqueio(request, pk):
    b = get_object_or_404(HorarioBloqueado, pk=pk)
    if request.method == 'POST':
        b.delete()
        messages.success(request, "Bloqueio removido.")
    return redirect('barbearia:agenda')


# ── SERVIÇOS ──────────────────────────────────────────────────────────────────

@_staff_required
def servicos(request):
    lista = Servico.objects.all().order_by('nome')
    return render(request, 'barbearia/servicos.html', {'servicos': lista})


@_staff_required
def novo_servico(request):
    form = ServicoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        s = form.save()
        messages.success(request, f"Serviço '{s.nome}' criado!")
        return redirect('barbearia:servicos')
    return render(request, 'barbearia/form_servico.html', {'form': form, 'titulo': 'Novo Serviço'})


@_staff_required
def editar_servico(request, pk):
    s = get_object_or_404(Servico, pk=pk)
    form = ServicoForm(request.POST or None, instance=s)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Serviço atualizado!")
        return redirect('barbearia:servicos')
    return render(request, 'barbearia/form_servico.html', {'form': form, 'titulo': 'Editar Serviço', 'servico': s})


@_staff_required
def excluir_servico(request, pk):
    s = get_object_or_404(Servico, pk=pk)
    if request.method == 'POST':
        nome = s.nome
        s.delete()
        messages.success(request, f"Serviço '{nome}' excluído.")
    return redirect('barbearia:servicos')


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES — Gestão de Usuários do Sistema
# ─────────────────────────────────────────────────────────────────────────────

@_admin_required
def configuracoes_usuarios(request):
    # Exclui clientes do portal (têm cliente_perfil) e o próprio superusuário
    usuarios = (
        User.objects
        .select_related('permissao')
        .filter(cliente_perfil__isnull=True, is_superuser=False)
        .order_by('username')
    )
    return render(request, 'barbearia/configuracoes/usuarios.html', {
        'usuarios': usuarios,
        'funcionalidades': FUNCIONALIDADES,
    })


@_admin_required
def configuracoes_novo_usuario(request):
    form = SistemaUsuarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        user = User.objects.create_user(
            username=cd['username'],
            password=cd['password'],
            is_staff=True,
        )
        PermissaoUsuario.objects.create(
            usuario=user,
            **{campo: cd.get(campo, False) for campo, *_ in FUNCIONALIDADES}
        )
        messages.success(request, f"Usuário '{user.username}' criado.")
        return redirect('barbearia:configuracoes_usuarios')
    return render(request, 'barbearia/configuracoes/form_usuario.html', {
        'form': form,
        'titulo': 'Novo Usuário do Sistema',
        'funcionalidades': FUNCIONALIDADES,
    })


@_admin_required
def configuracoes_editar_usuario(request, pk):
    u = get_object_or_404(User, pk=pk, cliente_perfil__isnull=True, is_superuser=False)
    perm, _ = PermissaoUsuario.objects.get_or_create(usuario=u)

    initial = {'ativo': u.is_active}
    for campo, *_ in FUNCIONALIDADES:
        initial[campo] = getattr(perm, campo, False)

    form = EditarSistemaUsuarioForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        u.is_active = cd.get('ativo', True)
        if cd.get('nova_senha'):
            u.set_password(cd['nova_senha'])
        u.save()
        for campo, *_ in FUNCIONALIDADES:
            setattr(perm, campo, cd.get(campo, False))
        perm.save()
        messages.success(request, f"Usuário '{u.username}' atualizado.")
        return redirect('barbearia:configuracoes_usuarios')

    return render(request, 'barbearia/configuracoes/form_usuario.html', {
        'form': form,
        'usuario': u,
        'titulo': f'Editar — {u.username}',
        'funcionalidades': FUNCIONALIDADES,
    })


@_admin_required
def configuracoes_excluir_usuario(request, pk):
    u = get_object_or_404(User, pk=pk, cliente_perfil__isnull=True, is_superuser=False)
    if u == request.user:
        messages.error(request, 'Você não pode excluir o seu próprio usuário.')
        return redirect('barbearia:configuracoes_usuarios')
    if request.method == 'POST':
        username = u.username
        u.delete()
        messages.success(request, f"Usuário '{username}' removido.")
    return redirect('barbearia:configuracoes_usuarios')


# ─────────────────────────────────────────────────────────────────────────────
# LEMBRETES DE AGENDAMENTO
# ─────────────────────────────────────────────────────────────────────────────

@_staff_required
def lembretes(request):
    agora = timezone.now()
    # Agendamentos ativos nas próximas 48h
    limite = agora + timedelta(hours=48)

    pendentes = (
        Agendamento.objects
        .filter(
            data_hora__gte=agora,
            data_hora__lte=limite,
            status__in=['agendado', 'confirmado'],
            lembrete_enviado=False,
        )
        .select_related('cliente', 'barbeiro', 'servico')
        .order_by('data_hora')
    )

    enviados_recentes = (
        Agendamento.objects
        .filter(lembrete_enviado=True)
        .select_related('cliente', 'barbeiro', 'servico')
        .order_by('-lembrete_enviado_em')[:30]
    )

    return render(request, 'barbearia/lembretes.html', {
        'pendentes': pendentes,
        'enviados_recentes': enviados_recentes,
        'agora': agora,
    })


@_staff_required
def marcar_lembrete_enviado(request, pk):
    """Chamado via fetch() quando admin clica 'Enviar via WhatsApp'."""
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    ag = get_object_or_404(Agendamento, pk=pk)
    ag.lembrete_enviado = True
    ag.lembrete_enviado_em = timezone.now()
    ag.save(update_fields=['lembrete_enviado', 'lembrete_enviado_em'])
    return JsonResponse({'ok': True})


# ─────────────────────────────────────────────────────────────────────────────
# PORTAL DO CLIENTE
# ─────────────────────────────────────────────────────────────────────────────

def cliente_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'cliente_perfil'):
            return redirect('barbearia:cliente_dashboard')
        return redirect('barbearia:dashboard')

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            if not hasattr(user, 'cliente_perfil'):
                messages.error(request, 'Use o portal administrativo para este login.')
                return render(request, 'barbearia/cliente/login.html')
            login(request, user)
            return redirect('barbearia:cliente_dashboard')
        messages.error(request, 'Usuário ou senha incorretos.')
    return render(request, 'barbearia/cliente/login.html')


def cliente_registro(request):
    form = ClienteRegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        user = User.objects.create_user(
            username=cd['username'],
            password=cd['password'],
        )
        first, *rest = cd['nome'].split(' ', 1)
        user.first_name = first
        user.last_name = rest[0] if rest else ''
        user.save()
        # Cria ou vincula o registro de Cliente ao User do portal
        cliente_obj, created = Cliente.objects.get_or_create(
            telefone=cd['telefone'],
            defaults={'nome': cd['nome']},
        )
        if not created:
            cliente_obj.nome = cd['nome']
        cliente_obj.usuario = user
        cliente_obj.save()
        login(request, user)
        messages.success(request, f"Bem-vindo(a), {first}! Conta criada.")
        return redirect('barbearia:cliente_dashboard')
    return render(request, 'barbearia/cliente/registro.html', {'form': form})


@_cliente_required
def cliente_dashboard(request):
    cliente = request.user.cliente_perfil
    proximos = Agendamento.objects.filter(
        data_hora__gte=timezone.now(),
        status__in=['agendado', 'confirmado'],
        cliente=cliente,
    ).select_related('servico', 'barbeiro').order_by('data_hora')[:5]
    return render(request, 'barbearia/cliente/dashboard.html', {
        'proximos': proximos,
        'hoje': date.today(),
        'cliente': cliente,
    })


@_cliente_required
def cliente_agendar(request):
    form = AgendamentoClienteForm(request.POST or None)
    servicos_lista = Servico.objects.filter(ativo=True).order_by('nome')
    barbeiros_lista = Barbeiro.objects.filter(ativo=True)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        svc = cd['servico']
        barb = cd['barbeiro']
        dt = cd['data_hora']
        dt_aware = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

        cliente_obj = request.user.cliente_perfil
        ag = Agendamento.objects.create(
            cliente=cliente_obj,
            barbeiro=barb,
            servico=svc,
            data_hora=dt_aware,
            valor_cobrado=svc.preco,
            observacoes=cd.get('observacoes', ''),
            status='agendado',
        )
        # Notifica todos os usuários do sistema
        for admin_user in User.objects.filter(is_staff=True, is_active=True)[:3]:
            Notificacao.objects.create(
                usuario=admin_user,
                mensagem=(
                    f"Novo agendamento via portal: {cliente_obj.nome} "
                    f"com {barb.nome} em {dt_aware.strftime('%d/%m às %H:%M')}"
                ),
                tipo='novo_agendamento',
            )
        messages.success(request, f"Agendamento confirmado para {dt_aware.strftime('%d/%m às %H:%M')}!")
        return redirect('barbearia:cliente_meus_agendamentos')

    return render(request, 'barbearia/cliente/agendar.html', {
        'form': form,
        'servicos_lista': servicos_lista,
        'barbeiros_lista': barbeiros_lista,
    })


@_cliente_required
def cliente_meus_agendamentos(request):
    cliente = request.user.cliente_perfil
    qs = Agendamento.objects.filter(cliente=cliente).select_related('servico', 'barbeiro').order_by('-data_hora')

    futuros = qs.filter(data_hora__gte=timezone.now()).exclude(status__in=['cancelado', 'concluido'])
    passados = qs.filter(
        Q(data_hora__lt=timezone.now()) | Q(status__in=['concluido', 'cancelado', 'faltou'])
    )[:20]

    return render(request, 'barbearia/cliente/meus_agendamentos.html', {
        'futuros': futuros,
        'passados': passados,
    })


@_cliente_required
def cliente_cancelar_agendamento(request, pk):
    cliente = request.user.cliente_perfil
    ag = get_object_or_404(
        Agendamento, pk=pk, cliente=cliente, status__in=['agendado', 'confirmado'],
    )
    if request.method == 'POST':
        ag.status = 'cancelado'
        ag.save()
        messages.success(request, "Agendamento cancelado.")
    return redirect('barbearia:cliente_meus_agendamentos')


@_cliente_required
def cliente_perfil(request):
    cliente = request.user.cliente_perfil
    initial = {'nome': cliente.nome, 'telefone': cliente.telefone}
    form = PerfilClienteForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        cliente.nome = cd['nome']
        cliente.telefone = cd['telefone']
        cliente.save()
        # Atualiza nome do User
        first, *rest = cd['nome'].split(' ', 1)
        request.user.first_name = first
        request.user.last_name = rest[0] if rest else ''
        if cd.get('nova_senha') and cd.get('senha_atual'):
            if not request.user.check_password(cd['senha_atual']):
                form.add_error('senha_atual', 'Senha atual incorreta.')
            else:
                request.user.set_password(cd['nova_senha'])
                update_session_auth_hash(request, request.user)
                messages.success(request, "Senha alterada!")
        request.user.save()
        messages.success(request, "Perfil atualizado!")
        return redirect('barbearia:cliente_perfil')

    return render(request, 'barbearia/cliente/perfil.html', {'form': form, 'cliente': cliente})


@_cliente_required
def cliente_planos(request):
    cliente = request.user.cliente_perfil
    planos = Plano.objects.filter(ativo=True).prefetch_related('servicos').order_by('preco_mensal')

    wa_numero = getattr(settings, 'BARBEARIA_WHATSAPP', '5583999999999')

    planos_ctx = []
    for p in planos:
        msg = (
            f"Olá! Vi os planos disponíveis no portal da Boss Barbearia e tenho interesse "
            f"no plano *{p.nome}* (R$ {p.preco_mensal}/mês). "
            f"Podem me dar mais informações e fazer o cadastro?"
        )
        planos_ctx.append({
            'plano': p,
            'link_whatsapp': f"https://wa.me/{wa_numero}?text={quote(msg)}",
            'e_meu_plano': cliente.plano_id == p.pk,
        })

    return render(request, 'barbearia/cliente/planos.html', {
        'planos_ctx': planos_ctx,
        'cliente': cliente,
    })


def cliente_logout(request):
    logout(request)
    return redirect('barbearia:cliente_login')
