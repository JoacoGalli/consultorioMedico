# Docker Deployment - Consultorio Médico

## Quick Start (Desarrollo)

```bash
# 1. Clonar y entrar al directorio
cd consultorioMedico

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Construir e iniciar
docker-compose up --build

# 4. Aplicar migraciones y cargar datos
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata turnos/fixtures/initial_data.json

# 5. Crear superusuario
docker-compose exec web python manage.py createsuperuser
```

La app estará disponible en: http://localhost:8000

## Production Deployment

### 1. Configurar variables de entorno

Editar `.env` con valores reales:

```env
SECRET_KEY=your-super-secure-random-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgres://user:password@host:5432/dbname
```

### 2. Configurar Nginx (SSL)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # ... resto de nginx.conf
}
```

### 3. Deploy con Docker Compose

```bash
# Production
docker-compose -f docker-compose.yml up -d --build

# Ver logs
docker-compose logs -f web

# Restart
docker-compose restart web
```

## Comandos útiles

```bash
# Ver contenedores
docker-compose ps

# Entrar al contenedor
docker-compose exec web bash

# Ver logs
docker-compose logs -f

# Recrear base de datos
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata turnos/fixtures/initial_data.json

# Backup base de datos
docker-compose exec db pg_dump -U postgres consultorio > backup.sql

# Restaurar backup
cat backup.sql | docker-compose exec -T db psql -U postgres consultorio
```

## Estructura de archivos

```
├── Dockerfile           # Imagen Docker de la app
├── docker-compose.yml   # Orquestación de servicios
├── nginx.conf          # Configuración de Nginx
├── gunicorn.conf.py    # Configuración de Gunicorn
├── entrypoint.sh       # Script de inicio
├── requirements.txt    # Dependencias Python
└── .env                # Variables de entorno (no commitear)
```

## Servicios

- **web**: Aplicación Django (puerto 8000)
- **db**: PostgreSQL 16 (puerto 5432)
- **nginx**: Reverse proxy (puerto 80/443)
