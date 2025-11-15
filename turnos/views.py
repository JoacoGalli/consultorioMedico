from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date, datetime, timedelta
from .models import Paciente, Medico, Turno, DisponibilidadMedico, Cobertura
from .forms import (RegistroPacienteForm, EditarPerfilForm, TurnoForm, 
                   MedicoForm, DisponibilidadForm, TurnoSecretariaForm)
from .permissions import secretaria_required, paciente_required, verificar_permiso_turno
from django.http import JsonResponse

# ============= VISTAS PÚBLICAS =============

def home(request):
    """Página de inicio - Redirige según tipo de usuario"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('secretaria_dashboard')
        elif hasattr(request.user, 'paciente'):
            return redirect('paciente_dashboard')
    
    return render(request, 'home.html')

def registro_view(request):
    """Registro de nuevos pacientes"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido/a.')
            return redirect('paciente_dashboard')
    else:
        form = RegistroPacienteForm()
    
    return render(request, 'auth/registro.html', {'form': form})

def login_view(request):
    """Login para pacientes y secretaria"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a {user.get_full_name() or user.username}!')
            
            # Redirigir según tipo de usuario
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            elif user.is_staff:
                return redirect('secretaria_dashboard')
            else:
                return redirect('paciente_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'auth/login.html')

def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('home')

# ============= VISTAS DE PACIENTE =============

@login_required
@paciente_required
def paciente_dashboard(request):
    """Dashboard del paciente"""
    paciente = request.user.paciente
    turnos_futuros = Turno.objects.filter(
        paciente=paciente,
        fecha__gte=date.today(),
        estado__in=['pendiente', 'confirmado']
    ).order_by('fecha', 'hora')[:5]
    
    context = {
        'paciente': paciente,
        'turnos_futuros': turnos_futuros
    }
    return render(request, 'paciente/dashboard.html', context)

@login_required
@paciente_required
def perfil_view(request):
    """Editar perfil del paciente"""
    paciente = request.user.paciente
    
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            # Actualizar datos del User
            user = request.user
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['nombre']
            user.last_name = form.cleaned_data['apellido']
            user.save()
            
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        form = EditarPerfilForm(instance=paciente)
    
    return render(request, 'paciente/perfil.html', {'form': form, 'paciente': paciente})

@login_required
@paciente_required
def mis_turnos_view(request):
    """Ver todos los turnos del paciente"""
    paciente = request.user.paciente
    turnos = Turno.objects.filter(paciente=paciente).order_by('-fecha', '-hora')
    
    return render(request, 'paciente/mis_turnos.html', {'turnos': turnos})

@login_required
@paciente_required
def reservar_turno_view(request):
    """Reservar un nuevo turno"""
    paciente = request.user.paciente
    
    if request.method == 'POST':
        form = TurnoForm(request.POST, paciente=paciente)
        if form.is_valid():
            turno = form.save(commit=False)
            turno.paciente = paciente
            turno.creado_por = request.user
            
            # Verificar que el turno no esté ocupado
            existe = Turno.objects.filter(
                medico=turno.medico,
                fecha=turno.fecha,
                hora=turno.hora,
                estado__in=['pendiente', 'confirmado']
            ).exists()
            
            if existe:
                messages.error(request, 'Este horario ya está ocupado. Por favor elegí otro.')
            else:
                turno.save()
                messages.success(request, '¡Turno reservado exitosamente!')
                return redirect('mis_turnos')
    else:
        form = TurnoForm(paciente=paciente)
    
    medicos = Medico.objects.filter(activo=True)
    if paciente.cobertura:
        medicos = medicos.filter(coberturas=paciente.cobertura)
    
    return render(request, 'paciente/reservar_turno.html', {
        'form': form,
        'medicos': medicos
    })

@login_required
@paciente_required
@verificar_permiso_turno
def cancelar_turno_view(request, turno_id):
    """Cancelar un turno"""
    turno = get_object_or_404(Turno, pk=turno_id)
    
    if not turno.puede_cancelar():
        messages.error(request, 'No podés cancelar este turno (debe ser con 24hs de anticipación).')
        return redirect('mis_turnos')
    
    if request.method == 'POST':
        turno.estado = 'cancelado'
        turno.save()
        messages.success(request, 'Turno cancelado correctamente.')
        return redirect('mis_turnos')
    
    return render(request, 'paciente/cancelar_turno.html', {'turno': turno})

# ============= VISTAS DE SECRETARIA =============

@login_required
@secretaria_required
def secretaria_dashboard(request):
    """Dashboard de la secretaria"""
    turnos_hoy = Turno.objects.filter(fecha=date.today()).order_by('hora')
    medicos_activos = Medico.objects.filter(activo=True).count()
    pacientes_total = Paciente.objects.count()
    
    context = {
        'turnos_hoy': turnos_hoy,
        'medicos_activos': medicos_activos,
        'pacientes_total': pacientes_total
    }
    return render(request, 'secretaria/dashboard.html', context)

@login_required
@secretaria_required
def gestionar_medicos_view(request):
    """Listar y gestionar médicos"""
    medicos = Medico.objects.all().order_by('apellido', 'nombre')
    return render(request, 'secretaria/gestionar_medicos.html', {'medicos': medicos})

@login_required
@secretaria_required
def crear_medico_view(request):
    """Crear nuevo médico"""
    if request.method == 'POST':
        form = MedicoForm(request.POST)
        if form.is_valid():
            medico = form.save()
            messages.success(request, f'Médico {medico.nombre_completo} creado exitosamente.')
            return redirect('gestionar_medicos')
    else:
        form = MedicoForm()
    
    return render(request, 'secretaria/crear_medico.html', {'form': form})

@login_required
@secretaria_required
def editar_medico_view(request, medico_id):
    """Editar médico existente"""
    medico = get_object_or_404(Medico, pk=medico_id)
    
    if request.method == 'POST':
        form = MedicoForm(request.POST, instance=medico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Médico actualizado correctamente.')
            return redirect('gestionar_medicos')
    else:
        form = MedicoForm(instance=medico)
    
    return render(request, 'secretaria/editar_medico.html', {
        'form': form,
        'medico': medico
    })

@login_required
@secretaria_required
def gestionar_disponibilidad_view(request, medico_id):
    """Gestionar disponibilidad de un médico"""
    medico = get_object_or_404(Medico, pk=medico_id)
    disponibilidades = medico.disponibilidades.all()
    
    if request.method == 'POST':
        # Verificar si es eliminación
        if 'eliminar_disponibilidad' in request.POST:
            disp_id = request.POST.get('eliminar_disponibilidad')
            try:
                disp = DisponibilidadMedico.objects.get(pk=disp_id, medico=medico)
                disp.delete()
                messages.success(request, 'Disponibilidad eliminada correctamente.')
            except DisponibilidadMedico.DoesNotExist:
                messages.error(request, 'No se pudo eliminar la disponibilidad.')
            return redirect('gestionar_disponibilidad', medico_id=medico.id)
        
        # Si no, es creación
        form = DisponibilidadForm(request.POST)
        if form.is_valid():
            disp = form.save(commit=False)
            disp.medico = medico
            disp.save()
            messages.success(request, 'Disponibilidad agregada correctamente.')
            return redirect('gestionar_disponibilidad', medico_id=medico.id)
    else:
        form = DisponibilidadForm()
    
    return render(request, 'secretaria/gestionar_disponibilidad.html', {
        'medico': medico,
        'disponibilidades': disponibilidades,
        'form': form
    })

@login_required
@secretaria_required
def gestionar_turnos_view(request):
    """Ver y gestionar todos los turnos"""
    turnos = Turno.objects.all().order_by('-fecha', '-hora')
    
    # Filtros
    medico_id = request.GET.get('medico')
    fecha = request.GET.get('fecha')
    estado = request.GET.get('estado')
    
    if medico_id:
        turnos = turnos.filter(medico_id=medico_id)
    if fecha:
        turnos = turnos.filter(fecha=fecha)
    if estado:
        turnos = turnos.filter(estado=estado)
    
    medicos = Medico.objects.filter(activo=True)
    
    return render(request, 'secretaria/gestionar_turnos.html', {
        'turnos': turnos,
        'medicos': medicos
    })

@login_required
@secretaria_required
def crear_turno_secretaria_view(request):
    """Crear turno desde secretaría (para pacientes no registrados)"""
    if request.method == 'POST':
        form = TurnoSecretariaForm(request.POST)
        if form.is_valid():
            turno = form.save(commit=False)
            turno.creado_por = request.user
            
            # Verificar que no esté ocupado
            existe = Turno.objects.filter(
                medico=turno.medico,
                fecha=turno.fecha,
                hora=turno.hora,
                estado__in=['pendiente', 'confirmado']
            ).exclude(pk=turno.pk if turno.pk else None).exists()
            
            if existe:
                messages.error(request, 'Este horario ya está ocupado.')
            else:
                turno.save()
                messages.success(request, 'Turno creado exitosamente.')
                return redirect('gestionar_turnos')
    else:
        form = TurnoSecretariaForm()
    
    return render(request, 'secretaria/crear_turno.html', {'form': form})

# ============= AJAX ENDPOINTS =============

@login_required
def obtener_horarios_disponibles(request):
    """Endpoint AJAX para obtener horarios disponibles"""
    medico_id = request.GET.get('medico_id')
    fecha_str = request.GET.get('fecha')
    
    if not medico_id or not fecha_str:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    try:
        medico = Medico.objects.get(pk=medico_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        dia_semana = fecha.weekday()
        
        # Obtener disponibilidad del médico para ese día
        disponibilidades = DisponibilidadMedico.objects.filter(
            medico=medico,
            dia_semana=dia_semana
        )
        
        horarios_disponibles = []
        
        for disp in disponibilidades:
            horarios = disp.generar_horarios()
            
            # Filtrar horarios ya ocupados
            for hora in horarios:
                ocupado = Turno.objects.filter(
                    medico=medico,
                    fecha=fecha,
                    hora=hora,
                    estado__in=['pendiente', 'confirmado']
                ).exists()
                
                if not ocupado:
                    horarios_disponibles.append(hora.strftime('%H:%M'))
        
        return JsonResponse({'horarios': sorted(horarios_disponibles)})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)