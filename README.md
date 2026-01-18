# 🏛️ Especificación de Arquitectura de Software: Ecosistema "Chef Edwin"

**Título Oficial:** Plataforma de Asistencia Educativa Culinaria Basada en Inteligencia Artificial Generativa Multimodal
**Versión del Documento:** 1.0 (first edition)
**Fecha de Emisión:** Diciembre 2025
**Autor:** Carlos Benavides 
**Marco de Referencia:** C4 Model, IEEE 1471 (4+1), ISO/IEC 25010
**Nivel de Acceso:** Uso Corporativo

---

## 📑 Índice Maestro

1.  **Visión y Contexto (Modelo C4)**
2.  **Vista Lógica y de Datos (ERD)**
3.  **Vista de Procesos (Flujos Dinámicos)**
4.  **Vista de Desarrollo y Decisiones (ADR)**
5.  **Vista Física e Infraestructura**
6.  **Requisitos y Niveles de Servicio (SLA)**
7.  **Gestión de Riesgos y Seguridad**
8.  **Evolución Futura**

---

## 1. Visión y Contexto (Modelo C4)

### 1.1 Resumen Ejecutivo
Chef Edwin es una plataforma de **Tutoría Culinaria Inteligente** implementada como un sistema web en Python. Utiliza la API de **Google Gemini** para proveer retroalimentación educativa inmediata a estudiantes a través de **WhatsApp**, actuando como un intermediario inteligente que procesa texto, audio e imágenes.

### 1.2 Diagrama de Contexto (Nivel 1)

Diagrama de Contexto Chef Edwin
<img width="1536" height="1024" alt="ChatGPT Image 23 dic 2025, 02_23_07" src="https://github.com/user-attachments/assets/35b58769-9a42-41f7-8d5d-f3743ca86427" />)

