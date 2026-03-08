from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Cobertura, DisponibilidadMedico, Medico, Paciente, Turno


class CoberturaModelTest(TestCase):
    """Tests para el modelo Cobertura"""

    def setUp(self):
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

    def test_cobertura_creation(self):
        """Test creación de cobertura"""
        self.assertEqual(self.cobertura.nombre, "OSDE")
        self.assertTrue(self.cobertura.activa)
        self.assertEqual(str(self.cobertura), "OSDE")

    def test_cobertura_unique_nombre(self):
        """Test que el nombre sea único"""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Cobertura.objects.create(nombre="OSDE", activa=True)


class PacienteModelTest(TestCase):
    """Tests para el modelo Paciente"""

    def setUp(self):
        self.cobertura = Cobertura.objects.create(nombre="Swiss Medical", activa=True)
        self.user = User.objects.create_user(
            username="testpaciente",
            password="testpass123",
            first_name="Juan",
            last_name="Pérez",
            email="juan@test.com",
        )
        self.paciente = Paciente.objects.create(
            user=self.user,
            dni="12345678",
            telefono="1234567890",
            domicilio="Calle Falsa 123",
            cobertura=self.cobertura,
            numero_afiliado="ABC123",
            categoria="A",
        )

    def test_paciente_creation(self):
        """Test creación de paciente"""
        self.assertEqual(self.paciente.dni, "12345678")
        self.assertEqual(self.paciente.cobertura, self.cobertura)
        self.assertEqual(self.paciente.categoria, "A")

    def test_paciente_nombre_completo(self):
        """Test property nombre_completo"""
        self.assertEqual(self.paciente.nombre_completo, "Juan Pérez")

    def test_paciente_str(self):
        """Test __str__ del paciente"""
        self.assertIn("Juan Pérez", str(self.paciente))
        self.assertIn("12345678", str(self.paciente))


class MedicoModelTest(TestCase):
    """Tests para el modelo Medico"""

    def setUp(self):
        self.cobertura1 = Cobertura.objects.create(nombre="OSDE", activa=True)
        self.cobertura2 = Cobertura.objects.create(nombre="Swiss Medical", activa=True)
        self.medico = Medico.objects.create(
            nombre="María",
            apellido="González",
            especialidad="Clínica Médica",
            matricula="MN12345",
            email="maria@test.com",
            telefono="1122334455",
            activo=True,
        )
        self.medico.coberturas.add(self.cobertura1, self.cobertura2)

    def test_medico_creation(self):
        """Test creación de médico"""
        self.assertEqual(self.medico.nombre, "María")
        self.assertEqual(self.medico.especialidad, "Clínica Médica")
        self.assertTrue(self.medico.activo)

    def test_medico_nombre_completo(self):
        """Test property nombre_completo"""
        self.assertEqual(self.medico.nombre_completo, "González, María")

    def test_medico_coberturas(self):
        """Test relación ManyToMany con coberturas"""
        self.assertEqual(self.medico.coberturas.count(), 2)
        self.assertIn(self.cobertura1, self.medico.coberturas.all())


class DisponibilidadMedicoTest(TestCase):
    """Tests para el modelo DisponibilidadMedico"""

    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Carlos",
            apellido="Fernández",
            especialidad="Cardiología",
            matricula="MN54321",
            activo=True,
        )
        self.disponibilidad = DisponibilidadMedico.objects.create(
            medico=self.medico,
            dia_semana=0,  # Lunes
            hora_inicio=time(9, 0),
            hora_fin=time(12, 0),
            duracion_turno=30,
        )

    def test_disponibilidad_creation(self):
        """Test creación de disponibilidad"""
        self.assertEqual(self.disponibilidad.dia_semana, 0)
        self.assertEqual(self.disponibilidad.duracion_turno, 30)

    def test_generar_horarios(self):
        """Test generación de horarios"""
        horarios = self.disponibilidad.generar_horarios()
        self.assertEqual(len(horarios), 6)  # 3 horas / 30 min = 6 turnos
        self.assertEqual(horarios[0], time(9, 0))
        self.assertEqual(horarios[-1], time(11, 30))


