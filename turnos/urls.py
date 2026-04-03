from django.urls import path

from . import views

urlpatterns = [
    # Vistas públicas
    path("", views.home, name="home"),
    path("registro/", views.registro_view, name="registro"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cambiar-password/", views.cambiar_password_view, name="cambiar_password"),
    # Vistas de paciente
    path("paciente/", views.paciente_dashboard, name="paciente_dashboard"),
    path("paciente/perfil/", views.perfil_view, name="perfil"),
    path("paciente/mis-turnos/", views.mis_turnos_view, name="mis_turnos"),
    path("paciente/reservar-turno/", views.reservar_turno_view, name="reservar_turno"),
    path(
        "paciente/cancelar-turno/<int:turno_id>/", views.cancelar_turno_view, name="cancelar_turno"
    ),
    path(
        "paciente/confirmar-turno/<int:turno_id>/",
        views.confirmar_turno_view,
        name="confirmar_turno",
    ),
    # Vistas de secretaria
    path("secretaria/", views.secretaria_dashboard, name="secretaria_dashboard"),
    # Médicos
    path("secretaria/medicos/", views.gestionar_medicos_view, name="gestionar_medicos"),
    path("secretaria/medicos/crear/", views.crear_medico_view, name="crear_medico"),
    path(
        "secretaria/medicos/<int:medico_id>/editar/", views.editar_medico_view, name="editar_medico"
    ),
    path(
        "secretaria/medicos/<int:medico_id>/disponibilidad/",
        views.gestionar_disponibilidad_view,
        name="gestionar_disponibilidad",
    ),
    # Turnos
    path("secretaria/turnos/", views.gestionar_turnos_view, name="gestionar_turnos"),
    path(
        "secretaria/turnos/crear/", views.crear_turno_secretaria_view, name="crear_turno_secretaria"
    ),
    path("secretaria/turnos/<int:turno_id>/editar/", views.editar_turno_view, name="editar_turno"),
    path(
        "secretaria/turnos/<int:turno_id>/eliminar/",
        views.eliminar_turno_view,
        name="eliminar_turno",
    ),
    path("secretaria/sobreturnos/crear/", views.crear_sobreturno_view, name="crear_sobreturno"),
    # Coberturas
    path("secretaria/coberturas/", views.gestionar_coberturas_view, name="gestionar_coberturas"),
    path("secretaria/coberturas/crear/", views.crear_cobertura_view, name="crear_cobertura"),
    path(
        "secretaria/coberturas/<int:cobertura_id>/editar/",
        views.editar_cobertura_view,
        name="editar_cobertura",
    ),
    # Calendario y cancelaciones
    path("secretaria/calendario/", views.calendario_turnos_view, name="calendario_turnos"),
    path("secretaria/cancelar-dia/", views.cancelar_dia_view, name="cancelar_dia"),
    path("secretaria/cancelar-horario/", views.cancelar_horario_view, name="cancelar_horario"),
    path(
        "secretaria/cancelaciones/",
        views.gestionar_cancelaciones_view,
        name="gestionar_cancelaciones",
    ),
    path(
        "secretaria/cancelaciones/dia/<int:cancelacion_id>/eliminar/",
        views.eliminar_cancelacion_dia_view,
        name="eliminar_cancelacion_dia",
    ),
    path(
        "secretaria/cancelaciones/horario/<int:cancelacion_id>/eliminar/",
        views.eliminar_cancelacion_horario_view,
        name="eliminar_cancelacion_horario",
    ),
    # API endpoints
    path("api/horarios-disponibles/", views.obtener_horarios_disponibles, name="obtener_horarios"),
    path("api/buscar-paciente/", views.buscar_paciente_por_dni, name="buscar_paciente"),
    path(
        "api/disponibilidad-calendario/",
        views.obtener_disponibilidad_calendario,
        name="disponibilidad_calendario",
    ),
    path(
        "api/slots-del-dia/",
        views.obtener_slots_del_dia,
        name="slots_del_dia",
    ),
]
