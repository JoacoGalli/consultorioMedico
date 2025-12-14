# Sistema de Turnos para Consultorio Médico 🏥

Sistema web desarrollado con Django para la gestión de turnos médicos con múltiples doctores.

## 🎯 Características

- **Registro y autenticación de pacientes**
- **Gestión completa de turnos médicos**
- **Panel administrativo para secretaría**
- **Gestión de coberturas médicas personalizables**
- **Calendario visual de turnos disponibles/ocupados**
- **Múltiples médicos con diferentes especialidades**
- **Sistema de coberturas médicas**
- **Horarios dinámicos por médico**
- **Interfaz moderna con TailwindCSS**
- **Suite completa de tests automatizados**

---

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Virtualenv (recomendado)

---

## 🚀 Instalación

### 1. Clonar o crear el proyecto

```bash
mkdir consultorio_medico
cd consultorio_medico
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# En Linux/Mac
source venv/bin/activate

# En Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui-cambiar-en-produccion
DEBUG=True
```

### 5. Aplicar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Cargar datos iniciales

```bash
python manage.py loaddata turnos/fixtures/initial_data.json
```

### 7. Crear usuario administrador (secretaria)

```bash
python manage.py createsuperuser
```

Seguir las instrucciones en pantalla. Este será el usuario de la secretaria.

### 8. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

El sistema estará disponible en: **http://127.0.0.1:8000/**

---

## 👥 Tipos de Usuarios

### Paciente
- **Registro**: Desde la web en `/registro/`
- **Funcionalidades**:
  - Gestionar perfil personal
  - Reservar turnos según cobertura
  - Ver mis turnos
  - Cancelar turnos (con 24hs de anticipación)

### Secretaria (Staff)
- **Acceso**: Crear usuario con `createsuperuser`
- **Funcionalidades**:
  - Crear y gestionar médicos
  - Asignar horarios de atención
  - Gestionar coberturas por médico
  - Crear turnos para pacientes no registrados
  - Ver todos los turnos del consultorio
  - Filtrar turnos por médico, fecha y estado

---

## 🗂️ Estructura del Proyecto

```
consultorio_medico/
├── manage.py
├── requirements.txt
├── README.md
├── .env
├── db.sqlite3
├── consultorio/          # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── turnos/               # Aplicación principal
│   ├── models.py         # Modelos de datos
│   ├── views.py          # Lógica de vistas
│   ├── urls.py           # Rutas
│   ├── forms.py          # Formularios
│   ├── admin.py          # Configuración admin
│   ├── permissions.py    # Permisos personalizados
│   └── fixtures/         # Datos iniciales
│       └── initial_data.json
├── templates/            # Templates HTML
│   ├── base.html
│   ├── home.html
│   ├── auth/
│   ├── paciente/
│   └── secretaria/
└── static/               # Archivos estáticos (CSS, JS, imágenes)
```

---

## 📊 Modelo de Datos

### Entidades Principales

1. **Usuario** (Django User)
   - Autenticación y autorización

2. **Paciente** (OneToOne con User)
   - DNI, teléfono, domicilio
   - Cobertura médica
   - Número de afiliado
   - Categoría

3. **Médico**
   - Nombre, apellido, especialidad
   - Matrícula profesional
   - Coberturas que acepta (ManyToMany)
   - Estado activo/inactivo

4. **DisponibilidadMedico**
   - Día de la semana
   - Horario de inicio y fin
   - Duración de cada turno

5. **Cobertura**
   - Obras sociales/prepagas
   - Estado activa/inactiva

6. **Turno**
   - Paciente (puede ser null para turnos sin registro)
   - Médico
   - Fecha y hora
   - Estado (pendiente, confirmado, cancelado, completado)
   - Motivo y observaciones

### Relaciones

- **Usuario → Paciente**: 1:1
- **Paciente → Turno**: 1:N
- **Médico → Turno**: 1:N
- **Médico → DisponibilidadMedico**: 1:N
- **Médico ↔ Cobertura**: N:N
- **Cobertura → Paciente**: 1:N

---

## 🔑 Endpoints Principales

