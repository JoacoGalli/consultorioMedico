from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date, datetime, timedelta
from .models import Paciente, Medico, Turno, DisponibilidadMedico, Cobertura
from .forms import (RegistroPacienteForm, EditarPerfilForm, TurnoForm, 
                   MedicoForm, DisponibilidadForm, TurnoSecretariaForm, CoberturaForm)
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

# ============= VISTAS DE COBERTURAS =============

@login_required
@secretaria_required
def gestionar_coberturas_view(request):
    """Listar y gestionar coberturas"""
    coberturas = Cobertura.objects.all().order_by('nombre')
    return render(request, 'secretaria/gestionar_coberturas.html', {'coberturas': coberturas})

@login_required
@secretaria_required
def crear_cobertura_view(request):
    """Crear nueva cobertura"""
    if request.method == 'POST':
        form = CoberturaForm(request.POST)
        if form.is_valid():
            cobertura = form.save()
            messages.success(request, f'Cobertura {cobertura.nombre} creada exitosamente.')
            return redirect('gestionar_coberturas')
    else:
        form = CoberturaForm()
    
    return render(request, 'secretaria/crear_cobertura.html', {'form': form})

@login_required
@secretaria_required
def editar_cobertura_view(request, cobertura_id):
    """Editar cobertura existente"""
    cobertura = get_object_or_404(Cobertura, pk=cobertura_id)
    
    if request.method == 'POST':
        form = CoberturaForm(request.POST, instance=cobertura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cobertura actualizada correctamente.')
            return redirect('gestionar_coberturas')
    else:
        form = CoberturaForm(instance=cobertura)
    
    return render(request, 'secretaria/editar_cobertura.html', {
        'form': form,
        'cobertura': cobertura
    })

# ============= CALENDARIO DE TURNOS =============

@login_required
@secretaria_required
def calendario_turnos_view(request):
    """Vista de calendario con turnos disponibles y ocupados"""
    from calendar import monthcalendar, month_name
    
    # Obtener mes y año de los parámetros (o usar actual)
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    medico_id = request.GET.get('medico')
    filtro = request.GET.get('filtro', 'todos')  # 'todos', 'disponibles', 'ocupados'
    
    # Obtener médico seleccionado
    medico = None
    if medico_id:
        try:
            medico = Medico.objects.get(pk=medico_id, activo=True)
        except Medico.DoesNotExist:
            pass
    
    # Generar calendario
    cal = monthcalendar(year, month)
    
    # Obtener turnos del mes
    primer_dia = date(year, month, 1)
    if month == 12:
        ultimo_dia = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = date(year, month + 1, 1) - timedelta(days=1)
    
    turnos_query = Turno.objects.filter(
        fecha__gte=primer_dia,
        fecha__lte=ultimo_dia,
        estado__in=['pendiente', 'confirmado']
    )
    
    if medico:
        turnos_query = turnos_query.filter(medico=medico)
    
    # Crear diccionario de turnos por fecha
    turnos_por_fecha = {}
    for turno in turnos_query:
        fecha_str = turno.fecha.strftime('%Y-%m-%d')
        if fecha_str not in turnos_por_fecha:
            turnos_por_fecha[fecha_str] = []
        turnos_por_fecha[fecha_str].append(turno)
    
    # Calcular disponibilidad por día
    dias_calendario = []
    for semana in cal:
        semana_datos = []
        for dia in semana:
            if dia == 0:
                semana_datos.append(None)
            else:
                fecha = date(year, month, dia)
                fecha_str = fecha.strftime('%Y-%m-%d')
                
                # Contar turnos del día
                turnos_dia = turnos_por_fecha.get(fecha_str, [])
                
                # Calcular slots disponibles si hay médico seleccionado
                slots_totales = 0
                slots_ocupados = len(turnos_dia)
                
                if medico:
                    # Obtener disponibilidades del médico para ese día de la semana
                    dia_semana = fecha.weekday()
                    disponibilidades = DisponibilidadMedico.objects.filter(
                        medico=medico,
                        dia_semana=dia_semana
                    )
                    
                    for disp in disponibilidades:
                        slots_totales += len(disp.generar_horarios())
                
                slots_disponibles = slots_totales - slots_ocupados if medico else None
                
                # Determinar estado del día
                if medico:
                    if slots_disponibles == 0 and slots_totales > 0:
                        estado = 'ocupado'
                    elif slots_disponibles > 0:
                        estado = 'disponible'
                    else:
                        estado = 'sin_horario'
                else:
                    if slots_ocupados > 0:
                        estado = 'con_turnos'
                    else:
                        estado = 'sin_turnos'
                
                semana_datos.append({
                    'dia': dia,
                    'fecha': fecha,
                    'estado': estado,
                    'turnos': turnos_dia,
                    'slots_disponibles': slots_disponibles,
                    'slots_totales': slots_totales,
                    'slots_ocupados': slots_ocupados
                })
        
        dias_calendario.append(semana_datos)
    
    # Navegación de meses
    mes_anterior = month - 1 if month > 1 else 12
    año_anterior = year if month > 1 else year - 1
    mes_siguiente = month + 1 if month < 12 else 1
    año_siguiente = year if month < 12 else year + 1
    
    medicos = Medico.objects.filter(activo=True)

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    context = {
        'calendario': dias_calendario,
        'mes': month_name[month],
        'año': year,
        'mes_num': month,
        'medico': medico,
        'medicos': medicos,
        'filtro': filtro,
        'mes_anterior': mes_anterior,
        'año_anterior': año_anterior,
        'mes_siguiente': mes_siguiente,
        'año_siguiente': año_siguiente,
        'dias_semana': dias_semana,
    }
    
    return render(request, 'secretaria/calendario_turnos.html', context)

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