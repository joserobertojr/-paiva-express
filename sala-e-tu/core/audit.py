from .models import AuditLog


def log(request, acao, modulo, descricao):
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
    )
    usuario = request.user if request.user.is_authenticated else None
    AuditLog.objects.create(
        usuario=usuario,
        acao=acao,
        modulo=modulo,
        descricao=descricao,
        ip=ip or None,
    )
