"""
Agente de Recolección e Ingestión de Datos.
Valida y estandariza los datos ingresados por estudiantes o docentes en la interfaz.
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..messaging.message import AgentMessage


class IngestionAgent(BaseAgent):
    """Agente receptor y validador de entradas de notas parciales."""
    def __init__(self, agent_id: str, bus):
        super().__init__(agent_id, bus)

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        if message.performative == "REQUEST" and message.content.get("action") == "INGEST":
            raw_input = message.content.get("payload", {})
            validated, errors = self.validate_payload(raw_input)

            if errors:
                self.send(
                    receiver=message.sender,
                    performative="FAILURE",
                    content={"errors": errors},
                    conversation_id=message.conversation_id
                )
            else:
                self.send(
                    receiver=message.sender,
                    performative="INFORM",
                    content={"data": validated},
                    conversation_id=message.conversation_id
                )
        return None

    def validate_payload(self, data: Dict[str, Any]):
        """Valida rangos de calificaciones (0 a 20) y normaliza strings."""
        errors = []
        cleaned = {}

        for k, v in data.items():
            if k in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
                if v is not None and str(v).strip() != "":
                    try:
                        n = float(v)
                        if not (0.0 <= n <= 20.0):
                            errors.append(f"{k} debe estar entre 0.0 y 20.0 (recibido: {n})")
                        cleaned[k] = n
                    except ValueError:
                        errors.append(f"{k} no es un número válido: {v}")
                else:
                    cleaned[k] = None
            elif k.startswith("PESO_"):
                if v is not None and str(v).strip() != "":
                    try:
                        cleaned[k] = float(v)
                    except ValueError:
                        cleaned[k] = None
                else:
                    cleaned[k] = None
            else:
                cleaned[k] = v

        return cleaned, errors
