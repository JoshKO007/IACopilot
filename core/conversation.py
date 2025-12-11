from typing import List, Dict, Optional

class GestorConversacion:
    def __init__(self):
        self.historial: List[Dict] = []
        self.notas: List[str] = []
        self.recordatorios: List[str] = [] 
        self.contador_turnos: int = 0
        self.limite_turnos: int = 20

    def procesar_comando(self, entrada_usuario: str) -> Optional[str]:
        texto = entrada_usuario.strip()
        comando = texto.lower()

        if self.contador_turnos >= self.limite_turnos and comando != "/limpiar":
            return "BLOCK: **Límite de sesión alcanzado.** Escribe `/limpiar` para reiniciar."

        if comando.startswith("/nota"):
            contenido = texto[5:].strip()
            if contenido:
                self.notas.append(contenido)
                return f"SYSTEM_INSTRUCTION: Se guardó la NOTA '{contenido}'. Confirma con 'Nota guardada'."
            return "SYSTEM_INSTRUCTION: Error de sintaxis. El usuario usó /nota vacío."

        if comando == "/misnotas":
            if not self.notas: return "SYSTEM_INSTRUCTION: El usuario pide notas. Dile que no tiene."
            return f"SYSTEM_INSTRUCTION: Muestra estas notas: {', '.join(self.notas)}."

        if comando.startswith("/recordatorio"):
            contenido = texto[13:].strip() 
            if contenido:
                self.recordatorios.append(contenido)
                return f"SYSTEM_INSTRUCTION: El usuario creó un RECORDATORIO: '{contenido}'. Confirma con una frase tipo 'Recordatorio establecido para: {contenido}'."
            return "SYSTEM_INSTRUCTION: Error. El usuario usó /recordatorio vacío."

        if comando.startswith("/busqueda"):
            consulta = texto[9:].strip() 
            if consulta:
                return f"SYSTEM_INSTRUCTION: MODO BÚSQUEDA ACTIVADO. El usuario busca: '{consulta}'. Ignora tu personalidad de asistente amable. Responde ÚNICAMENTE con la información factual, directa, resumida y sin saludos. Como si fueras un snippet de Google."
            return "SYSTEM_INSTRUCTION: Error. Usuario usó /busqueda vacío."

        if comando == "/limpiar":
            self.historial = []
            self.notas = []
            self.recordatorios = []
            self.contador_turnos = 0
            return "SYSTEM_INSTRUCTION: Memoria borrada. Saluda de nuevo."

        return None

    def actualizar_historial(self, rol: str, contenido: str):
        self.historial.append({"role": rol, "content": contenido})
        if rol == "assistant":
            self.contador_turnos += 1

    def obtener_historial(self) -> List[Dict]:
        return self.historial