from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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


class RegistroPacienteForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "tu@email.com",
            }
        ),
    )
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Juan",
            }
        ),
    )
    apellido = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Pérez",
            }
        ),
    )
    dni = forms.CharField(
        max_length=8,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "12345678",
            }
        ),
    )
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "11-1234-5678",
            }
        ),
    )
    domicilio = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Calle Falsa 123",
            }
        ),
    )
    cobertura = forms.ModelChoiceField(
        queryset=Cobertura.objects.filter(activa=True),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        ),
    )
    numero_afiliado = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "123456789",
            }
        ),
    )
    categoria = forms.ChoiceField(
        choices=Paciente.CATEGORIAS,
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "nombre_usuario",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["nombre"]
        user.last_name = self.cleaned_data["apellido"]

        if commit:
            user.save()
            Paciente.objects.create(
                user=user,
                dni=self.cleaned_data["dni"],
                telefono=self.cleaned_data["telefono"],
                domicilio=self.cleaned_data["domicilio"],
                cobertura=self.cleaned_data["cobertura"],
                numero_afiliado=self.cleaned_data["numero_afiliado"],
                categoria=self.cleaned_data["categoria"],
            )
        return user


class EditarPerfilForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        ),
    )
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        ),
    )
    apellido = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            }
        ),
    )

    class Meta:
        model = Paciente
        fields = ["telefono", "domicilio", "cobertura", "numero_afiliado", "categoria"]
        widgets = {
            "telefono": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "domicilio": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "cobertura": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "numero_afiliado": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["email"].initial = self.instance.user.email
            self.fields["nombre"].initial = self.instance.user.first_name
            self.fields["apellido"].initial = self.instance.user.last_name


class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = [
            "nombre",
            "apellido",
            "especialidad",
            "matricula",
            "email",
            "telefono",
            "coberturas",
            "activo",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "apellido": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "especialidad": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "matricula": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "coberturas": forms.CheckboxSelectMultiple(),
            "activo": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-blue-600"}),
        }


class DisponibilidadForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadMedico
        fields = ["dia_semana", "hora_inicio", "hora_fin", "duracion_turno"]
        widgets = {
            "dia_semana": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "hora_inicio": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                }
            ),
            "hora_fin": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                }
            ),
            "duracion_turno": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "min": 15,
                    "max": 120,
                    "step": 15,
                }
            ),
        }


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ["medico", "fecha", "hora", "motivo"]
        widgets = {
            "medico": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "min": date.today().isoformat(),
                }
            ),
            "hora": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                }
            ),
            "motivo": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        paciente = kwargs.pop("paciente", None)
        super().__init__(*args, **kwargs)

        # Filtrar médicos que acepten la cobertura del paciente
        if paciente and paciente.cobertura:
            self.fields["medico"].queryset = Medico.objects.filter(
                coberturas=paciente.cobertura, activo=True
            )
        else:
            self.fields["medico"].queryset = Medico.objects.filter(activo=True)


