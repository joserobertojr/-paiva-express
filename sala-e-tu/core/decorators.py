from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.perfil.eh_admin:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('core:dashboard')
    return wrapper