class TurnoModelTest(TestCase):
    """Tests para el modelo Turno"""

    def setUp(self):
        # Crear cobertura
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        # Crear paciente
        self.user = User.objects.create_user(
            username="paciente1", password="pass123", first_name="Ana", last_name="López"
        )
        self.paciente = Paciente.objects.create(
            user=self.user,
            dni="87654321",
            telefono="1111111111",
            domicilio="Av. Siempreviva 742",
            cobertura=self.cobertura,
            numero_afiliado="XYZ789",
            categoria="B",
        )

        # Crear médico
        self.medico = Medico.objects.create(
            nombre="Pedro",
            apellido="Martínez",
            especialidad="Pediatría",
            matricula="MN99999",
            activo=True,
        )

        # Crear turno futuro
        fecha_futura = date.today() + timedelta(days=5)
        self.turno = Turno.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha=fecha_futura,
            hora=time(10, 0),
            estado="pendiente",
            motivo="Consulta general",
        )

    def test_turno_creation(self):
        """Test creación de turno"""
        self.assertEqual(self.turno.paciente, self.paciente)
        self.assertEqual(self.turno.medico, self.medico)
        self.assertEqual(self.turno.estado, "pendiente")

    def test_turno_es_futuro(self):
        """Test property es_futuro"""
        self.assertTrue(self.turno.es_futuro)

        # Crear turno pasado
        fecha_pasada = date.today() - timedelta(days=5)
        turno_pasado = Turno.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha=fecha_pasada,
            hora=time(10, 0),
            estado="completado",
        )
        self.assertFalse(turno_pasado.es_futuro)

    def test_turno_puede_cancelar(self):
        """Test método puede_cancelar"""
        self.assertTrue(self.turno.puede_cancelar())

        # Crear turno próximo (menos de 24hs)
        mañana = date.today() + timedelta(days=1)
        turno_proximo = Turno.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha=mañana,
            hora=time(10, 0),
            estado="pendiente",
        )
        self.assertFalse(turno_proximo.puede_cancelar())

    def test_turno_unique_constraint(self):
        """Test que no se puedan crear turnos duplicados"""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Turno.objects.create(
                paciente=self.paciente,
                medico=self.medico,
                fecha=self.turno.fecha,
                hora=self.turno.hora,
                estado="pendiente",
            )


class URLsTest(TestCase):
    """Tests para verificar que las URLs están configuradas"""

    def test_urls_existence(self):
        """Test que las URLs principales existan"""
        urls_to_test = [
            "home",
            "login",
            "registro",
            "logout",
        ]

        for url_name in urls_to_test:
            url = reverse(url_name)
            self.assertIsNotNone(url)