class TurnoSecretariaForm(forms.ModelForm):
    paciente_dni = forms.CharField(
        max_length=8,
        required=False,
        label="DNI del Paciente",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Ingresá el DNI y presioná Buscar",
            }
        ),
    )
    paciente_nombre = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Nombre del paciente",
            }
        ),
    )
    paciente_apellido = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Apellido del paciente",
            }
        ),
    )
    paciente_telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Teléfono",
            }
        ),
    )
    paciente_cobertura = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Obra Social",
            }
        ),
    )
    paciente_email = forms.EmailField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "placeholder": "Email (obligatorio para registro)",
            }
        ),
    )
    hora_turno = forms.ChoiceField(
        required=False,
        label="Hora del Turno",
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
            }
        ),
    )

    class Meta:
        model = Turno
        fields = [
            "paciente",
            "paciente_nombre",
            "paciente_apellido",
            "paciente_telefono",
            "medico",
            "fecha",
            "motivo",
            "notas_secretaria",
            "paciente_email",
        ]
        widgets = {
            "paciente": forms.HiddenInput(),
            "paciente_nombre": forms.TextInput(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg"}
            ),
            "paciente_apellido": forms.TextInput(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg"}
            ),
            "paciente_telefono": forms.TextInput(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg"}
            ),
            "medico": forms.Select(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg"}
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg",
                }
            ),
            "motivo": forms.Textarea(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg", "rows": 2}
            ),
            "notas_secretaria": forms.Textarea(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg", "rows": 2}
            ),
            "paciente_email": forms.TextInput(
                attrs={"class": "w-full px-4 py-2 border border-gray-300 rounded-lg"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hora_turno"].choices = [("", "Seleccioná un médico y fecha")]

    def clean(self):
        cleaned_data = super().clean()
        hora_str = self.cleaned_data.get("hora_turno") or self.data.get("hora_turno")
        if hora_str:
            from datetime import datetime

            cleaned_data["hora"] = datetime.strptime(hora_str, "%H:%M").time()
        return cleaned_data


class CoberturaForm(forms.ModelForm):
    class Meta:
        model = Cobertura
        fields = ["nombre", "activa"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Ej: OSDE, Swiss Medical, IOMA",
                }
            ),
            "activa": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-blue-600"}),
        }


class ArchivoTurnoForm(forms.ModelForm):
    class Meta:
        model = ArchivoTurno
        fields = ["archivo", "descripcion"]
        widgets = {
            "archivo": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                }
            ),
            "descripcion": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Descripción del archivo",
                }
            ),
        }


class TurnoEditarForm(forms.ModelForm):
    paciente_nombre = forms.CharField(max_length=200, required=False)
    paciente_apellido = forms.CharField(max_length=200, required=False)
    paciente_telefono = forms.CharField(max_length=20, required=False)
    paciente_email = forms.EmailField(required=False)

    class Meta:
        model = Turno
        fields = [
            "medico",
            "fecha",
            "hora",
            "paciente_nombre",
            "paciente_apellido",
            "paciente_telefono",
            "paciente_email",
            "confirmado",
            "motivo",
            "notas_secretaria",
        ]
        widgets = {
            "medico": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "hora": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "paciente_telefono": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "paciente_email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "confirmado": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-blue-600"}),
            "motivo": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "rows": 2,
                }
            ),
            "notas_secretaria": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.paciente:
            self.fields["paciente_nombre"].initial = self.instance.paciente.user.first_name
            self.fields["paciente_apellido"].initial = self.instance.paciente.user.last_name
            self.fields["paciente_telefono"].initial = self.instance.paciente.telefono
            self.fields["paciente_email"].initial = self.instance.paciente.user.email

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class SobreturnoForm(forms.ModelForm):
    class Meta:
        model = Sobreturno
        fields = [
            "paciente",
            "paciente_nombre",
            "paciente_apellido",
            "paciente_telefono",
            "paciente_email",
            "medico",
            "fecha",
            "hora",
            "motivo",
            "notas_secretaria",
        ]
        widgets = {
            "paciente": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "paciente_nombre": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Nombre del paciente",
                }
            ),
            "paciente_apellido": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Apellido del paciente",
                }
            ),
            "paciente_telefono": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Teléfono",
                }
            ),
            "paciente_email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Email (para notificaciones)",
                }
            ),
            "medico": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "hora": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "motivo": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "rows": 2,
                }
            ),
            "notas_secretaria": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "rows": 2,
                }
            ),
        }


class CancelacionDiaForm(forms.ModelForm):
    class Meta:
        model = CancelacionDia
        fields = ["medico", "fecha", "motivo"]
        widgets = {
            "medico": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "motivo": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Ej: Feriado, Licencia médica, Vacaciones",
                }
            ),
        }


class CancelacionHorarioForm(forms.ModelForm):
    class Meta:
        model = CancelacionHorario
        fields = ["medico", "fecha", "hora_inicio", "hora_fin", "motivo"]
        widgets = {
            "medico": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                }
            ),
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "hora_inicio": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "hora_fin": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                }
            ),
            "motivo": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Ej: El médico entra más tarde este día",
                }
            ),
        }
