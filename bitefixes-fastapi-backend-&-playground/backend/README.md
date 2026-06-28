# Backend Omnicanal de Soporte Técnico - BiteFixes 🛠️🤖

Este repositorio contiene la estructura completa, modular y documentada del backend de producción para **BiteFixes**. Diseñado con una arquitectura de microservicios limpia, utiliza **FastAPI** como pasarela API robusta, **Supabase (PostgreSQL)** para persistencia transaccional rápida y el modelo **Gemini 3.5 Flash** de Google con **Function Calling** nativo para resolver conversaciones y automatizar operaciones de soporte técnico en tiempo real.

---

## 🏗️ Arquitectura Omnicanal de Flujo
```text
[ WhatsApp Chatbot (Meta) ] ──┐
[ Canal Web (Widget Chat)   ] ──┼─► [ FastAPI backend ] ──► [ Gemini 3.5 Flash ] (Decide herram.)
[ App Móvil (Soporte App)   ] ──┘         │                             │ (Function Calls)
                                          ▼                             ▼
                              [ Supabase database ] ◄───────────────────┘
                                - 'clientes' table
                                - 'tickets' table
```

---

## ⚡ Requisitos Previos

- **Python 3.10 o superior** instalado.
- Un proyecto activo en **Supabase** (puedes crear uno gratuito en [supabase.com](https://supabase.com)).
- Una llave de API de **Google Gemini** (puedes generarla gratis en [Google AI Studio](https://ai.studio)).
- Una cuenta de **Facebook Developer** con el producto **WhatsApp Business API** activado si deseas conectar el bot de WhatsApp real.

---

## 🚀 Despliegue y Puesta en Marcha Local

### 1. Clonar el proyecto y acceder al directorio
```bash
mkdir bitefixes-backend && cd bitefixes-backend
# Copia los archivos del hub en su respectiva estructura
```

### 2. Configurar el Entorno Virtual
Crea un entorno de ejecución aislado para evitar conflictos de dependencias en tu máquina:
```bash
python -m venv venv

# Activar en Windows:
venv\Scripts\activate

# Activar en Linux / macOS:
source venv/bin/activate
```

### 3. Instalar Dependencias Requeridas
Instala los módulos del archivo `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Inicializar la Base de Datos en Supabase
1. Ingresa a la consola de administración de tu proyecto en Supabase.
2. Abre la sección de **SQL Editor** y crea una nueva consulta.
3. Copia e ingresa todo el contenido del archivo `schema.sql` provisto en este hub.
4. Presiona **Run** para crear de inmediato las tablas de `clientes` y `tickets`, junto a los índices de búsqueda y datos demo para pruebas iniciales.

### 5. Configurar Variables de Entorno
Crea un archivo llamado `.env` en la raíz del proyecto basándote en `.env.example`:
```bash
cp .env.example .env
# Abre .env y edita las llaves de Supabase, Gemini y WhatsApp Business.
```

### 6. Ejecutar el Servidor de Desarrollo
Corre el servidor utilizando **Uvicorn**:
```bash
uvicorn app.main:app --reload --port 3000
```
El servidor estará activo de inmediato en: `http://localhost:3000`

---

## 🔗 Pruebas de Endpoints e Integración

### Documentación Interactiva de la API
FastAPI genera de forma automática documentación de producción interactiva bajo estándares de OpenAPI:
- **Swagger UI**: Accede a `http://localhost:3000/docs` para interactuar visualmente con los endpoints, simular requests y ver payloads de respuesta detallados.
- **Redoc**: Accede a `http://localhost:3000/redoc` para una lectura formal de especificaciones técnicas.

---

## 💬 Flujo Conversacional del Bot (Paso a Paso)

El bot está diseñado para guiar de manera inteligente al cliente sin que este se dé cuenta del flujo técnico subyacente:

1. **Recepción**: Llega el mensaje al webhook de WhatsApp con el número del cliente.
2. **Identificación**: Gemini recibe el contexto y solicita de inmediato la herramienta `tool_verificar_cliente`.
3. **Registro (Si es necesario)**:
   - Si no está registrado en Supabase, el bot le solicita su nombre y dirección de forma cordial.
   - Al recibir los datos, se llama a `tool_registrar_cliente`, guardándolos permanentemente en Supabase.
4. **Análisis del Problema**: El bot escucha la avería, la categoriza lógicamente (`Hardware`, `Software`, `Redes`, etc.), y llama a `tool_crear_ticket` para levantar el reporte de inmediato.
5. **Confirmación**: Se le entrega al cliente su número oficial de ticket para su tranquilidad, cerrando la interacción de manera profesional.