### 1.3 Diagrama de Contenedores (Nivel 2 - Realidad V1)
Refleja estrictamente el código desplegado actual: Monolito Django.
![Diagrama de Contenedores Chef Edwin](https://github.com/user-attachments/assets/3ddcf2fb-5d45-408f-ad2b-69ebd9610af4)
## 2. Vista Lógica y de Datos (ERD)

### 2.1 Modelo de Datos Actual
Esquema relacional implementado en `assistant/models.py`.

```mermaid
erDiagram
    STUDENT ||--o{ CONVERSATION_LOG : genera
    
    STUDENT {
        bigint id PK
        string phone_number UK
        string role "student|teacher"
        boolean is_authenticated
        datetime created_at
    }

    CONVERSATION_LOG {
        bigint id PK
        bigint student_id FK
        text message_body
        text chef_response
        timestamp timestamp
    }
```

---

## 3. Vista de Procesos (Flujos Dinámicos)

### 3.1 Modelo de Concurrencia (Síncrono)
Actualmente, el sistema opera con **Workers Síncronos** (Gunicorn).
1.  WhatsApp envía mensaje.
2.  Worker de Django recibe petición.
3.  Worker llama a Gemini (Espera ~3-5s).
4.  Worker guarda en BD.
5.  Worker responde a WhatsApp.
*Nota: Este modelo requiere configurar `timeout` alto en Gunicorn para evitar errores con imágenes pesadas.*

### 3.2 Diagrama de Secuencia: Flujo Real V1
```mermaid
sequenceDiagram
    autonumber
    actor User as Estudiante
    participant WA as WhatsApp
    participant App as Django View
    participant Logic as ai_service.py
    participant DB as Database
    participant Gemini as Google API

    User->>WA: "Dame una receta"
    WA->>App: POST /webhook
    
    activate App
    App->>DB: Get Student(phone)
    
    alt Usuario Autenticado
        App->>Logic: get_chef_response()
        activate Logic
        Logic->>DB: Fetch Last 5 Logs
        Logic->>Gemini: GenerateContent(History + Msg)
        Gemini-->>Logic: "Aquí tienes la receta..."
        Logic-->>App: Texto Generado
        deactivate Logic
        
        App->>DB: Save ConversationLog
        App-->>WA: TwiML <Response>
    else No Autenticado
        App-->>WA: "Pide Contraseña"
    end
    deactivate App
    
    WA-->>User: Mensaje en Celular
```

---

## 4. Vista de Desarrollo y Decisiones (ADR)

### 4.1 Stack Tecnológico Implementado
*   **Backend:** Python 3.11 + Django 5.2.
*   **Servidor Web:** Gunicorn (Producción - Render) / Runserver (Dev).
*   **Base de Datos:** PostgreSQL con `dj-database-url`.
*   **IA:** `google-generativeai` SDK.
*   **Archivos:** Sistema de archivos efímero (`/tmp`) para descargas temporales de audio/imagen.

### 4.2 Registro de Decisiones Arquitectónicas (ADR)

| ID | Título | Contexto | Decisión | Consecuencia |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-01** | **Django vs Microframeworks** | Necesidad de MVP rápido con Admin. | **Usar Django.** | Mayor tamaño de imagen Docker, pero Admin Panel gratis. |
| **ADR-02** | **Procesamiento Síncrono** | Complejidad de colas (Redis). | **Mantener síncrono en V1.** | Simplicidad de despliegue. Riesgo de timeout en audios largos (mitigable con timeouts altos). |
| **ADR-03** | **Gemini Multimodal** | Transcripción de Audio. | **Usar Gemini nativo.** | Ahorra integrar Whisper/Deepgram. Dependencia fuerte de Google. |

---

## 5. Vista Física e Infraestructura

### 5.1 Diagrama de Despliegue (Render PaaS)

```mermaid
graph TD
    subgraph Internet
        User[Móvil]
        Admin[Navegador]
    end

    subgraph "Nube (Render.com)"
        LB[Load Balancer]
        
        subgraph "Web Service"
            Django[Instancia Gunicorn]
            TempFile[Disco Efímero /tmp]
        end
        
        subgraph "Managed Data"
            Postgres[(Base de Datos)]
        end
    end
    
    subgraph "Google Cloud"
        VertexAI[Gemini API]
    end
    
    User -->|HTTPS| LB
    Admin -->|HTTPS| LB
    LB --> Django
    Django --> Postgres
    Django -->|API Call| VertexAI
    Django -->|Escribe| TempFile
```

---

## 6. Requisitos Implementados

### 6.1 Funcionalidades Actuales
*   **RF-01:** Webhook compatible con Twilio para Texto, Imagen y Audio.
*   **RF-02:** Autenticación básica por contraseña (campo `is_authenticated` en BD).
*   **RF-03:** Diferenciación de Roles (Prompt de Profesor vs Estudiante).
*   **RF-04:** Historial de conversación persistente en PostgreSQL.

### 6.2 SLAs Actuales
*   **Latencia Promedio:** 3-6 segundos (dependiente de API Google).
*   **Disponibilidad:** Dependiente de Render Free/Starter Tier.

---

## 7. Gestión de Riesgos Actuales

| Riesgo | Estado | Mitigación en Código |
| :--- | :--- | :--- |
| **Timouts de Webhook** | Activo | El código optimiza las descargas de medios. Si Google tarda >15s, Twilio falla. |
| **Alucinaciones** | Mitigado | Prompt del sistema (System Prompt) incluye instrucciones de seguridad alimentaria. |
| **Costos API** | Monitorizado | Uso de modelo `gemini-flash` para minimizar costos. |

---

## 8. Evolución Futura (Roadmap)

Tecnologías consideradas para futuras versiones (No implementadas aún):
*   **V2:** Tablas de Perfil y Gamificación.
*   **V3:** Colas de tareas para evitar timeouts en audios largos.
*   **V4:** Interfaz Web React separada.

---
**Firma de Aprobación Técnica:**
*CarlosBena Chef Edwin - V1.0*
