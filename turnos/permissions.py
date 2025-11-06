from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps

def es_secretaria(user):
    """Verifica si el usuario es staff (secretaria)"""
    return user.is_authenticated and user.is_staff

def es_paciente(user):
    """Verifica si el usuario es un paciente registrado"""
    return user.is_authenticated and hasattr(user, 'paciente') and not user.is_staff

def secretaria_required(function=None, redirect_field_name='next', login_url='/login/'):
    """
    Decorator para vistas que requieren permisos de secretaria
    """
    actual_decorator = user_passes_test(
        es_secretaria,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def paciente_required(function=None, redirect_field_name='next', login_url='/login/'):
    """
    Decorator para vistas que requieren ser paciente
    """
    actual_decorator = user_passes_test(
        es_paciente,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def verificar_permiso_turno(view_func):
    """
    Decorator que verifica que un paciente solo pueda ver/modificar sus propios turnos
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Si es staff, tiene acceso total
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Si no es staff, debe ser el dueño del turno
        turno_id = kwargs.get('turno_id') or kwargs.get('pk')
        if turno_id:
            from .models import Turno
            try:
                turno = Turno.objects.get(pk=turno_id)
                if turno.paciente and turno.paciente.user == request.user:
                    return view_func(request, *args, **kwargs)
                else:
                    raise PermissionDenied("No tenés permiso para acceder a este turno")
            except Turno.DoesNotExist:
                raise PermissionDenied("El turno no existe")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper