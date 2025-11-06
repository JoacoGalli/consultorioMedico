from django.contrib import admin
from .models import Cobertura, Paciente, Medico, DisponibilidadMedico, Turno

@admin.register(Cobertura)
class CoberturaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'dni', 'telefono', 'cobertura', 'categoria', 'fecha_registro']
    list_filter = ['cobertura', 'categoria', 'fecha_registro']
    search_fields = ['user__first_name', 'user__last_name', 'dni', 'user__email']
    date_hierarchy = 'fecha_registro'
    
    def nombre_completo(self, obj):
        return obj.nombre_completo
    nombre_completo.short_description = 'Nombre Completo'

class DisponibilidadInline(admin.TabularInline):
    model = DisponibilidadMedico
    extra = 1

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'especialidad', 'matricula', 'activo']
    list_filter = ['especialidad', 'activo', 'coberturas']
    search_fields = ['nombre', 'apellido', 'matricula']
    filter_horizontal = ['coberturas']
    inlines = [DisponibilidadInline]
    
    def nombre_completo(self, obj):
        return obj.nombre_completo
    nombre_completo.short_description = 'Nombre Completo'

@admin.register(DisponibilidadMedico)
class DisponibilidadMedicoAdmin(admin.ModelAdmin):
    list_display = ['medico', 'get_dia_semana_display', 'hora_inicio', 'hora_fin', 'duracion_turno']
    list_filter = ['dia_semana', 'medico']
    search_fields = ['medico__nombre', 'medico__apellido']

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ['get_paciente', 'medico', 'fecha', 'hora', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha', 'medico']
    search_fields = ['paciente__user__first_name', 'paciente__user__last_name', 'paciente_nombre', 'medico__nombre', 'medico__apellido']
    date_hierarchy = 'fecha'
    
    def get_paciente(self, obj):
        if obj.paciente:
            return obj.paciente.nombre_completo
        return obj.paciente_nombre
    get_paciente.short_description = 'Paciente'