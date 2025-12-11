AI Copilot MVP
Este proyecto consiste en un asistente conversacional inteligente desarrollado en Python. La aplicación demuestra la implementación de un ciclo de vida completo de interacción con Modelos de Lenguaje Grande (LLMs), incluyendo gestión de memoria a corto plazo, uso de herramientas simuladas (comandos), persistencia de estado por sesión y una arquitectura resiliente ante fallos de red.

1. Stack Técnico y Modelo Utilizado
La arquitectura se ha seleccionado priorizando la latencia ultra-baja y la robustez del sistema.

Lenguaje: Python 3.9+

Framework de Interfaz: Streamlit. Seleccionado por su capacidad de gestión de estado de sesión (st.session_state) y renderizado rápido de componentes de UI.

Proveedor de Inferencia: Groq.

Justificación: Se utiliza Groq debido a su arquitectura LPU (Language Processing Unit), la cual ofrece velocidades de inferencia significativamente superiores a las soluciones basadas en GPU tradicionales, permitiendo una experiencia de chat en tiempo real.

Modelo: llama-3.1-8b-instant (Meta).

Justificación: Este modelo ofrece el mejor equilibrio entre velocidad y capacidad de razonamiento para tareas de asistencia general. Su ventana de contexto y capacidad de seguimiento de instrucciones son suficientes para la lógica de este MVP sin incurrir en los tiempos de espera de modelos más grandes (70b).

Gestión de Errores: Librería tenacity. Implementa patrones de Exponential Backoff para manejar límites de velocidad (Rate Limits) y errores transitorios de red.

2. Parámetros de Inferencia y Rationale
El usuario dispone de control explícito sobre los hiperparámetros del modelo a través de la interfaz lateral. La configuración predeterminada y su justificación técnica son:

Temperature (0.0 - 1.0): Controla la entropía/aleatoriedad de la salida.

Rationale: Valor por defecto 0.7. Mantiene un equilibrio entre respuestas deterministas (para comandos y datos) y creatividad (para conversación fluida).

Top_P (0.0 - 1.0): Muestreo de núcleo (Nucleus Sampling).

Rationale: Valor por defecto 1.0. Restringe la selección de tokens a aquellos que componen la masa de probabilidad acumulada, filtrando alucinaciones o palabras incoherentes de baja probabilidad.

Max Tokens: Límite de longitud de generación.

Rationale: Valor por defecto 512. Previene la generación de bucles infinitos y controla el consumo de recursos por turno.

Seed (Semilla): Entero para reproducibilidad.

Rationale: Permite fijar el estado aleatorio del modelo, útil para pruebas de regresión y depuración (debugging), asegurando que el mismo input genere el mismo output.

3. Descripción de la Lógica Conversacional
El sistema no envía mensajes crudos al modelo; utiliza un pipeline de procesamiento intermedio:

System Prompt Persistente: Se inyecta al inicio de cada interacción un prompt maestro que define:

Rol y Tono (Consultor experto y empático).

Protocolos de Seguridad (Guardrails contra contenido ilícito).

Gestión de Memoria Silenciosa (Instrucción para recordar datos del usuario sin confirmarlos explícitamente).

Procesamiento de Comandos (Tool Use Simulado): Antes de llamar al LLM, un analizador léxico intercepta el input.

Si detecta comandos (/nota, /recordatorio, /busqueda), ejecuta la lógica localmente y genera una "Instrucción de Sistema" oculta para guiar la respuesta del LLM.

Si detecta el límite de sesión (20 turnos), bloquea la ejecución para prevenir abuso del servicio gratuito.

Ventana Deslizante (Sliding Window):

Para mantener la coherencia sin exceder el límite de tokens de entrada, se truncan los mensajes antiguos, enviando únicamente el System Prompt + los últimos 20 turnos de conversación.

4. Métricas de Desempeño
Los siguientes datos reflejan el comportamiento del sistema bajo pruebas de carga estándar en un entorno de desarrollo.

Latencia (Tiempo de Respuesta):

p50 (Mediana): ~0.56 segundos. (Respuesta típica).

p95 (Cola): ~0.68 segundos. (Incluye casos de reintentos leves).

Consumo de Tokens (Promedio por turno):

Entrada: ~800 tokens (System Prompt robusto + Historial acumulado).

Salida: ~50 - 150 tokens (Respuestas concisas).

Fiabilidad:

Tasa de Reintentos: < 5% (Manejados automáticamente por tenacity).

Tasa de Fallbacks Visibles: < 0.1% (Errores críticos de autenticación o caída total del servicio).

5. Limitaciones y Posibles Mejoras
Como MVP (Producto Mínimo Viable), el sistema presenta las siguientes limitaciones intencionales que representan oportunidades de mejora futura:

Volatilidad de Datos: La memoria (historial, notas y recordatorios) reside en st.session_state (RAM). Si se recarga la página, los datos se pierden.

Mejora: Integrar una base de datos ligera (SQLite o Redis) para persistencia a largo plazo.

Contexto Limitado: La ventana de 20 turnos olvida información antigua en conversaciones muy extensas.

Mejora: Implementar una base de datos vectorial (RAG) para recuperar información relevante antigua semánticamente.

Ejecución de Comandos: Actualmente los comandos solo simulan la acción mediante confirmación de texto.

Mejora: Conectar /busqueda a una API real (como Google Serper) y /recordatorio a un servicio de calendario real (Google Calendar API).