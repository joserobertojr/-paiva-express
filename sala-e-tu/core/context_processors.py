from .models import SECOES


def user_perfil(request):
    eh_admin = False
    perfil = None
    user_perms = {s: False for s, _ in SECOES}

    if request.user.is_authenticated:
        if request.user.is_superuser:
            eh_admin = True
            user_perms = {s: True for s, _ in SECOES}
        else:
            try:
                perfil = request.user.perfil
                eh_admin = perfil.eh_admin
                user_perms = perfil.perms_dict()
            except Exception:
                pass

    return {
        'eh_admin': eh_admin,
        'perfil_usuario': perfil,
        'user_perms': user_perms,
    }
