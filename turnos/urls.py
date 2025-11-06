from django.urls import path
from . import views

urlpatterns = [
    # Vistas públicas
    path('', views.home, name='home'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Vistas de paciente
    path('paciente/', views.paciente_dashboard, name='paciente_dashboard'),
    path('paciente/perfil/', views.perfil_view, name='perfil'),
    path('paciente/mis-turnos/', views.mis_turnos_view, name='mis_turnos'),
    path('paciente/reservar-turno/', views.reservar_turno_view, name='reservar_turno'),
    path('paciente/cancelar-turno/<int:turno_id>/', views.cancelar_turno_view, name='cancelar_turno'),
    
    # Vistas de secretaria
    path('secretaria/', views.secretaria_dashboard, name='secretaria_dashboard'),
    path('secretaria/medicos/', views.gestionar_medicos_view, name='gestionar_medicos'),
    path('secretaria/medicos/crear/', views.crear_medico_view, name='crear_medico'),
    path('secretaria/medicos/<int:medico_id>/editar/', views.editar_medico_view, name='editar_medico'),
    path('secretaria/medicos/<int:medico_id>/disponibilidad/', views.gestionar_disponibilidad_view, name='gestionar_disponibilidad'),
    path('secretaria/turnos/', views.gestionar_turnos_view, name='gestionar_turnos'),
    path('secretaria/turnos/crear/', views.crear_turno_secretaria_view, name='crear_turno_secretaria'),
    
    # API endpoints
    path('api/horarios-disponibles/', views.obtener_horarios_disponibles, name='obtener_horarios'),
]