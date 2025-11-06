from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import time, datetime, timedelta

class Cobertura(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Cobertura"
        verbose_name_plural = "Coberturas"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Paciente(models.Model):
    CATEGORIAS = [
        ('A', 'Categoría A'),
        ('B', 'Categoría B'),
        ('C', 'Categoría C'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='paciente')
    dni = models.CharField(max_length=8, unique=True)
    telefono = models.CharField(max_length=20)
    domicilio = models.CharField(max_length=200)
    cobertura = models.ForeignKey(Cobertura, on_delete=models.SET_NULL, null=True, related_name='pacientes')
    numero_afiliado = models.CharField(max_length=50)
    categoria = models.CharField(max_length=1, choices=CATEGORIAS, default='A')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - DNI: {self.dni}"
    
    @property
    def nombre_completo(self):
        return self.user.get_full_name()

class Medico(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    coberturas = models.ManyToManyField(Cobertura, related_name='medicos', blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Médico"
        verbose_name_plural = "Médicos"
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"Dr. {self.apellido}, {self.nombre} - {self.especialidad}"
    
    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"

class DisponibilidadMedico(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='disponibilidades')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    duracion_turno = models.IntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        help_text="Duración en minutos (15-120)"
    )
    
    class Meta:
        verbose_name = "Disponibilidad"
        verbose_name_plural = "Disponibilidades"
        unique_together = ['medico', 'dia_semana', 'hora_inicio']
        ordering = ['dia_semana', 'hora_inicio']
    
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

class Turno(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ]
    
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='turnos', null=True, blank=True)
    paciente_nombre = models.CharField(max_length=200, blank=True, help_text="Para turnos sin registro")
    paciente_telefono = models.CharField(max_length=20, blank=True)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='turnos')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    motivo = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='turnos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        unique_together = ['medico', 'fecha', 'hora']
        ordering = ['-fecha', '-hora']
    
    def __str__(self):
        paciente = self.paciente.nombre_completo if self.paciente else self.paciente_nombre
        return f"{paciente} - {self.medico.nombre_completo} - {self.fecha} {self.hora}"
    
    @property
    def es_futuro(self):
        ahora = datetime.now()
        fecha_hora_turno = datetime.combine(self.fecha, self.hora)
        return fecha_hora_turno > ahora
    
    def puede_cancelar(self):
        """Permite cancelar turnos con al menos 24hs de anticipación"""
        ahora = datetime.now()
        fecha_hora_turno = datetime.combine(self.fecha, self.hora)
        return fecha_hora_turno - ahora > timedelta(hours=24)