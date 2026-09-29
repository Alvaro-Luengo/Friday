# ⚡ GUÍA INTEGRAL DE FRIDAY V2.0 ⚡
### Asistente Personal Inteligente, Antigravity Hub & App Nativa Android
**Creada para: Álvaro Luengo**

---

## 📌 ÍNDICE
1. [App Nativa Real para Android (Friday.apk)](#1-app-nativa-real-para-android-fridayapk)
2. [Funcionalidad Completa de Asistente Virtual (Estilo Ok Google)](#2-funcionalidad-completa-de-asistente-virtual-estilo-ok-google)
3. [Consola en Vivo de Antigravity (AGY) y Streaming en Tiempo Real](#3-consola-en-vivo-de-antigravity-agy-y-streaming-en-tiempo-real)
4. [Supervisor de Seguridad y Aprobación de Acciones Críticas](#4-supervisor-de-seguridad-y-aprobación-de-acciones-críticas)
5. [Historial Auditado de Operaciones](#5-historial-auditado-de-operaciones)
6. [El Tiempo Atmosférico (Hoy y Previsión 7 Días)](#6-el-tiempo-atmosférico-hoy-y-previsión-7-días)
7. [Indicador Visual en Pantalla PC (Esquina Superior Izquierda)](#7-indicador-visual-en-pantalla-pc-esquina-superior-izquierda)
8. [Configuración de Conexión y Enlace Remoto](#8-configuración-de-conexión-y-enlace-remoto)
9. [Arranque Automático y Control en PC](#9-arranque-automático-y-control-en-pc)

---

## 1. APP NATIVA REAL PARA ANDROID (FRIDAY.APK)

Se ha creado y compilado una **aplicación nativa real de Android** (no es un acceso directo de Chrome ni una PWA):

* **Archivo Instalador APK:** [Friday.apk](file:///D:/Friday/Friday.apk) (compilado en `D:\Friday\Friday.apk`).
* **Código Fuente Completo:** Ubicado en [android_app](file:///D:/Friday/android_app) con Gradle 8.13, Jetpack Compose Material 3, Android SDK 35 y Kotlin 2.0.
* **Descarga Directa desde el Móvil:**
  * Puedes descargar el APK en 1 clic abriendo en el navegador de tu móvil tu enlace fijo:
    👉 `https://unburst-stacee-reforgeable.ngrok-free.dev/download/friday.apk`
* **Compilación en 1 Clic:**
  * Si realizas cambios en el código de la app, solo ejecuta [compilar_apk.bat](file:///D:/Friday/compilar_apk.bat).

### Pasos de Instalación en tu POCO X8 Pro Max:
1. Abre el enlace `/download/friday.apk` en tu móvil o transfiere el archivo [Friday.apk](file:///D:/Friday/Friday.apk) por USB/Telegram.
2. Pulsa en el archivo descargado para instalarlo (*"Permitir instalar aplicaciones de orígenes desconocidos"*).
3. **Configurar como Asistente Digital Predeterminado (Sustituir a Ok Google):**
   * Ajustes de Android -> **Aplicaciones** -> **Aplicaciones predeterminadas** -> **Asistente digital**.
   * Selecciona **Friday**. ¡Ahora invocar el asistente con gesto o botón abrirá Friday!
4. **Permisos en HyperOS:**
   * Ajustes -> Aplicaciones -> Friday -> Conceder permisos de **Micrófono**, **Teléfono** y **Contactos**.
   * Activar **Inicio automático en segundo plano** y batería en **"Sin restricciones"**.

---

## 2. FUNCIONALIDAD COMPLETA DE ASISTENTE VIRTUAL (ESTILO OK GOOGLE)

Friday cuenta con un motor híbrido que detecta si la acción debe realizarse nativamente en tu teléfono o enviarse a tu ordenador:

* **💬 WhatsApp Nativo:**
  * *"Friday, envía un WhatsApp a mamá diciendo llego en 10 minutos"*
  * *"Friday, mensaje a mamá"*
  * Abre WhatsApp con el chat del contacto y el mensaje listo para enviar con 1 toque.
* **📞 Llamadas Telefónicas:**
  * *"Friday, llama a mamá"* / *"Friday, marcar al 657188367"*
  * Lanza la llamada automáticamente mediante el marcador telefónico de Android.
* **🎵 Spotify Integrado:**
  * *"Friday, pon Coldplay en Spotify"* / *"Friday, reproduce Back in Black"* / *"Friday, modo poder"*
  * Abre la app de Spotify en el móvil y comienza la reproducción de la canción seleccionada.
* **📅 Hora, Fecha y Día en Directo:**
  * *"Friday, ¿qué hora es?"* -> *"Son las 18:05."*
  * *"Friday, ¿qué día es hoy?"* -> *"Hoy es martes, 29 de septiembre de 2026, y son las 18:05."*
* **🌤️ Tiempo y Clima (Hoy y 7 Días):**
  * *"Friday, ¿qué tiempo hace?"* / *"Friday, el tiempo esta semana"* / *"Friday, ¿va a llover?"*
  * Consulta Open-Meteo Madrid y muestra tarjetas detalladas con temperaturas máximas/mínimas, probabilidad de lluvia y descripción.
* **📍 Ubicación y Rutas (Google Maps):**
  * *"Friday, cómo ir a Gran Vía"* / *"Friday, dónde estoy"*
  * Lanza la navegación en Google Maps directamente.
* **🔍 Búsquedas en Internet (Google Search):**
  * *"Friday, busca en Google resultados del Real Madrid"*
  * Abre Google Search con los resultados de la consulta.

---

## 3. CONSOLA EN VIVO DE ANTIGRAVITY (AGY) Y STREAMING EN TIEMPO REAL

Tanto en la App Android nativa como en el enlace web tienes una **consola en vivo dedicada para Antigravity**:

* **Streaming en Directo (SSE):**
  * Cuando pides a AGY una tarea (ej: *"Crea un script que compruebe la memoria"* o *"Desarrolla una función para procesar datos"*), las palabras, razonamientos y llamadas a herramientas se transmiten letra por letra a tu pantalla en tiempo real.
* **Parámetros Automáticos:**
  * Incorpora `--dangerously-skip-permissions` para auto-aprobar herramientas del agente sin bloquearse por falta de terminal.
  * Opción de sesión continua (`-c`) para mantener el hilo de la conversación anterior.
* **Monitoreo de Herramientas:**
  * Los pasos de ejecución muestran distintivos claros como `[HERRAMIENTA: run_command]`, `[ESCRIBIENDO ARCHIVO: ...]`, o `[CONSULTANDO AGENTE]`.

---

## 4. SUPERVISOR DE SEGURIDAD Y APROBACIÓN DE ACCIONES CRÍTICAS

Para proteger tu ordenador de eliminaciones involuntarias o modificaciones no deseadas:

1. **Detección Automática de Peligro:**
   * Si una petición o herramienta de AGY intenta **eliminar archivos o carpetas** (ej: comandos `del`, `rmdir`, `Remove-Item`, `unlink`, `shutil.rmtree`) o **modificar archivos críticos del sistema** (`main.py`, `config.py`, `.env`, directorios raíz), Friday pausa automáticamente la ejecución.
2. **Alerta en la Pantalla del Móvil:**
   * Tu teléfono vibra y muestra una tarjeta de alerta de seguridad en rojo:
     > ⚠️ **CONFIRMACIÓN DE SEGURIDAD REQUERIDA**  
     > *Acción detectada: Eliminación de archivos / Modificación de archivo crítico*  
     > `[RECHAZAR]` `[AUTORIZAR ACCIÓN]`
3. **Decisión en Tus Manos:**
   * Si pulsas **Autorizar**, la tarea continúa con `--dangerously-skip-permissions`.
   * Si pulsas **Rechazar** o pasan 45 segundos sin respuesta, la acción se cancela inmediatamente sin tocar ningún archivo.

---

## 5. HISTORIAL AUDITADO DE OPERACIONES

Todas las instrucciones enviadas a AGY se registran de forma inmutable en [agy_audit.jsonl](file:///D:/Friday/agy_audit.jsonl):
* Fecha y hora exacta.
* Texto del prompt solicitado.
* Estado final (`COMPLETED`, `REJECTED`, `ERROR`).
* Herramientas ejecutadas en tu ordenador.
* Tokens consumidos y duración en segundos.
* Puedes consultar este historial en cualquier momento desde la pestaña **"Historial"** de la app o el endpoint `/api/agy/history`.

---

## 6. EL TIEMPO ATMOSFÉRICO (HOY Y PREVISIÓN 7 DÍAS)

Sincronizado vía Open-Meteo Madrid:
* Muestra temperatura actual, sensación térmica, estado del cielo, humedad y viento.
* Tarjetas para cada día de la semana con:
  * Día de la semana (Hoy, Mañana, Jueves, Viernes...).
  * Máxima y mínima prevista.
  * Probabilidad porcentual de lluvia (🌧️ %).

---

## 7. INDICADOR VISUAL EN PANTALLA PC (ESQUINA SUPERIOR IZQUIERDA)

* **Dónde aparece:** En la **esquina superior izquierda** de tu pantalla principal (`x=24, y=28`).
* **Aspecto:** HUD cyber holográfico semi-transparente con borde cian brillante (`#00ffc8`), icono de micrófono pulsante 🎤 y el texto `FRIDAY ESCUCHANDO...`.
* **Comportamiento:**
  * En reposo permanece 100% invisible.
  * Al decir *"Friday"* o *"Fraydey"*, aparece de inmediato y suena el pitido de inicio.
  * Al terminar de hablar, suena el pitido de procesamiento y se oculta.

---

## 8. CONFIGURACIÓN DE CONEXIÓN Y ENLACE REMOTO

* **Enlace Fijo Permanente Actual:**
  👉 `https://unburst-stacee-reforgeable.ngrok-free.dev`
* **PIN de Seguridad:** `1234` (configurable en [config.py](file:///D:/Friday/config.py) y en los ajustes de la app).
* **Endpoints Clave de la API:**
  * `GET /download/friday.apk`: Descarga directa del APK.
  * `POST /api/agy/stream`: Streaming SSE de Antigravity en vivo.
  * `POST /api/agy/approve`: Autorización remota de acciones críticas.
  * `GET /api/agy/history`: Historial auditado.
  * `GET /api/status`: Métricas del PC (CPU, RAM, Disco, Batería).
  * `GET /api/weather`: Previsión meteorológica de 7 días.

---

## 9. ARRANQUE AUTOMÁTICO Y CONTROL EN PC

* [start_visible.bat](file:///D:/Friday/start_visible.bat): Inicia Friday en ventana de consola visible para depuración.
* [start_hidden.vbs](file:///D:/Friday/start_hidden.vbs): Inicia Friday en segundo plano de forma silenciosa e invisible.
* [stop_friday.bat](file:///D:/Friday/stop_friday.bat): Detiene todos los procesos de Friday y sus túneles.
* [friday_status.bat](file:///D:/Friday/friday_status.bat): Muestra si Friday está activa y la URL actual.
* [compilar_apk.bat](file:///D:/Friday/compilar_apk.bat): Recompila la app de Android en 1 clic.
