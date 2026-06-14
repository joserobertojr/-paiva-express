from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from clientes.models import Cliente
from pacotes.models import Pacote
from reservas.models import Reserva
from pagamentos.models import Pagamento
from vendedores.models import Vendedor
from .decorators import admin_required
from .models import PerfilUsuario, AuditLog, SECOES
from .audit import log as audit_log


@login_required
def dashboard(request):
    hoje = timezone.now()
    mes, ano = hoje.month, hoje.year

    total_clientes = Cliente.objects.filter(ativo=True).count()
    total_pacotes  = Pacote.objects.filter(ativo=True).count()
    reservas_mes   = Reserva.objects.filter(
        criado_em__month=mes, criado_em__year=ano
    ).exclude(status='cancelada').count()
    receita_mes = Pagamento.objects.filter(
        registrado_em__month=mes, registrado_em__year=ano,
    ).aggregate(t=Sum('valor'))['t'] or 0

    reservas_recentes = Reserva.objects.exclude(status='cancelada').prefetch_related(
        'passageiros__cliente', 'pacote'
    ).order_by('-criado_em')[:8]

    proximos_pacotes = Pacote.objects.filter(
        ativo=True, data_saida__gte=hoje.date()
    ).order_by('data_saida')[:5]

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'total_pacotes': total_pacotes,
        'reservas_mes': reservas_mes,
        'receita_mes': receita_mes,
        'reservas_recentes': reservas_recentes,
        'proximos_pacotes': proximos_pacotes,
    })


# ── Configurações ─────────────────────────────────────────────────────────────

@login_required
@admin_required
def configuracoes(request):
    # Só exibe vendedores que já têm acesso ao sistema
    usuarios = Vendedor.objects.filter(
        ativo=True, user__isnull=False
    ).select_related('user__perfil').order_by('nome')
    return render(request, 'configuracoes/index.html', {'usuarios': usuarios})


@login_required
@admin_required
def conf_novo_usuario(request):
    # Vendedores sem acesso ainda
    vendedores_sem_acesso = Vendedor.objects.filter(ativo=True, user__isnull=True).order_by('nome')

    if request.method == 'POST':
        vendedor_id = request.POST.get('vendedor')
        username    = request.POST.get('username', '').strip()
        senha       = request.POST.get('senha', '').strip()
        role        = request.POST.get('role', 'vendedor')

        if not vendedor_id:
            messages.error(request, 'Selecione um vendedor.')
        elif not username or not senha:
            messages.error(request, 'Usuário e senha são obrigatórios.')
        elif len(senha) < 8:
            messages.error(request, 'A senha deve ter ao menos 8 caracteres.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Este nome de usuário já está em uso.')
        else:
            vendedor = get_object_or_404(Vendedor, pk=vendedor_id, user__isnull=True)
            user = User.objects.create_user(
                username=username, password=senha, first_name=vendedor.nome
            )
            perfil = PerfilUsuario(user=user, role=role)
            # Permissões granulares do POST
            for secao, _ in SECOES:
                setattr(perfil, f'perm_{secao}', request.POST.get(f'perm_{secao}') == 'on')
            # Admin tem tudo implícito; garantir que perm_configuracoes fique marcado
            if role == 'admin':
                for secao, _ in SECOES:
                    setattr(perfil, f'perm_{secao}', True)
            perfil.save()
            vendedor.user = user
            vendedor.save()
            audit_log(request, AuditLog.ACAO_CRIAR, 'Configurações',
                      f'Criou acesso para {vendedor.nome} (usuário: {username}, perfil: {role})')
            messages.success(request, f'Acesso criado para {vendedor.nome}.')
            return redirect('core:configuracoes')

    return render(request, 'configuracoes/form_novo_usuario.html', {
        'vendedores_sem_acesso': vendedores_sem_acesso,
        'secoes': SECOES,
    })


@login_required
@admin_required
def conf_editar_usuario(request, vendedor_pk):
    vendedor = get_object_or_404(Vendedor, pk=vendedor_pk)
    if not vendedor.user:
        messages.error(request, 'Este vendedor não possui acesso cadastrado.')
        return redirect('core:configuracoes')

    perfil, _ = PerfilUsuario.objects.get_or_create(user=vendedor.user)

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha', '').strip()
        role       = request.POST.get('role', perfil.role)

        if nova_senha and len(nova_senha) < 8:
            messages.error(request, 'A senha deve ter ao menos 8 caracteres.')
        else:
            if nova_senha:
                vendedor.user.set_password(nova_senha)
                vendedor.user.save()
            perfil.role = role
            if role == 'admin':
                for secao, _ in SECOES:
                    setattr(perfil, f'perm_{secao}', True)
            else:
                for secao, _ in SECOES:
                    setattr(perfil, f'perm_{secao}', request.POST.get(f'perm_{secao}') == 'on')
            perfil.save()
            audit_log(request, AuditLog.ACAO_EDITAR, 'Configurações',
                      f'Editou acesso de {vendedor.nome} (perfil: {role})')
            messages.success(request, 'Usuário atualizado.')
            return redirect('core:configuracoes')

    perms_atuais = perfil.perms_dict()
    secoes_com_perms = [(s, lbl, perms_atuais.get(s, False)) for s, lbl in SECOES]
    return render(request, 'configuracoes/form_editar_usuario.html', {
        'vendedor': vendedor,
        'perfil': perfil,
        'secoes_com_perms': secoes_com_perms,
    })


@login_required
@admin_required
def conf_excluir_usuario(request, vendedor_pk):
    vendedor = get_object_or_404(Vendedor, pk=vendedor_pk)
    if request.method == 'POST' and vendedor.user:
        user = vendedor.user
        nome = vendedor.nome
        vendedor.user = None
        vendedor.save()
        user.delete()
        audit_log(request, AuditLog.ACAO_EXCLUIR, 'Configurações',
                  f'Removeu acesso de {nome}')
        messages.success(request, f'Acesso de {nome} removido.')
    return redirect('core:configuracoes')


@login_required
@admin_required
def conf_logs(request):
    logs = AuditLog.objects.select_related('usuario').order_by('-timestamp')[:200]
    return render(request, 'configuracoes/logs.html', {'logs': logs})
