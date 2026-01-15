# Duma Backend API

## Descripción del Proyecto

Duma Backend es una robusta API RESTful desarrollada con **Flask** diseñada para potenciar la plataforma de comercio electrónico y logística "Duma Express". El sistema gestiona procesos críticos como la integración con múltiples tiendas internacionales (Amazon, eBay, Walmart, etc.), gestión de usuarios, carritos de compra, pedidos, pagos y seguimiento de envíos.

### Características Principales
- **Arquitectura Modular**: Utiliza el patrón Factory de Flask y Blueprints para una clara separación de responsabilidades.
- **Documentación Automática**: API documentada con Swagger (Flask-RESTX).
- **Seguridad**: Autenticación basada en JWT, encriptación de datos sensibles y protección contra ataques de fuerza bruta (Rate Limiting).
- **Procesamiento Asíncrono**: Tareas en segundo plano gestionadas con Celery y Redis.
- **Integraciones**: Soporte para pasarelas de pago (Stripe, Braintree), notificaciones push (OneSignal) y actualización automática de tasas de cambio.

## Stack Tecnológico

- **Lenguaje**: Python 3.10+
- **Framework**: Flask, Flask-RESTX
- **Base de Datos**: PostgreSQL (SQLAlchemy ORM)
- **Cache / Message Broker**: Redis
- **Tareas en Segundo Plano**: Celery
- **Migraciones**: Flask-Migrate (Alembic)
- **Seguridad**: JWT, Argon2, Marshmallow (Validación)
- **Servidor de Producción**: Gunicorn

---

## Guía de Inicio Rápido

### Requisitos Previos
- Python 3.10 o superior
- PostgreSQL
- Redis
- Docker (opcional, para despliegue con contenedores)

### Instalación Local

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd duma-backend
   ```

2. **Configurar el entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Copia el archivo de ejemplo y completa los valores necesarios:
   ```bash
   cp .env.example .env
   ```
   *Nota: Asegúrate de configurar correctamente `DATABASE_URL`, `REDIS_URL` y generar una `ENCRYPTION_KEY`.*

5. **Inicializar la base de datos**:
   ```bash
   flask db-init      # Ejecuta las migraciones
   flask seed-all     # Inserta datos iniciales (tiendas, tasas de cambio)
   ```

6. **Crear usuario administrador**:
   ```bash
   flask create-superadmin --email admin@example.com --password tu_password --name "Admin Name"
   ```

7. **Ejecutar la aplicación**:
   ```bash
   python run.py
   ```
   La API estará disponible en `http://localhost:5000` y la documentación Swagger en `http://localhost:5000/api/docs`.

### Ejecución con Docker

Si prefieres usar Docker, puedes levantar todo el stack (API, DB, Redis, Celery) con un solo comando:

```bash
docker-compose up -d
```

---

## Comandos CLI Personalizados

El proyecto incluye varios comandos útiles accesibles a través de `flask`:

- `flask db-init`: Inicializa la base de datos ejecutando las migraciones pendientes.
- `flask db-reset`: Elimina y recrea todas las tablas (¡Cuidado: borra datos!).
- `flask seed-all`: Pobla la base de datos con tiendas por defecto y tasa de cambio inicial.
- `flask create-superadmin`: Crea un usuario con privilegios totales.
- `flask generate-encryption-key`: Genera una clave válida para la variable `ENCRYPTION_KEY`.
- `flask update-exchange-rate`: Actualiza las tasas de cambio desde la API externa.
- `flask show-routes`: Muestra todas las rutas registradas en la aplicación.

## Estructura del Proyecto

```text
app/
├── api/            # Endpoints de la API y lógica de rutas
├── models/         # Modelos de SQLAlchemy
├── schemas/        # Esquemas de Marshmallow para validación/serialización
├── services/       # Lógica de negocio y servicios externos
├── utils/          # Utilidades (encriptación, helpers)
├── config.py       # Configuraciones de entorno
└── extensions.py   # Inicialización de extensiones de Flask
run.py              # Punto de entrada de la aplicación
```
