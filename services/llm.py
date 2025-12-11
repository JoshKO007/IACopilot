import os
import time
from groq import Groq, APIConnectionError, RateLimitError, APIStatusError, InternalServerError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ErrorReintentable(Exception):
    pass

class ServicioLLM:
    def __init__(self):
        self.clave_api = os.getenv("GROQ_API_KEY")
        self.modelo = os.getenv("MODEL_ID", "llama-3.3-70b-versatile")
        
        self.cliente = Groq(api_key=self.clave_api)

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, ErrorReintentable, InternalServerError)),
        reraise=True 
    )
    def _llamada_api_cruda(self, mensajes, temp, tokens, top_p, seed):
        """
        Método interno protegido. Realiza la llamada "peligrosa" a la API.
        """
        try:
            respuesta = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=mensajes,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                seed=seed, 
                timeout=12.0 
            )
            return respuesta
            
        except APIStatusError as e:
            if e.status_code >= 500:
                raise ErrorReintentable(f"Error del servidor Groq ({e.status_code})")
            
            raise e

    def generar_respuesta(self, mensajes, temperatura=0.7, max_tokens=1024, top_p=1.0, seed=None):
        """
        Genera una respuesta manejando fallos y midiendo métricas.
        """
        inicio = time.time()
        
        try:
            completacion = self._llamada_api_cruda(mensajes, temperatura, max_tokens, top_p, seed)
            
            latencia = time.time() - inicio
            
            return {
                "contenido": completacion.choices[0].message.content,
                "uso": {
                    "tokens_entrada": completacion.usage.prompt_tokens,
                    "tokens_salida": completacion.usage.completion_tokens, 
                    "tokens_totales": completacion.usage.total_tokens
                },
                "latencia": round(latencia, 2),
                "error": None
            }

        except RateLimitError:
            return {
                "contenido": "**Sistema saturado.** Demasiadas peticiones. Intenta en 10 segundos.",
                "error": "RateLimit 429",
                "latencia": round(time.time() - inicio, 2)
            }
            
        except APIStatusError as e:
            msg = "Error técnico en la IA."
            if e.status_code == 401:
                msg = "**Error de Llave:** Revisa tu GROQ_API_KEY en el archivo .env"
            elif e.status_code == 400:
                msg = "**Solicitud Inválida:** Revisa el formato de los mensajes."
            
            return {
                "contenido": msg,
                "error": f"API Error {e.status_code}",
                "latencia": round(time.time() - inicio, 2)
            }
            
        except Exception as e:
            return {
                "contenido": "**Error de Conexión:** No puedo contactar al cerebro digital. Verifica tu internet.",
                "error": str(e),
                "latencia": round(time.time() - inicio, 2)
            }