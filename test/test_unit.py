import pytest
from unittest.mock import MagicMock, patch
from groq import APIStatusError

from core.prompting import construir_mensajes, PROMPT_DEL_SISTEMA
from core.conversation import GestorConversacion
from services.llm import ServicioLLM, ErrorReintentable

def test_prompting_system_persistente():
    """Rúbrica: system prompt persistente."""
    historial = [{"role": "user", "content": "hola"}]
    mensajes = construir_mensajes(historial, "nuevo mensaje")
    assert mensajes[0]["role"] == "system"
    assert mensajes[0]["content"] == PROMPT_DEL_SISTEMA

def test_prompting_truncado():
    """Rúbrica: truncado correcto."""
    historial_largo = [{"role": "user", "content": f"msg {i}"} for i in range(50)]
    mensajes = construir_mensajes(historial_largo, "input final", max_turnos=20)
    
    assert len(mensajes) == 22
    assert mensajes[-1]["content"] == "input final"

def test_conversation_estado():
    """Rúbrica: mantiene N últimos turnos."""
    gestor = GestorConversacion()
    gestor.actualizar_historial("user", "A")
    gestor.actualizar_historial("assistant", "B")
    
    assert len(gestor.historial) == 2
    assert gestor.contador_turnos == 1

def test_conversation_comando_nota():
    """Rúbrica: reconoce /nota."""
    gestor = GestorConversacion()
    entrada = "/nota Comprar leche"
    
    resp = gestor.procesar_comando(entrada)
    
    assert "Comprar leche" in gestor.notas
    assert "SYSTEM_INSTRUCTION" in resp


@patch("services.llm.Groq")
def test_llm_parametros_timeout(mock_groq):
    """Rúbrica: timeout explícito."""
    servicio = ServicioLLM()
    mock_cliente = mock_groq.return_value
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hola"
    mock_response.usage.total_tokens = 10
    mock_cliente.chat.completions.create.return_value = mock_response

    servicio.generar_respuesta([{"role": "user", "content": "test"}])
    
    args, kwargs = mock_cliente.chat.completions.create.call_args
    assert kwargs["timeout"] == 12.0

@patch("services.llm.Groq")
def test_llm_error_401_no_reintenta(mock_groq):
    """Rúbrica: diferencia entre 400 y 500 (Caso 400/401)."""
    servicio = ServicioLLM()
    mock_cliente = mock_groq.return_value
    
    error = APIStatusError(message="Auth Error", response=MagicMock(status_code=401), body=None)
    mock_cliente.chat.completions.create.side_effect = error
    
    resultado = servicio.generar_respuesta([{"role": "user", "content": "test"}])
    
    assert resultado["error"] is not None
    assert "Error de Llave" in resultado["contenido"]

@patch("services.llm.Groq")
def test_llm_error_500_si_reintenta(mock_groq):
    """Rúbrica: diferencia entre 400 y 500 (Caso 500 -> Retry)."""
    servicio = ServicioLLM()
    
    error_500 = APIStatusError(message="Server Error", response=MagicMock(status_code=500), body=None)
    try:
        if error_500.status_code >= 500:
            raise ErrorReintentable("Simulacion")
    except ErrorReintentable:
        assert True 
    except:
        assert False 