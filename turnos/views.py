from contextlib import suppress
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CancelacionDiaForm,
    CancelacionHorarioForm,
    CoberturaForm,
    DisponibilidadForm,
    EditarPerfilForm,
    MedicoForm,
    RegistroPacienteForm,
    SobreturnoForm,
    TurnoForm,
    TurnoEditarForm,
    TurnoSecretariaForm,
)
from .models import (
    CancelacionDia,
    CancelacionHorario,
    Cobertura,
    DisponibilidadMedico,
    Medico,
    Paciente,
    Sobreturno,
    Turno,
)
from .permissions import paciente_required, secretaria_required, verificar_permiso_turno

# ============= VISTAS PÚBLICAS =============


def home(request):
    """Página de inicio - Redirige según tipo de usuario"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("secretaria_dashboard")
        elif hasattr(request.user, "paciente"):
            return redirect("paciente_dashboard")

    return render(request, "home.html")


def registro_view(request):
    """Registro de nuevos pacientes"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "¡Registro exitoso! Bienvenido/a.")
            return redirect("paciente_dashboard")
    else:
        form = RegistroPacienteForm()

    return render(request, "auth/registro.html", {"form": form})


def login_view(request):
    """Login para pacientes y secretaria"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verificar si debe cambiar password
            try:
                if hasattr(user, "paciente") and user.paciente.debe_cambiar_password:
                    login(request, user)
                    messages.warning(request, "Debés cambiar tu contraseña antes de continuar.")
                    return redirect("cambiar_password")
            except:
                pass

            login(request, user)
            messages.success(request, f"¡Bienvenido/a {user.get_full_name() or user.username}!")

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            elif user.is_staff:
                return redirect("secretaria_dashboard")
            else:
                return redirect("paciente_dashboard")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "auth/login.html")


def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("home")


@login_required
def cambiar_password_view(request):
    """Vista para cambiar contraseña obligatoria"""
    user = request.user

    # Verificar que sea un paciente y deba cambiar password
    if not hasattr(user, "paciente") or not user.paciente.debe_cambiar_password:
        return redirect("paciente_dashboard")

    if request.method == "POST":
        password_actual = request.POST.get("password_actual")
        password_nuevo = request.POST.get("password_nuevo")
        password_confirmar = request.POST.get("password_confirmar")

        if not user.check_password(password_actual):
            messages.error(request, "La contraseña actual es incorrecta.")
            return render(request, "auth/cambiar_password.html")

        if len(password_nuevo) < 8:
            messages.error(request, "La nueva contraseña debe tener al menos 8 caracteres.")
            return render(request, "auth/cambiar_password.html")

        if password_nuevo != password_confirmar:
            messages.error(request, "Las contraseñas nuevas no coinciden.")
            return render(request, "auth/cambiar_password.html")

        if password_nuevo == password_actual:
            messages.error(request, "La nueva contraseña debe ser diferente a la actual.")
            return render(request, "auth/cambiar_password.html")

        user.set_password(password_nuevo)
        user.save()

        user.paciente.debe_cambiar_password = False
        user.paciente.save()

        update_session_auth_hash(request, user)
        login(request, user)

        messages.success(request, "¡Contraseña cambiada exitosamente!")
        return redirect("paciente_dashboard")

    return render(request, "auth/cambiar_password.html")


# ============= VISTAS DE PACIENTE =============


@login_required
@paciente_required
def paciente_dashboard(request):
    """Dashboard del paciente"""
    paciente = request.user.paciente
    turnos_futuros = Turno.objects.filter(paciente=paciente, fecha__gte=date.today()).order_by(
        "fecha", "hora"
    )[:5]

    context = {"paciente": paciente, "turnos_futuros": turnos_futuros}
    return render(request, "paciente/dashboard.html", context)


@login_required
@paciente_required
def perfil_view(request):
    """Editar perfil del paciente"""
    paciente = request.user.paciente

    if request.method == "POST":
        form = EditarPerfilForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            # Actualizar datos del User
            user = request.user
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["nombre"]
            user.last_name = form.cleaned_data["apellido"]
            user.save()

            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("perfil")
    else:
        form = EditarPerfilForm(instance=paciente)

    return render(request, "paciente/perfil.html", {"form": form, "paciente": paciente})


@login_required
@paciente_required
def mis_turnos_view(request):
    """Ver todos los turnos del paciente"""
    paciente = request.user.paciente
    turnos = Turno.objects.filter(paciente=paciente).order_by("-fecha", "-hora")

    return render(request, "paciente/mis_turnos.html", {"turnos": turnos})


@login_required
@paciente_required
def reservar_turno_view(request):
    """Reservar un nuevo turno"""
    paciente = request.user.paciente

    if request.method == "POST":
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
            ).exists()

            if existe:
                messages.error(request, "Este horario ya está ocupado. Por favor elegí otro.")
            else:
                turno.save()
                messages.success(request, "¡Turno reservado exitosamente!")
                return redirect("mis_turnos")
    else:
        form = TurnoForm(paciente=paciente)

    medicos = Medico.objects.filter(activo=True)
    if paciente.cobertura:
        medicos = medicos.filter(coberturas=paciente.cobertura)

    return render(request, "paciente/reservar_turno.html", {"form": form, "medicos": medicos})


@login_required
@paciente_required
@verificar_permiso_turno
def cancelar_turno_view(request, turno_id):
    """Cancelar un turno"""
    turno = get_object_or_404(Turno, pk=turno_id)

    if not turno.puede_cancelar():
        messages.error(request, "No podés cancelar este turno (debe ser con 24hs de anticipación).")
        return redirect("mis_turnos")

    if request.method == "POST":
        turno.estado = "cancelado"
        turno.save()
        messages.success(request, "Turno cancelado correctamente.")
        return redirect("mis_turnos")

    return render(request, "paciente/cancelar_turno.html", {"turno": turno})


# ============= VISTAS DE SECRETARIA =============


@login_required
@secretaria_required
def secretaria_dashboard(request):
    """Dashboard de la secretaria"""
    turnos_hoy = Turno.objects.filter(fecha=date.today()).order_by("hora")
    medicos_activos = Medico.objects.filter(activo=True).count()
    pacientes_total = Paciente.objects.count()

    context = {
        "turnos_hoy": turnos_hoy,
        "medicos_activos": medicos_activos,
        "pacientes_total": pacientes_total,
    }
    return render(request, "secretaria/dashboard.html", context)


@login_required
@secretaria_required
def gestionar_medicos_view(request):
    """Listar y gestionar médicos"""
    medicos = Medico.objects.all().order_by("apellido", "nombre")
    return render(request, "secretaria/gestionar_medicos.html", {"medicos": medicos})


@login_required
@secretaria_required
def crear_medico_view(request):
    """Crear nuevo médico"""
    if request.method == "POST":
        form = MedicoForm(request.POST)
        if form.is_valid():
            medico = form.save()
            messages.success(request, f"Médico {medico.nombre_completo} creado exitosamente.")
            return redirect("gestionar_medicos")
    else:
        form = MedicoForm()

    return render(request, "secretaria/crear_medico.html", {"form": form})


@login_required
@secretaria_required
def editar_medico_view(request, medico_id):
    """Editar médico existente"""
    medico = get_object_or_404(Medico, pk=medico_id)

    if request.method == "POST":
        form = MedicoForm(request.POST, instance=medico)
        if form.is_valid():
            form.save()
            messages.success(request, "Médico actualizado correctamente.")
            return redirect("gestionar_medicos")
    else:
        form = MedicoForm(instance=medico)

    return render(request, "secretaria/editar_medico.html", {"form": form, "medico": medico})


@login_required
@secretaria_required
def gestionar_disponibilidad_view(request, medico_id):
    """Gestionar disponibilidad de un médico"""
    medico = get_object_or_404(Medico, pk=medico_id)
    disponibilidades = medico.disponibilidades.all()

    if request.method == "POST":
        # Verificar si es eliminación
        if "eliminar_disponibilidad" in request.POST:
            disp_id = request.POST.get("eliminar_disponibilidad")
            try:
                disp = DisponibilidadMedico.objects.get(pk=disp_id, medico=medico)
                disp.delete()
                messages.success(request, "Disponibilidad eliminada correctamente.")
            except DisponibilidadMedico.DoesNotExist:
                messages.error(request, "No se pudo eliminar la disponibilidad.")
            return redirect("gestionar_disponibilidad", medico_id=medico.id)

        # Si no, es creación
        form = DisponibilidadForm(request.POST)
        if form.is_valid():
            disp = form.save(commit=False)
            disp.medico = medico
            disp.save()
            messages.success(request, "Disponibilidad agregada correctamente.")
            return redirect("gestionar_disponibilidad", medico_id=medico.id)
    else:
        form = DisponibilidadForm()

    return render(
        request,
        "secretaria/gestionar_disponibilidad.html",
        {"medico": medico, "disponibilidades": disponibilidades, "form": form},
    )


@login_required
@secretaria_required
def gestionar_turnos_view(request):
    """Ver y gestionar todos los turnos"""
    turnos = Turno.objects.all().order_by("-fecha", "-hora")

    # Filtros
    medico_id = request.GET.get("medico")
    fecha = request.GET.get("fecha")

    if medico_id:
        turnos = turnos.filter(medico_id=medico_id)
    if fecha:
        turnos = turnos.filter(fecha=fecha)

    medicos = Medico.objects.filter(activo=True)

    return render(
        request, "secretaria/gestionar_turnos.html", {"turnos": turnos, "medicos": medicos}
    )


@login_required
@secretaria_required
def crear_turno_secretaria_view(request):
    """Crear turno desde secretaría (crea paciente si no existe)"""
    medico_prefill = None
    fecha_prefill = None
    hora_prefill = None

    if request.method == "GET":
        medico_id = request.GET.get("medico")
        fecha_str = request.GET.get("fecha")
        hora_str = request.GET.get("hora")

        if medico_id:
            try:
                medico_prefill = Medico.objects.get(pk=medico_id)
            except Medico.DoesNotExist:
                pass
        if fecha_str:
            fecha_prefill = fecha_str
        if hora_str:
            hora_prefill = hora_str

    if request.method == "POST":
        hora_str = request.POST.get("hora_turno")
        medico_id = request.POST.get("medico")
        fecha_str = request.POST.get("fecha")
        paciente_dni = request.POST.get("paciente_dni", "").strip()
        paciente_nombre = request.POST.get("paciente_nombre", "").strip()
        paciente_apellido = request.POST.get("paciente_apellido", "").strip()
        paciente_telefono = request.POST.get("paciente_telefono", "").strip()
        paciente_email = request.POST.get("paciente_email", "").strip()
        cobertura_nombre = request.POST.get("paciente_cobertura", "").strip()
        motivo = request.POST.get("motivo", "")
        notas = request.POST.get("notas_secretaria", "")
        paciente_id = request.POST.get("paciente", "") or None

        if not hora_str or not medico_id or not fecha_str:
            messages.error(request, "Debés seleccionar médico, fecha y horario.")
            form = TurnoSecretariaForm(request.POST)
            return render(request, "secretaria/crear_turno.html", {"form": form})

        if not paciente_nombre or not paciente_apellido:
            messages.error(request, "Debés ingresar nombre y apellido del paciente.")
            form = TurnoSecretariaForm(request.POST)
            return render(request, "secretaria/crear_turno.html", {"form": form})

        try:
            from datetime import datetime
            from django.contrib.auth.models import User

            turno_hora = datetime.strptime(hora_str, "%H:%M").time()
            turno_fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            medico = Medico.objects.get(pk=medico_id)

            # Determinar el paciente
            paciente_obj = None

            # Si hay paciente_id seleccionado (ya registrado)
            if paciente_id:
                try:
                    paciente_obj = Paciente.objects.get(pk=paciente_id)
                except Paciente.DoesNotExist:
                    pass

            # Si no hay paciente_id pero hay DNI, buscar si existe
            if not paciente_obj and paciente_dni:
                try:
                    paciente_obj = Paciente.objects.get(dni=paciente_dni)
                except Paciente.DoesNotExist:
                    pass

            # Si no existe el paciente, crearlo
            if not paciente_obj:
                if not paciente_email:
                    messages.error(
                        request, "Para crear un nuevo paciente necesitás ingresar un email."
                    )
                    form = TurnoSecretariaForm(request.POST)
                    return render(request, "secretaria/crear_turno.html", {"form": form})

                # Generar username único
                base_username = (
                    f"pac_{paciente_dni}" if paciente_dni else f"pac_{paciente_email.split('@')[0]}"
                )
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1

                # Crear contraseña simple temporal
                password_temporal = f"{paciente_nombre.lower()}123"

                # Crear usuario para el paciente
                user = User.objects.create_user(
                    username=username,
                    email=paciente_email,
                    first_name=paciente_nombre,
                    last_name=paciente_apellido,
                    password=password_temporal,
                )

                # Buscar cobertura
                cobertura_obj = None
                if cobertura_nombre:
                    try:
                        cobertura_obj = Cobertura.objects.get(
                            nombre__iexact=cobertura_nombre, activa=True
                        )
                    except Cobertura.DoesNotExist:
                        pass

                # Crear paciente con flag para cambiar password
                paciente_obj = Paciente.objects.create(
                    user=user,
                    dni=paciente_dni or f"EMP_{user.id}",
                    telefono=paciente_telefono,
                    cobertura=cobertura_obj,
                    debe_cambiar_password=True,
                )

                # Guardar credenciales para mostrar
                credenciales = f"Usuario: {username} | Contraseña temporal: {password_temporal}"
                messages.info(
                    request,
                    f"Se creó el paciente {paciente_nombre} {paciente_apellido}. {credenciales}",
                )

            # Crear el turno
            turno = Turno(
                medico=medico,
                fecha=turno_fecha,
                hora=turno_hora,
                paciente=paciente_obj,
                paciente_nombre=paciente_nombre,
                paciente_apellido=paciente_apellido,
                paciente_telefono=paciente_telefono,
                paciente_email=paciente_email,
                motivo=motivo,
                notas_secretaria=notas,
                creado_por=request.user,
            )

            existe = Turno.objects.filter(
                medico=turno.medico,
                fecha=turno.fecha,
                hora=turno.hora,
            ).exists()

            if existe:
                messages.error(request, "Este horario ya está ocupado.")
                form = TurnoSecretariaForm(request.POST)
                return render(request, "secretaria/crear_turno.html", {"form": form})

            turno.save()
            messages.success(
                request, f"Turno creado exitosamente para {paciente_nombre} {paciente_apellido}."
            )
            return redirect("gestionar_turnos")

        except Exception as e:
            messages.error(request, f"Error al crear turno: {str(e)}")
            form = TurnoSecretariaForm(request.POST)
            return render(request, "secretaria/crear_turno.html", {"form": form})
    else:
        form = TurnoSecretariaForm()

    return render(
        request,
        "secretaria/crear_turno.html",
        {
            "form": form,
            "medico_prefill": str(medico_prefill) if medico_prefill else None,
            "fecha_prefill": fecha_prefill,
            "hora_prefill": hora_prefill,
        },
    )


# ============= VISTAS DE COBERTURAS =============


@login_required
@secretaria_required
def gestionar_coberturas_view(request):
    """Listar y gestionar coberturas"""
    coberturas = Cobertura.objects.all().order_by("nombre")
    return render(request, "secretaria/gestionar_coberturas.html", {"coberturas": coberturas})


@login_required
@secretaria_required
def crear_cobertura_view(request):
    """Crear nueva cobertura"""
    if request.method == "POST":
        form = CoberturaForm(request.POST)
        if form.is_valid():
            cobertura = form.save()
            messages.success(request, f"Cobertura {cobertura.nombre} creada exitosamente.")
            return redirect("gestionar_coberturas")
    else:
        form = CoberturaForm()

    return render(request, "secretaria/crear_cobertura.html", {"form": form})


@login_required
@secretaria_required
def editar_cobertura_view(request, cobertura_id):
    """Editar cobertura existente"""
    cobertura = get_object_or_404(Cobertura, pk=cobertura_id)

    if request.method == "POST":
        form = CoberturaForm(request.POST, instance=cobertura)
        if form.is_valid():
            form.save()
            messages.success(request, "Cobertura actualizada correctamente.")
            return redirect("gestionar_coberturas")
    else:
        form = CoberturaForm(instance=cobertura)

    return render(
        request, "secretaria/editar_cobertura.html", {"form": form, "cobertura": cobertura}
    )


# ============= CALENDARIO DE TURNOS =============


@login_required
@secretaria_required
def calendario_turnos_view(request):
    """Vista de calendario con turnos disponibles y ocupados"""
    from calendar import month_name, monthcalendar

    # Obtener mes y año de los parámetros (o usar actual)
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    medico_id = request.GET.get("medico")
    filtro = request.GET.get("filtro", "todos")  # 'todos', 'disponibles', 'ocupados'

    # Obtener médico seleccionado
    medico = None
    if medico_id:
        with suppress(Medico.DoesNotExist):
            medico = Medico.objects.get(pk=medico_id, activo=True)

    # Generar calendario
    cal = monthcalendar(year, month)

    # Obtener turnos del mes
    primer_dia = date(year, month, 1)
    if month == 12:
        ultimo_dia = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = date(year, month + 1, 1) - timedelta(days=1)

    turnos_query = Turno.objects.filter(fecha__gte=primer_dia, fecha__lte=ultimo_dia)

    if medico:
        turnos_query = turnos_query.filter(medico=medico)

    # Crear diccionario de turnos por fecha
    turnos_por_fecha = {}
    for turno in turnos_query:
        fecha_str = turno.fecha.strftime("%Y-%m-%d")
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
                fecha_str = fecha.strftime("%Y-%m-%d")

                # Contar turnos del día
                turnos_dia = turnos_por_fecha.get(fecha_str, [])

                # Calcular slots disponibles si hay médico seleccionado
                slots_totales = 0
                slots_ocupados = len(turnos_dia)

                if medico:
                    # Obtener disponibilidades del médico para ese día de la semana
                    dia_semana = fecha.weekday()
                    disponibilidades = DisponibilidadMedico.objects.filter(
                        medico=medico, dia_semana=dia_semana
                    )

                    try:
                        for disp in disponibilidades:
                            horarios = disp.generar_horarios()
                            if horarios:
                                slots_totales += len(horarios)
                    except Exception:
                        slots_totales = 0

                slots_disponibles = max(0, slots_totales - slots_ocupados) if medico else 0

                # Determinar estado del día
                if medico:
                    if slots_totales == 0:
                        estado = "sin_horario"
                    elif slots_disponibles == 0:
                        estado = "completo"
                    else:
                        estado = "disponible"
                else:
                    estado = "con_turnos" if slots_ocupados > 0 else "sin_turnos"

                semana_datos.append(
                    {
                        "dia": dia,
                        "fecha": fecha,
                        "fecha_str": fecha_str,
                        "estado": estado,
                        "turnos": turnos_dia,
                        "slots_disponibles": slots_disponibles,
                        "slots_totales": slots_totales,
                        "slots_ocupados": slots_ocupados,
                    }
                )

        dias_calendario.append(semana_datos)

    # Navegación de meses
    mes_anterior = month - 1 if month > 1 else 12
    año_anterior = year if month > 1 else year - 1
    mes_siguiente = month + 1 if month < 12 else 1
    año_siguiente = year if month < 12 else year + 1

    medicos = Medico.objects.filter(activo=True)

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    context = {
        "calendario": dias_calendario,
        "mes": month_name[month],
        "año": year,
        "mes_num": month,
        "medico": medico,
        "medicos": medicos,
        "filtro": filtro,
        "mes_anterior": mes_anterior,
        "año_anterior": año_anterior,
        "mes_siguiente": mes_siguiente,
        "año_siguiente": año_siguiente,
        "dias_semana": dias_semana,
        "date_today": today,
    }

    return render(request, "secretaria/calendario_turnos.html", context)


# ============= AJAX ENDPOINTS =============


@login_required
def obtener_horarios_disponibles(request):
    """Endpoint AJAX para obtener horarios disponibles para un día"""
    medico_id = request.GET.get("medico_id")
    fecha_str = request.GET.get("fecha")

    if not medico_id or not fecha_str:
        return JsonResponse({"error": "Faltan parámetros"}, status=400)

    try:
        medico = Medico.objects.get(pk=medico_id)
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        dia_semana = fecha.weekday()

        disponibilidades = DisponibilidadMedico.objects.filter(medico=medico, dia_semana=dia_semana)
        horarios_disponibles = []
        horarios_ocupados = []

        for disp in disponibilidades:
            hora_actual = datetime.combine(fecha, disp.hora_inicio)
            hora_fin = datetime.combine(fecha, disp.hora_fin)

            while hora_actual < hora_fin:
                hora_time = hora_actual.time()
                turno_existe = Turno.objects.filter(
                    medico=medico, fecha=fecha, hora=hora_time
                ).exists()

                if turno_existe:
                    horarios_ocupados.append(hora_actual.strftime("%H:%M"))
                else:
                    horarios_disponibles.append(hora_actual.strftime("%H:%M"))

                hora_actual += timedelta(minutes=disp.duracion_turno)

        return JsonResponse(
            {
                "horarios_disponibles": sorted(horarios_disponibles),
                "horarios_ocupados": sorted(horarios_ocupados),
                "total_disponibles": len(horarios_disponibles),
                "total_ocupados": len(horarios_ocupados),
            }
        )

    except Medico.DoesNotExist:
        return JsonResponse({"error": "Médico no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ============= CONFIRMAR TURNO (PACIENTE) =============


@login_required
@paciente_required
def confirmar_turno_view(request, turno_id):
    """Paciente confirma su turno"""
    turno = get_object_or_404(Turno, pk=turno_id, paciente=request.user.paciente)

    if request.method == "POST":
        turno.confirmado = True
        turno.save()
        messages.success(request, "¡Turno confirmado! Se envió un email de confirmación.")
        return redirect("mis_turnos")

    return render(request, "paciente/confirmar_turno.html", {"turno": turno})


# ============= EDITAR TURNO (SECRETARIA) =============


@login_required
@secretaria_required
def editar_turno_view(request, turno_id):
    """Editar un turno existente"""
    turno = get_object_or_404(Turno, pk=turno_id)

    if request.method == "POST":
        medico_id = request.POST.get("medico")
        fecha_str = request.POST.get("fecha")
        hora_str = request.POST.get("hora")
        paciente_nombre = request.POST.get("paciente_nombre", "").strip()
        paciente_apellido = request.POST.get("paciente_apellido", "").strip()
        paciente_telefono = request.POST.get("paciente_telefono", "").strip()
        paciente_email = request.POST.get("paciente_email", "").strip()
        motivo = request.POST.get("motivo", "")
        notas = request.POST.get("notas_secretaria", "")

        if not medico_id or not fecha_str or not hora_str:
            messages.error(request, "Debés completar médico, fecha y horario.")
            form = TurnoEditarForm(request.POST, instance=turno)
            return render(request, "secretaria/editar_turno.html", {"form": form, "turno": turno})

        try:
            from datetime import datetime

            turno_hora = datetime.strptime(hora_str, "%H:%M").time()
            turno_fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            medico = Medico.objects.get(pk=medico_id)

            # Check for duplicate (excluding current turn)
            existe = (
                Turno.objects.filter(
                    medico=medico,
                    fecha=turno_fecha,
                    hora=turno_hora,
                )
                .exclude(pk=turno.pk)
                .exists()
            )

            if existe:
                messages.error(request, "Ese horario ya está ocupado.")
                form = TurnoEditarForm(request.POST, instance=turno)
                return render(
                    request, "secretaria/editar_turno.html", {"form": form, "turno": turno}
                )

            # Update turno
            turno.medico = medico
            turno.fecha = turno_fecha
            turno.hora = turno_hora
            turno.paciente_nombre = paciente_nombre
            turno.paciente_apellido = paciente_apellido
            turno.paciente_telefono = paciente_telefono
            turno.paciente_email = paciente_email
            turno.motivo = motivo
            turno.notas_secretaria = notas
            turno.save()

            messages.success(request, "Turno actualizado correctamente.")
            return redirect("gestionar_turnos")

        except Exception as e:
            messages.error(request, f"Error al actualizar turno: {str(e)}")
            form = TurnoEditarForm(request.POST, instance=turno)
            return render(request, "secretaria/editar_turno.html", {"form": form, "turno": turno})
    else:
        form = TurnoEditarForm(instance=turno)

    return render(request, "secretaria/editar_turno.html", {"form": form, "turno": turno})


@login_required
@secretaria_required
def eliminar_turno_view(request, turno_id):
    """Eliminar un turno"""
    turno = get_object_or_404(Turno, pk=turno_id)

    if request.method == "POST":
        turno.delete()
        messages.success(request, "Turno eliminado correctamente.")
        return redirect("gestionar_turnos")

    return render(request, "secretaria/eliminar_turno.html", {"turno": turno})


# ============= SOBRE TURNOS =============


@login_required
@secretaria_required
def crear_sobreturno_view(request):
    """Crear un sobreturno (turno fuera de horario normal)"""
    if request.method == "POST":
        form = SobreturnoForm(request.POST)
        if form.is_valid():
            sobreturno = form.save(commit=False)
            sobreturno.creado_por = request.user
            sobreturno.save()
            messages.success(request, "Sobreturno creado exitosamente.")
            return redirect("secretaria_dashboard")
    else:
        form = SobreturnoForm()

    return render(request, "secretaria/crear_sobreturno.html", {"form": form})


# ============= CANCELACIONES =============


@login_required
@secretaria_required
def cancelar_dia_view(request):
    """Cancelar un día completo (feriado, licencia)"""
    if request.method == "POST":
        form = CancelacionDiaForm(request.POST)
        if form.is_valid():
            cancelacion = form.save(commit=False)
            cancelacion.creado_por = request.user
            cancelacion.save()
            messages.success(request, "Día cancelado correctamente. Se notificará a los pacientes.")
            return redirect("calendario_turnos")
    else:
        form = CancelacionDiaForm()

    return render(request, "secretaria/cancelar_dia.html", {"form": form})


@login_required
@secretaria_required
def cancelar_horario_view(request):
    """Cancelar un rango horario específico"""
    if request.method == "POST":
        form = CancelacionHorarioForm(request.POST)
        if form.is_valid():
            cancelacion = form.save(commit=False)
            cancelacion.creado_por = request.user
            cancelacion.save()
            messages.success(request, "Horario cancelado correctamente.")
            return redirect("calendario_turnos")
    else:
        form = CancelacionHorarioForm()

    return render(request, "secretaria/cancelar_horario.html", {"form": form})


@login_required
@secretaria_required
def gestionar_cancelaciones_view(request):
    """Ver y gestionar cancelaciones de día y horario"""
    year = int(request.GET.get("year", date.today().year))
    month = int(request.GET.get("month", date.today().month))

    cancelaciones_dia = CancelacionDia.objects.filter(fecha__year=year, fecha__month=month)
    cancelaciones_horario = CancelacionHorario.objects.filter(fecha__year=year, fecha__month=month)

    medicos = Medico.objects.filter(activo=True)

    context = {
        "cancelaciones_dia": cancelaciones_dia,
        "cancelaciones_horario": cancelaciones_horario,
        "medicos": medicos,
        "year": year,
        "month": month,
    }
    return render(request, "secretaria/gestionar_cancelaciones.html", context)


@login_required
@secretaria_required
def eliminar_cancelacion_dia_view(request, cancelacion_id):
    """Eliminar una cancelación de día"""
    cancelacion = get_object_or_404(CancelacionDia, pk=cancelacion_id)

    if request.method == "POST":
        cancelacion.delete()
        messages.success(request, "Cancelación de día eliminada.")
        return redirect("gestionar_cancelaciones")

    return render(request, "secretaria/eliminar_cancelacion_dia.html", {"cancelacion": cancelacion})


@login_required
@secretaria_required
def eliminar_cancelacion_horario_view(request, cancelacion_id):
    """Eliminar una cancelación de horario"""
    cancelacion = get_object_or_404(CancelacionHorario, pk=cancelacion_id)

    if request.method == "POST":
        cancelacion.delete()
        messages.success(request, "Cancelación de horario eliminada.")
        return redirect("gestionar_cancelaciones")

    return render(
        request, "secretaria/eliminar_cancelacion_horario.html", {"cancelacion": cancelacion}
    )


# ============= API ENDPOINTS ADICIONALES =============


def buscar_paciente_por_dni(request):
    """API para buscar paciente por DNI"""
    dni = request.GET.get("dni", "")
    if not dni:
        return JsonResponse({"error": "DNI requerido"}, status=400)

    try:
        paciente = Paciente.objects.get(dni=dni)
        cobertura_nombre = ""
        if paciente.cobertura:
            try:
                cobertura_nombre = paciente.cobertura.nombre
            except:
                pass

        return JsonResponse(
            {
                "encontrado": True,
                "paciente": {
                    "id": paciente.id,
                    "nombre": paciente.user.first_name or "",
                    "apellido": paciente.user.last_name or "",
                    "dni": paciente.dni,
                    "telefono": paciente.telefono or "",
                    "cobertura": cobertura_nombre,
                    "email": paciente.user.email or "",
                },
            }
        )
    except Paciente.DoesNotExist:
        return JsonResponse({"encontrado": False})


def obtener_disponibilidad_calendario(request):
    """API para obtener disponibilidad del calendario mensual"""
    year = int(request.GET.get("year", date.today().year))
    month = int(request.GET.get("month", date.today().month))
    medico_id = request.GET.get("medico")

    if not medico_id:
        return JsonResponse({"error": "Médico requerido"}, status=400)

    primer_dia = date(year, month, 1)
    if month == 12:
        ultimo_dia = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = date(year, month + 1, 1) - timedelta(days=1)

    disponibilidades = DisponibilidadMedico.objects.filter(medico_id=medico_id)
    disp_por_dia = {}
    for disp in disponibilidades:
        disp_por_dia[disp.dia_semana] = disp

    turnos_del_mes = Turno.objects.filter(
        medico_id=medico_id, fecha__gte=primer_dia, fecha__lte=ultimo_dia
    )

    turnos_por_fecha = {}
    for turno in turnos_del_mes:
        fecha_str = turno.fecha.isoformat()
        if fecha_str not in turnos_por_fecha:
            turnos_por_fecha[fecha_str] = 0
        turnos_por_fecha[fecha_str] += 1

    today = date.today()
    disponibilidad_dias = {}

    for day_num in range(1, ultimo_dia.day + 1):
        fecha_actual = date(year, month, day_num)
        fecha_str = fecha_actual.isoformat()
        dia_semana = fecha_actual.weekday()

        slots_totales = 0
        if dia_semana in disp_por_dia:
            disp = disp_por_dia[dia_semana]
            hora_actual = datetime.combine(fecha_actual, disp.hora_inicio)
            hora_fin = datetime.combine(fecha_actual, disp.hora_fin)
            while hora_actual < hora_fin:
                slots_totales += 1
                hora_actual += timedelta(minutes=disp.duracion_turno)

        slots_ocupados = turnos_por_fecha.get(fecha_str, 0)
        slots_disponibles = max(0, slots_totales - slots_ocupados)

        if fecha_actual < today:
            estado = "pasado"
        elif slots_totales == 0:
            estado = "sin_horario"
        elif slots_disponibles == 0:
            estado = "completo"
        else:
            estado = "disponible"

        disponibilidad_dias[fecha_str] = {
            "dia": day_num,
            "dia_semana": dia_semana,
            "slots_totales": slots_totales,
            "slots_ocupados": slots_ocupados,
            "slots_disponibles": slots_disponibles,
            "estado": estado,
        }

    return JsonResponse(
        {
            "year": year,
            "month": month,
            "disponibilidad": disponibilidad_dias,
        }
    )


def obtener_slots_del_dia(request):
    """API para obtener todos los slots de un día específico"""
    medico_id = request.GET.get("medico_id")
    fecha_str = request.GET.get("fecha")

    if not medico_id or not fecha_str:
        return JsonResponse({"error": "Parámetros requeridos"}, status=400)

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        medico = Medico.objects.get(pk=medico_id)
        dia_semana = fecha.weekday()

        disponibilidades = DisponibilidadMedico.objects.filter(medico=medico, dia_semana=dia_semana)

        slots = []
        turnos_del_dia = Turno.objects.filter(medico=medico, fecha=fecha)
        turnos_dict = {t.hora.strftime("%H:%M"): t for t in turnos_del_dia}

        for disp in disponibilidades:
            hora_actual = datetime.combine(fecha, disp.hora_inicio)
            hora_fin = datetime.combine(fecha, disp.hora_fin)

            while hora_actual < hora_fin:
                hora_str = hora_actual.strftime("%H:%M")
                turno = turnos_dict.get(hora_str)

                if turno:
                    slots.append(
                        {
                            "hora": hora_str,
                            "disponible": False,
                            "turno_id": turno.id,
                            "paciente": turno.paciente.nombre_completo
                            if turno.paciente
                            else turno.paciente_nombre,
                        }
                    )
                else:
                    slots.append(
                        {
                            "hora": hora_str,
                            "disponible": True,
                            "turno_id": None,
                            "paciente": None,
                        }
                    )

                hora_actual += timedelta(minutes=disp.duracion_turno)

        return JsonResponse(
            {
                "fecha": fecha_str,
                "medico": str(medico),
                "slots": slots,
                "total_disponibles": len([s for s in slots if s["disponible"]]),
            }
        )

    except Medico.DoesNotExist:
        return JsonResponse({"error": "Médico no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