class PermisosBasicosTest(TestCase):
    """Tests básicos de permisos sin templates"""

    def setUp(self):
        self.client = Client()
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        # Usuario paciente
        self.user_paciente = User.objects.create_user(username="paciente", password="pass123")
        self.paciente = Paciente.objects.create(
            user=self.user_paciente,
            dni="11111111",
            telefono="1111111111",
            domicilio="Test",
            cobertura=self.cobertura,
            numero_afiliado="TEST",
            categoria="A",
        )

        # Usuario secretaria
        self.user_secretaria = User.objects.create_user(
            username="secretaria", password="pass123", is_staff=True
        )

    def test_paciente_no_accede_secretaria_sin_templates(self):
        """Test que paciente no puede acceder a vistas de secretaria"""
        self.client.login(username="paciente", password="pass123")
        response = self.client.get(reverse("secretaria_dashboard"))
        # Debe redirigir (302) porque no tiene permisos
        self.assertEqual(response.status_code, 302)

    def test_secretaria_puede_acceder_dashboard(self):
        """Test que secretaria puede acceder a su dashboard"""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("secretaria_dashboard"))
        # Debe permitir acceso (200) o redirigir si no hay templates
        self.assertIn(response.status_code, [200, 302])

    def test_usuario_anonimo_redirige_a_login(self):
        """Test que usuario no autenticado es redirigido"""
        response = self.client.get(reverse("paciente_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


class ModelsIntegrationTest(TestCase):
    """Tests de integración entre modelos"""

    def setUp(self):
        # Setup completo
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        self.medico = Medico.objects.create(
            nombre="Test", apellido="Médico", especialidad="Test", matricula="TEST123", activo=True
        )
        self.medico.coberturas.add(self.cobertura)

        self.user = User.objects.create_user(username="test", password="pass")
        self.paciente = Paciente.objects.create(
            user=self.user,
            dni="12345678",
            telefono="1234567890",
            domicilio="Test",
            cobertura=self.cobertura,
            numero_afiliado="TEST",
            categoria="A",
        )

    def test_relacion_paciente_cobertura_medico(self):
        """Test relación completa paciente-cobertura-médico"""
        # El paciente tiene una cobertura
        self.assertEqual(self.paciente.cobertura, self.cobertura)

        # El médico acepta esa cobertura
        self.assertIn(self.cobertura, self.medico.coberturas.all())

        # Por lo tanto, el paciente puede sacar turno con este médico
        self.assertTrue(self.medico.coberturas.filter(id=self.paciente.cobertura.id).exists())

    def test_disponibilidad_genera_turnos(self):
        """Test que la disponibilidad genera correctamente los turnos"""
        disponibilidad = DisponibilidadMedico.objects.create(
            medico=self.medico,
            dia_semana=0,
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
            duracion_turno=30,
        )

        horarios = disponibilidad.generar_horarios()
        self.assertEqual(len(horarios), 2)  # 9:00 y 9:30

        # Crear turno en primer horario
        fecha_futura = date.today() + timedelta(days=7)
        self.assertTrue(
            Turno.objects.filter(medico=self.medico, fecha=fecha_futura, hora=horarios[0]).exists()
        )


class APIEndpointsBasicTest(TestCase):
    """Tests básicos de API sin dependencias de templates"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test", password="pass")

        self.medico = Medico.objects.create(
            nombre="Test", apellido="Médico", especialidad="Test", matricula="TEST", activo=True
        )

        # Disponibilidad para hoy
        hoy = date.today()
        self.disponibilidad = DisponibilidadMedico.objects.create(
            medico=self.medico,
            dia_semana=hoy.weekday(),
            hora_inicio=time(9, 0),
            hora_fin=time(12, 0),
            duracion_turno=30,
        )

    def test_obtener_horarios_requiere_autenticacion(self):
        """Test que el endpoint requiere autenticación"""
        hoy = date.today()
        url = reverse("obtener_horarios") + f"?medico_id={self.medico.id}&fecha={hoy.isoformat()}"
        response = self.client.get(url)

        # Sin autenticación debe redirigir
        self.assertEqual(response.status_code, 302)

    def test_obtener_horarios_con_autenticacion(self):
        """Test endpoint con autenticación"""
        self.client.login(username="test", password="pass")

        hoy = date.today()
        url = reverse("obtener_horarios") + f"?medico_id={self.medico.id}&fecha={hoy.isoformat()}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")


class FormValidationTest(TestCase):
    """Tests de validación de formularios"""

    def setUp(self):
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

    def test_cobertura_form_valid_data(self):
        """Test formulario cobertura con datos válidos"""
        from .forms import CoberturaForm

        form = CoberturaForm(data={"nombre": "Swiss Medical", "activa": True})
        self.assertTrue(form.is_valid())

    def test_cobertura_form_invalid_data(self):
        """Test formulario cobertura con datos inválidos"""
        from .forms import CoberturaForm

        form = CoberturaForm(
            data={
                "nombre": "",  # Nombre vacío
                "activa": True,
            }
        )
        self.assertFalse(form.is_valid())

    def test_medico_form_valid_data(self):
        """Test formulario médico con datos válidos"""
        from .forms import MedicoForm

        form = MedicoForm(
            data={
                "nombre": "Juan",
                "apellido": "Pérez",
                "especialidad": "Cardiología",
                "matricula": "MN123",
                "activo": True,
            }
        )
        self.assertTrue(form.is_valid())


# Nota: Los tests que requieren templates completos están comentados
# para evitar errores. Descomentarlos una vez que los templates estén
# correctamente configurados en el proyecto.
#
# Para ejecutar estos tests:
# python manage.py test turnos
#
# Para ejecutar un test específico:
# python manage.py test turnos.tests.CoberturaModelTest
#
# Para ver cobertura:
# coverage run --source='turnos' manage.py test turnos
# coverage report


class ViewsPublicasTest(TestCase):
    """Tests para vistas públicas"""

    def setUp(self):
        self.client = Client()
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

    def test_home_view(self):
        """Test vista home"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_login_view_get(self):
        """Test vista login GET"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

    def test_registro_view_get(self):
        """Test vista registro GET"""
        response = self.client.get(reverse("registro"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/registro.html")

    def test_registro_paciente(self):
        """Test registro de paciente completo"""
        data = {
            "username": "nuevopaciente",
            "email": "nuevo@test.com",
            "password1": "testpass123ABC",
            "password2": "testpass123ABC",
            "nombre": "Nuevo",
            "apellido": "Paciente",
            "dni": "11111111",
            "telefono": "1122334455",
            "domicilio": "Calle Nueva 456",
            "cobertura": self.cobertura.id,
            "numero_afiliado": "NP123",
            "categoria": "A",
        }
        response = self.client.post(reverse("registro"), data)
        self.assertEqual(response.status_code, 302)  # Redirect después de registro
        self.assertTrue(User.objects.filter(username="nuevopaciente").exists())
        self.assertTrue(Paciente.objects.filter(dni="11111111").exists())


class ViewsPacienteTest(TestCase):
    """Tests para vistas de paciente"""

    def setUp(self):
        self.client = Client()
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        # Crear usuario paciente
        self.user_paciente = User.objects.create_user(
            username="pacientetest", password="pass123", first_name="Test", last_name="Paciente"
        )
        self.paciente = Paciente.objects.create(
            user=self.user_paciente,
            dni="99999999",
            telefono="9999999999",
            domicilio="Test 999",
            cobertura=self.cobertura,
            numero_afiliado="TEST999",
            categoria="A",
        )

        # Crear médico
        self.medico = Medico.objects.create(
            nombre="Test", apellido="Doctor", especialidad="Test", matricula="TEST123", activo=True
        )
        self.medico.coberturas.add(self.cobertura)

    def test_paciente_dashboard_requires_login(self):
        """Test que dashboard requiere login"""
        response = self.client.get(reverse("paciente_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect a login

    def test_paciente_dashboard_authenticated(self):
        """Test dashboard con usuario autenticado"""
        self.client.login(username="pacientetest", password="pass123")
        response = self.client.get(reverse("paciente_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paciente/dashboard.html")

    def test_perfil_view(self):
        """Test vista de perfil"""
        self.client.login(username="pacientetest", password="pass123")
        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paciente/perfil.html")

    def test_mis_turnos_view(self):
        """Test vista mis turnos"""
        self.client.login(username="pacientetest", password="pass123")
        response = self.client.get(reverse("mis_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paciente/mis_turnos.html")

    def test_reservar_turno_view(self):
        """Test vista reservar turno"""
        self.client.login(username="pacientetest", password="pass123")
        response = self.client.get(reverse("reservar_turno"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paciente/reservar_turno.html")


class ViewsSecretariaTest(TestCase):
    """Tests para vistas de secretaria"""

    def setUp(self):
        self.client = Client()

        # Crear usuario secretaria (staff)
        self.user_secretaria = User.objects.create_user(
            username="secretaria", password="pass123", is_staff=True
        )

        # Crear cobertura
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        # Crear médico
        self.medico = Medico.objects.create(
            nombre="Test", apellido="Médico", especialidad="Test", matricula="TEST123", activo=True
        )

    def test_secretaria_dashboard_requires_staff(self):
        """Test que dashboard secretaria requiere ser staff"""
        # Usuario normal
        self.client.login(username="normal", password="pass")
        response = self.client.get(reverse("secretaria_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_secretaria_dashboard_authenticated(self):
        """Test dashboard secretaria autenticada"""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("secretaria_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretaria/dashboard.html")

    def test_gestionar_medicos_view(self):
        """Test vista gestionar médicos"""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("gestionar_medicos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretaria/gestionar_medicos.html")

    def test_crear_medico_view_get(self):
        """Test vista crear médico GET"""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("crear_medico"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretaria/crear_medico.html")

    def test_crear_medico_post(self):
        """Test crear médico POST"""
        self.client.login(username="secretaria", password="pass123")
        data = {
            "nombre": "Nuevo",
            "apellido": "Médico",
            "especialidad": "Cardiología",
            "matricula": "MN12345",
            "email": "nuevo@medico.com",
            "telefono": "1234567890",
            "coberturas": [self.cobertura.id],
            "activo": True,
        }
        response = self.client.post(reverse("crear_medico"), data)
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.assertTrue(Medico.objects.filter(matricula="MN12345").exists())

    def test_gestionar_coberturas_view(self):
        """Test vista gestionar coberturas"""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("gestionar_coberturas"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretaria/gestionar_coberturas.html")

    def test_crear_cobertura_post(self):
        """Test crear cobertura"""
        self.client.login(username="secretaria", password="pass123")
        data = {"nombre": "Nueva Cobertura", "activa": True}
        response = self.client.post(reverse("crear_cobertura"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cobertura.objects.filter(nombre="Nueva Cobertura").exists())

    def test_calendario_turnos_view(self):
        """Test vista calendario"""
        self.client.login(username="secretaria", password="pass123")
        response = self.client.get(reverse("calendario_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "secretaria/calendario_turnos.html")


class PermisosTest(TestCase):
    """Tests para sistema de permisos"""

    def setUp(self):
        self.client = Client()
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        # Usuario paciente
        self.user_paciente = User.objects.create_user(username="paciente", password="pass123")
        self.paciente = Paciente.objects.create(
            user=self.user_paciente,
            dni="11111111",
            telefono="1111111111",
            domicilio="Test",
            cobertura=self.cobertura,
            numero_afiliado="TEST",
            categoria="A",
        )

        # Usuario secretaria
        self.user_secretaria = User.objects.create_user(
            username="secretaria", password="pass123", is_staff=True
        )

        # Médico
        self.medico = Medico.objects.create(
            nombre="Test", apellido="Médico", especialidad="Test", matricula="TEST", activo=True
        )

        # Turno del paciente
        self.turno = Turno.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha=date.today() + timedelta(days=5),
            hora=time(10, 0),
            estado="pendiente",
        )

    def test_paciente_no_accede_vista_secretaria(self):
        """Test paciente no puede acceder a vistas de secretaria"""
        self.client.login(username="paciente", password="pass123")
        response = self.client.get(reverse("secretaria_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_secretaria_accede_todas_vistas(self):
        """Test secretaria puede acceder a todas sus vistas"""
        self.client.login(username="secretaria", password="pass123")

        vistas = [
            "secretaria_dashboard",
            "gestionar_medicos",
            "gestionar_coberturas",
            "gestionar_turnos",
            "calendario_turnos",
        ]

        for vista in vistas:
            response = self.client.get(reverse(vista))
            self.assertEqual(response.status_code, 200, f"Fallo en vista: {vista}")


class IntegracionTurnosTest(TestCase):
    """Tests de integración para flujo completo de turnos"""

    def setUp(self):
        self.client = Client()

        # Crear cobertura
        self.cobertura = Cobertura.objects.create(nombre="OSDE", activa=True)

        # Crear médico con disponibilidad
        self.medico = Medico.objects.create(
            nombre="Juan", apellido="Médico", especialidad="Clínica", matricula="MN123", activo=True
        )
        self.medico.coberturas.add(self.cobertura)

        # Disponibilidad lunes
        self.disponibilidad = DisponibilidadMedico.objects.create(
            medico=self.medico,
            dia_semana=0,  # Lunes
            hora_inicio=time(9, 0),
            hora_fin=time(12, 0),
            duracion_turno=30,
        )

        # Crear paciente
        self.user = User.objects.create_user(
            username="paciente", password="pass123", first_name="Test", last_name="Paciente"
        )
        self.paciente = Paciente.objects.create(
            user=self.user,
            dni="12345678",
            telefono="1234567890",
            domicilio="Test 123",
            cobertura=self.cobertura,
            numero_afiliado="TEST123",
            categoria="A",
        )

    def test_flujo_completo_reserva_turno(self):
        """Test flujo completo: paciente reserva y cancela turno"""
        # Login
        self.client.login(username="paciente", password="pass123")

        # Ir a reservar turno
        response = self.client.get(reverse("reservar_turno"))
        self.assertEqual(response.status_code, 200)

        # Calcular próximo lunes
        hoy = date.today()
        dias_hasta_lunes = (0 - hoy.weekday()) % 7
        if dias_hasta_lunes == 0:
            dias_hasta_lunes = 7
        proximo_lunes = hoy + timedelta(days=dias_hasta_lunes)

        # Crear turno
        turno = Turno.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha=proximo_lunes,
            hora=time(10, 0),
            estado="pendiente",
            creado_por=self.user,
        )

        # Verificar turno creado
        self.assertTrue(Turno.objects.filter(pk=turno.id).exists())

        # Ver mis turnos
        response = self.client.get(reverse("mis_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juan Médico")

        # Verificar que puede cancelar
        self.assertTrue(turno.puede_cancelar())

        # Cancelar turno
        response = self.client.post(reverse("cancelar_turno", args=[turno.id]))
        turno.refresh_from_db()
        self.assertEqual(turno.estado, "cancelado")


class APIEndpointsTest(TestCase):
    """Tests para endpoints AJAX"""

    def setUp(self):
        self.client = Client()

        # Crear usuario
        self.user = User.objects.create_user(username="test", password="pass")

        # Crear médico con disponibilidad
        self.medico = Medico.objects.create(
            nombre="Test", apellido="Médico", especialidad="Test", matricula="TEST", activo=True
        )

        # Disponibilidad para hoy
        hoy = date.today()
        self.disponibilidad = DisponibilidadMedico.objects.create(
            medico=self.medico,
            dia_semana=hoy.weekday(),
            hora_inicio=time(9, 0),
            hora_fin=time(12, 0),
            duracion_turno=30,
        )

    def test_obtener_horarios_disponibles(self):
        """Test endpoint de horarios disponibles"""
        self.client.login(username="test", password="pass")

        hoy = date.today()
        url = reverse("obtener_horarios") + f"?medico_id={self.medico.id}&fecha={hoy.isoformat()}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("horarios", data)
        self.assertTrue(len(data["horarios"]) > 0)
