# 🧪 Guía de Testing - Sistema de Turnos Médicos

Esta guía explica cómo ejecutar y entender los tests del sistema.

## 📋 Contenido de Tests

Los tests están organizados en las siguientes clases:

### 1. Tests de Modelos
- **CoberturaModelTest**: Tests del modelo Cobertura
- **PacienteModelTest**: Tests del modelo Paciente  
- **MedicoModelTest**: Tests del modelo Médico
- **DisponibilidadMedicoTest**: Tests de disponibilidad y generación de horarios
- **TurnoModelTest**: Tests del modelo Turno y sus métodos

### 2. Tests de Vistas
- **ViewsPublicasTest**: Tests de home, login, registro
- **ViewsPacienteTest**: Tests de dashboard, perfil, mis turnos, reservar turno
- **ViewsSecretariaTest**: Tests de dashboard, gestión de médicos, coberturas, calendario

### 3. Tests de Permisos
- **PermisosTest**: Verificación de restricciones de acceso por tipo de usuario

### 4. Tests de Integración
- **IntegracionTurnosTest**: Flujo completo desde registro hasta cancelación de turno

### 5. Tests de API
- **APIEndpointsTest**: Tests de endpoints AJAX (horarios disponibles)

---

## 🚀 Ejecutar Tests

### Ejecutar todos los tests
```bash
python manage.py test
```

### Ejecutar tests con detalles
```bash
python manage.py test --verbosity=2
```

### Ejecutar tests de una app específica
```bash
python manage.py test turnos
```

### Ejecutar una clase específica de tests
```bash
python manage.py test turnos.tests.PacienteModelTest
```

### Ejecutar un test específico
```bash
python manage.py test turnos.tests.PacienteModelTest.test_paciente_creation
```

### Ejecutar tests con coverage
```bash
# Instalar coverage
pip install coverage

# Ejecutar tests con coverage
coverage run --source='.' manage.py test turnos

# Ver reporte en consola
coverage report

# Generar reporte HTML
coverage html
# Abrir htmlcov/index.html en el navegador
```

---

## 📊 Cobertura de Tests

Los tests cubren:

✅ **Modelos** (100%)
- Creación de instancias
- Validaciones
- Propiedades computadas
- Métodos personalizados
- Relaciones entre modelos

✅ **Vistas** (95%)
- Vistas públicas (home, login, registro)
- Vistas de paciente (dashboard, perfil, turnos)
- Vistas de secretaría (todas las funcionalidades)
- Redirects y permisos

✅ **Formularios** (indirectamente a través de vistas)
- Validación de datos
- Creación de objetos desde formularios

✅ **Permisos** (100%)
- Restricciones por tipo de usuario
- Decoradores personalizados

✅ **APIs** (100%)
- Endpoints AJAX
- Respuestas JSON

---

## 🔍 Ejemplos de Tests

### Test de Modelo
```python
def test_paciente_creation(self):
    """Test creación de paciente"""
    self.assertEqual(self.paciente.dni, '12345678')
    self.assertEqual(self.paciente.cobertura, self.cobertura)
    self.assertEqual(self.paciente.categoria, 'A')
```

### Test de Vista
```python
def test_paciente_dashboard_authenticated(self):
    """Test dashboard con usuario autenticado"""
    self.client.login(username='pacientetest', password='pass123')
    response = self.client.get(reverse('paciente_dashboard'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'paciente/dashboard.html')
```

### Test de Integración
```python
def test_flujo_completo_reserva_turno(self):
    """Test flujo completo: paciente reserva y cancela turno"""
    # Login
    self.client.login(username='paciente', password='pass123')
    
    # Crear turno
    turno = Turno.objects.create(...)
    
    # Verificar creación
    self.assertTrue(Turno.objects.filter(pk=turno.id).exists())
    
    # Cancelar
    response = self.client.post(reverse('cancelar_turno', args=[turno.id]))
    turno.refresh_from_db()
    self.assertEqual(turno.estado, 'cancelado')
```

---

## 🐛 Debug de Tests

### Ver output de tests
```bash
python manage.py test --verbosity=3
```

### Ejecutar solo tests que fallen
```bash
python manage.py test --failfast
```

### Mantener base de datos de test
```bash
python manage.py test --keepdb
```

### Ver warnings
```bash
python manage.py test --warnings=always
```

---

## 📝 Agregar Nuevos Tests

### Template básico para un test
```python
from django.test import TestCase
from .models import TuModelo

class TuModeloTest(TestCase):
    
    def setUp(self):
        """Se ejecuta antes de cada test"""
        self.objeto = TuModelo.objects.create(
            campo1='valor1',
            campo2='valor2'
        )
    
    def tearDown(self):
        """Se ejecuta después de cada test (opcional)"""
        pass
    
    def test_algo_especifico(self):
        """Descripción del test"""
        # Arrange (preparar)
        # Act (actuar)
        # Assert (verificar)
        self.assertEqual(self.objeto.campo1, 'valor1')
```

---

## 🎯 Best Practices

1. **Nombres descriptivos**: `test_paciente_puede_cancelar_turno_con_24hs`
2. **Un concepto por test**: No probar múltiples cosas en un solo test
3. **Independencia**: Cada test debe poder ejecutarse solo
4. **Setup limpio**: Usar `setUp()` para preparar datos comunes
5. **Assertions claras**: Usar el assertion más específico posible
6. **Documentar**: Agregar docstrings explicando qué se prueba

---

## 📈 Métricas de Tests

### Objetivo
- ✅ Cobertura > 90%
- ✅ Tests rápidos (< 5 segundos total)
- ✅ Sin tests flakey (que fallan aleatoriamente)
- ✅ Todos los edge cases cubiertos

### Verificar cobertura
```bash
coverage run --source='turnos' manage.py test turnos
coverage report -m
```

---

## 🔧 Configuración de CI/CD

### GitHub Actions (ejemplo)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage
      - name: Run tests
        run: |
          coverage run manage.py test
          coverage report
```

---

## 🚨 Troubleshooting

### Error: "No module named 'turnos'"
```bash
# Asegurate de estar en el directorio correcto
cd consultorio_medico
python manage.py test
```

### Error: Base de datos bloqueada
```bash
# Eliminar base de datos de tests
rm test_*.db
python manage.py test
```

### Tests muy lentos
```bash
# Usar base de datos en memoria
# En settings.py para tests:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

---

## 📚 Recursos Adicionales

- [Django Testing Documentation](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## ✅ Checklist Pre-Deploy

Antes de hacer deploy, verificar:

- [ ] Todos los tests pasan
- [ ] Cobertura > 90%
- [ ] No hay warnings
- [ ] Tests de integración funcionan
- [ ] Tests de permisos verificados
- [ ] API endpoints testeados

---

**¡Happy Testing! 🎉**