### Públicas
- `/` - Home page (redirige según usuario)
- `/login/` - Iniciar sesión
- `/registro/` - Registro de pacientes
- `/logout/` - Cerrar sesión

### Paciente (requiere login)
- `/paciente/` - Dashboard del paciente
- `/paciente/perfil/` - Editar perfil
- `/paciente/mis-turnos/` - Ver mis turnos
- `/paciente/reservar-turno/` - Reservar nuevo turno
- `/paciente/cancelar-turno/<id>/` - Cancelar turno

### Secretaria (requiere staff)
- `/secretaria/` - Dashboard de secretaría
- `/secretaria/medicos/` - Listar médicos
- `/secretaria/medicos/crear/` - Crear médico
- `/secretaria/medicos/<id>/editar/` - Editar médico
- `/secretaria/medicos/<id>/disponibilidad/` - Gestionar horarios
- `/secretaria/turnos/` - Ver todos los turnos
- `/secretaria/turnos/crear/` - Crear turno

### API
- `/api/horarios-disponibles/` - Obtener horarios disponibles (AJAX)

---

## 🛡️ Permisos y Seguridad

### Decoradores Personalizados

- `@paciente_required` - Solo pacientes registrados
- `@secretaria_required` - Solo personal staff
- `@verificar_permiso_turno` - Verificar acceso a turno específico

### Reglas de Negocio

- Los pacientes solo ven médicos que acepten su cobertura
- Los turnos solo pueden cancelarse con 24hs de anticipación
- No se pueden reservar horarios ya ocupados
- Los pacientes solo pueden ver/modificar sus propios turnos
- La secretaria tiene acceso total

---

## 🎨 Frontend

### TailwindCSS
El proyecto usa TailwindCSS via CDN para estilos modernos y responsivos.

### JavaScript
- Carga dinámica de horarios disponibles (AJAX)
- Validación de formularios
- Mensajes de feedback

### Componentes Reutilizables
- Navbar con menús contextuales
- Cards de estadísticas
- Tablas responsivas
- Formularios estilizados
- Mensajes flash

---

## 🔧 Comandos Útiles

### Crear migraciones
```bash
python manage.py makemigrations
```

### Aplicar migraciones
```bash
python manage.py migrate
```

### Crear superusuario
```bash
python manage.py createsuperuser
```

### Cargar fixtures
```bash
python manage.py loaddata turnos/fixtures/initial_data.json
```

### Recopilar archivos estáticos (producción)
```bash
python manage.py collectstatic
```

### Shell interactivo
```bash
python manage.py shell
```

### Ejecutar tests
```bash
# Todos los tests
python manage.py test

# Con detalles
python manage.py test --verbosity=2

# Con coverage
coverage run --source='turnos' manage.py test turnos
coverage report
```

Para más información sobre testing, ver [TESTING.md](TESTING.md)

---

## 📝 Administración Django

Acceder a: **http://127.0.0.1:8000/admin/**

Modelos disponibles en el admin:
- Coberturas
- Pacientes
- Médicos (con disponibilidades inline)
- Disponibilidades
- Turnos

---

## 🐛 Troubleshooting

### Error: "No module named 'decouple'"
```bash
pip install python-decouple
```

### Error de migraciones
```bash
python manage.py migrate --run-syncdb
```

### Puerto en uso
```bash
python manage.py runserver 8001
```

---

## 🚀 Deploy a Producción

### Consideraciones

1. **Cambiar SECRET_KEY** en `.env`
2. **DEBUG=False** en producción
3. **Configurar ALLOWED_HOSTS**
4. **Usar PostgreSQL** en lugar de SQLite
5. **Configurar archivos estáticos**:
   ```bash
   python manage.py collectstatic
   ```
6. **Configurar servidor web** (Nginx, Apache)
7. **Usar WSGI server** (Gunicorn, uWSGI)

### Ejemplo con Gunicorn
```bash
pip install gunicorn
gunicorn consultorio.wsgi:application --bind 0.0.0.0:8000
```

---

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

---

## 👨‍💻 Contacto

Para consultas o mejoras, crear un issue en el repositorio.

**¡Gracias por usar el Sistema de Turnos Médicos!** 🏥