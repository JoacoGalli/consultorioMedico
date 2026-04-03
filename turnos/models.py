from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Cobertura(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cobertura"
        verbose_name_plural = "Coberturas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Paciente(models.Model):
    CATEGORIAS = [
        ("A", "Categoría A"),
        ("B", "Categoría B"),
        ("C", "Categoría C"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="paciente")
    dni = models.CharField(max_length=8, unique=True)
    telefono = models.CharField(max_length=20)
    domicilio = models.CharField(max_length=200)
    cobertura = models.ForeignKey(
        Cobertura, on_delete=models.SET_NULL, null=True, related_name="pacientes"
    )
    numero_afiliado = models.CharField(max_length=50)
    categoria = models.CharField(max_length=1, choices=CATEGORIAS, default="A")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    debe_cambiar_password = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.user.get_full_name()} - DNI: {self.dni}"

    @property
    def nombre_completo(self):
        return self.user.get_full_name()


class Medico(models.Model):
    DIAS_SEMANA = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    coberturas = models.ManyToManyField(Cobertura, related_name="medicos", blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Médico"
        verbose_name_plural = "Médicos"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"Dr. {self.apellido}, {self.nombre} - {self.especialidad}"

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"


class DisponibilidadMedico(models.Model):
    DIAS_SEMANA = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name="disponibilidades")
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    duracion_turno = models.IntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        help_text="Duración en minutos (15-120)",
    )

    class Meta:
        verbose_name = "Disponibilidad"
        verbose_name_plural = "Disponibilidades"
        unique_together = ["medico", "dia_semana", "hora_inicio"]
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self):
        return f"{self.medico.nombre_completo} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"

    def generar_horarios(self):
        """Genera lista de horarios disponibles para esta disponibilidad"""
        horarios = []
        hora_actual = datetime.combine(datetime.today(), self.hora_inicio)
        hora_fin = datetime.combine(datetime.today(), self.hora_fin)

        while hora_actual < hora_fin:
            horarios.append(hora_actual.time())
            hora_actual += timedelta(minutes=self.duracion_turno)

        return horarios


class ArchivoTurno(models.Model):
    turno = models.ForeignKey("Turno", on_delete=models.CASCADE, related_name="archivos")
    archivo = models.FileField(upload_to="turnos_archivos/%Y/%m/")
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.turno} - {self.archivo.name}"


class CancelacionDia(models.Model):
    """Cancelación de un día completo por razones como feriados o licencias"""

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name="cancelaciones_dia")
    fecha = models.DateField()
    motivo = models.CharField(max_length=200, default="Feriado/Licencia")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cancelación de Día"
        verbose_name_plural = "Cancelaciones de Días"
        unique_together = ["medico", "fecha"]

    def __str__(self):
        return f"{self.medico.nombre_completo} - {self.fecha} ({self.motivo})"


class CancelacionHorario(models.Model):
    """Cancelación de un rango horario específico en un día"""

    medico = models.ForeignKey(
        Medico, on_delete=models.CASCADE, related_name="cancelaciones_horario"
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    motivo = models.CharField(max_length=200, default="Licencia parcial")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cancelación de Horario"
        verbose_name_plural = "Cancelaciones de Horarios"
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"{self.medico.nombre_completo} - {self.fecha} {self.hora_inicio}-{self.hora_fin}"


class Sobreturno(models.Model):
    """Turnos fuera del horario normal del médico (solo para secretaria)"""

    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="sobreturnos", null=True, blank=True
    )
    paciente_nombre = models.CharField(max_length=200)
    paciente_apellido = models.CharField(max_length=200)
    paciente_telefono = models.CharField(max_length=20)
    paciente_email = models.EmailField(blank=True)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name="sobreturnos")
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField(blank=True)
    notas_secretaria = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sobreturno"
        verbose_name_plural = "Sobreturnos"
        unique_together = ["medico", "fecha", "hora"]
        ordering = ["-fecha", "-hora"]

    def __str__(self):
        return f"Sobreturno: {self.paciente_apellido}, {self.paciente_nombre} - {self.fecha} {self.hora}"

    @property
    def es_futuro(self):
        ahora = datetime.now()
        fecha_hora = datetime.combine(self.fecha, self.hora)
        return fecha_hora > ahora


class Turno(models.Model):
    paciente = models.ForeignKey(
        Paciente, on_delete=models.CASCADE, related_name="turnos", null=True, blank=True
    )
    paciente_nombre = models.CharField(
        max_length=200, blank=True, help_text="Para turnos sin registro"
    )
    paciente_apellido = models.CharField(max_length=200, blank=True)
    paciente_telefono = models.CharField(max_length=20, blank=True)
    paciente_email = models.EmailField(blank=True, help_text="Email para notificaciones")
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name="turnos")
    fecha = models.DateField()
    hora = models.TimeField()
    confirmado = models.BooleanField(default=False)
    motivo = models.TextField(blank=True)
    notas_secretaria = models.TextField(blank=True, help_text="Notas internas de la secretaria")
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="turnos_creados"
    )
    fecha_creacion = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    fecha_modificacion = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        unique_together = ["medico", "fecha", "hora"]
        ordering = ["-fecha", "-hora"]

    def __str__(self):
        paciente = (
            self.paciente.nombre_completo
            if self.paciente
            else f"{self.paciente_apellido}, {self.paciente_nombre}"
        )
        return f"{paciente} - {self.medico.nombre_completo} - {self.fecha} {self.hora}"

    @property
    def estado(self):
        """Determina el estado automáticamente según la fecha/hora del turno"""
        ahora = datetime.now()
        fecha_hora_turno = datetime.combine(self.fecha, self.hora)

        if fecha_hora_turno < ahora - timedelta(hours=2):
            return "completado"
        elif fecha_hora_turno > ahora:
            return "pendiente"
        else:
            return "en_curso"

    @property
    def es_futuro(self):
        ahora = datetime.now()
        fecha_hora_turno = datetime.combine(self.fecha, self.hora)
        return fecha_hora_turno > ahora

    def puede_cancelar(self):
        ahora = datetime.now()
        fecha_hora_turno = datetime.combine(self.fecha, self.hora)
        return fecha_hora_turno - ahora > timedelta(hours=24)
