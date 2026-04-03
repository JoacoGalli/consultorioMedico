from django.contrib import admin

from .models import (
    ArchivoTurno,
    CancelacionDia,
    CancelacionHorario,
    Cobertura,
    DisponibilidadMedico,
    Medico,
    Paciente,
    Sobreturno,
    Turno,
)


@admin.register(Cobertura)
class CoberturaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activa"]
    list_filter = ["activa"]
    search_fields = ["nombre"]


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = [
        "nombre_completo",
        "dni",
        "telefono",
        "cobertura",
        "categoria",
        "fecha_registro",
    ]
    list_filter = ["cobertura", "categoria", "fecha_registro"]
    search_fields = ["user__first_name", "user__last_name", "dni", "user__email"]
    date_hierarchy = "fecha_registro"

    @admin.display(description="Paciente")
    def nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class DisponibilidadInline(admin.TabularInline):
    model = DisponibilidadMedico
    extra = 1


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "especialidad", "matricula", "activo"]
    list_filter = ["especialidad", "activo", "coberturas"]
    search_fields = ["nombre", "apellido", "matricula"]
    filter_horizontal = ["coberturas"]
    inlines = [DisponibilidadInline]

    @admin.display(description="Médico")
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"


@admin.register(DisponibilidadMedico)
class DisponibilidadMedicoAdmin(admin.ModelAdmin):
    list_display = ["medico", "get_dia_semana_display", "hora_inicio", "hora_fin", "duracion_turno"]
    list_filter = ["dia_semana", "medico"]
    search_fields = ["medico__nombre", "medico__apellido"]


class ArchivoTurnoInline(admin.TabularInline):
    model = ArchivoTurno
    extra = 1


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ["get_paciente", "medico", "fecha", "hora", "confirmado", "fecha_creacion"]
    list_filter = ["fecha", "medico", "confirmado"]
    search_fields = [
        "paciente__user__first_name",
        "paciente__user__last_name",
        "paciente_nombre",
        "paciente_apellido",
        "medico__nombre",
        "medico__apellido",
    ]
    date_hierarchy = "fecha"
    inlines = [ArchivoTurnoInline]

    @admin.display(description="Paciente")
    def get_paciente(self, obj):
        if obj.paciente:
            return f"{obj.paciente.user.first_name} {obj.paciente.user.last_name}"
        return f"{obj.paciente_apellido}, {obj.paciente_nombre}"


@admin.register(ArchivoTurno)
class ArchivoTurnoAdmin(admin.ModelAdmin):
    list_display = ["turno", "archivo", "descripcion", "fecha_subida"]
    list_filter = ["fecha_subida"]
    search_fields = ["turno__paciente_nombre", "turno__paciente_apellido", "descripcion"]


@admin.register(Sobreturno)
class SobreturnoAdmin(admin.ModelAdmin):
    list_display = ["get_paciente", "medico", "fecha", "hora", "creado_por"]
    list_filter = ["fecha", "medico"]
    search_fields = ["paciente_nombre", "paciente_apellido", "medico__nombre", "medico__apellido"]

    @admin.display(description="Paciente")
    def get_paciente(self, obj):
        return f"{obj.paciente_apellido}, {obj.paciente_nombre}"


@admin.register(CancelacionDia)
class CancelacionDiaAdmin(admin.ModelAdmin):
    list_display = ["medico", "fecha", "motivo", "creado_por"]
    list_filter = ["medico", "fecha"]
    search_fields = ["medico__nombre", "medico__apellido", "motivo"]


@admin.register(CancelacionHorario)
class CancelacionHorarioAdmin(admin.ModelAdmin):
    list_display = ["medico", "fecha", "hora_inicio", "hora_fin", "motivo"]
    list_filter = ["medico", "fecha"]
    search_fields = ["medico__nombre", "medico__apellido", "motivo"]
