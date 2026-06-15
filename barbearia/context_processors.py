from .models import Notificacao


def notificacoes_barbearia(request):
    ctx = {'notif_nao_lidas': 0, 'user_perm': None}
    if request.user.is_authenticated:
        ctx['notif_nao_lidas'] = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).count()
        if request.user.is_superuser:
            # Superusuário tem tudo — simula um objeto com tem_acesso sempre True
            ctx['user_perm'] = _SuperPerm()
        else:
            try:
                ctx['user_perm'] = request.user.permissao
            except Exception:
                pass
    return ctx


class _SuperPerm:
    """Proxy de permissão para superusuário — retorna True em tudo."""
    master = True
    agenda = True
    clientes = True
    barbeiros = True
    servicos = True
    financeiro = True
    planos = True
    relatorios = True
    configuracoes = True

    def tem_acesso(self, _):
        return True
