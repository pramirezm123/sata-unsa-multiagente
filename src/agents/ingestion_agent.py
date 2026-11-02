"""
Agente de Recolección e Ingestión de Datos.
Valida y estandariza los datos ingresados por estudiantes o docentes en la interfaz.
"""
from typing import Any

import numpy as np

from ..messaging.message import AgentMessage
from .base_agent import BaseAgent


class IngestionAgent(BaseAgent):
    """Agente receptor y validador de entradas de notas parciales."""
    def __init__(self, agent_id: str, bus):
        super().__init__(agent_id, bus)

    def handle_message(self, message: AgentMessage) -> AgentMessage | None:
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

    def validate_payload(self, data: dict[str, Any]):
        """Valida rangos de calificaciones (0 a 20), suma de ponderaciones (100%) y variables basales."""
        errors = []
        cleaned = {}
        pesos_encontrados = {}

        for k, v in data.items():
            is_empty = (
                v is None or
                str(v).strip() == "" or
                str(v).strip().lower() in ["nan", "none", "null"] or
                (isinstance(v, float) and np.isnan(v))
            )
            if k in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
                if not is_empty:
                    try:
                        n = float(v)
                        if not (0.0 <= n <= 20.0):
                            errors.append(f"{k} debe estar entre 0.0 y 20.0 (recibido: {n})")
                        cleaned[k] = n
                    except (ValueError, TypeError):
                        errors.append(f"{k} no es un número válido: {v}")
                        cleaned[k] = None
                else:
                    cleaned[k] = None
            elif k.startswith("PESO_"):
                if not is_empty:
                    try:
                        p_val = float(v)
                        if p_val <= 0 or p_val > 100:
                            errors.append(f"{k} debe ser mayor a 0 y menor o igual a 100 (recibido: {p_val})")
                        cleaned[k] = p_val
                        pesos_encontrados[k] = p_val
                    except (ValueError, TypeError):
                        errors.append(f"{k} no es un número válido: {v}")
                        cleaned[k] = None
                else:
                    cleaned[k] = None
            elif k in ["IRA", "IRA_ACUM"]:
                if not is_empty:
                    try:
                        ira_val = float(v)
                        if not (0.0 <= ira_val <= 20.0):
                            errors.append(f"{k} debe estar entre 0.0 y 20.0 (recibido: {ira_val})")
                        cleaned[k] = ira_val
                    except (ValueError, TypeError):
                        errors.append(f"{k} no es un número válido: {v}")
                        cleaned[k] = None
                else:
                    cleaned[k] = None
            elif k in ["REPETICIONES", "REPROBACIONES_PREVIAS"]:
                if not is_empty:
                    try:
                        rep_val = int(float(v))
                        if rep_val < 0:
                            errors.append(f"{k} no puede ser negativo (recibido: {rep_val})")
                        cleaned[k] = rep_val
                    except (ValueError, TypeError):
                        errors.append(f"{k} no es un entero válido: {v}")
                        cleaned[k] = None
                else:
                    cleaned[k] = None
            elif k in ["CREDITOS_MATRICULADOS", "CARGA_ACADEMICA"]:
                if not is_empty:
                    try:
                        cred_val = float(v)
                        if cred_val <= 0:
                            errors.append(f"{k} debe ser un valor positivo (recibido: {cred_val})")
                        cleaned[k] = cred_val
                    except (ValueError, TypeError):
                        errors.append(f"{k} no es un número válido: {v}")
                        cleaned[k] = None
                else:
                    cleaned[k] = None
            else:
                cleaned[k] = v

        # Validación de que las 6 ponderaciones oficiales sumen 100% si se proporcionan
        eval_keys = ["PESO_EC1", "PESO_EP1", "PESO_EC2", "PESO_EP2", "PESO_EC3", "PESO_EP3"]
        if all(k in pesos_encontrados for k in eval_keys):
            suma_pesos = sum(pesos_encontrados[k] for k in eval_keys)
            if abs(suma_pesos - 100.0) > 0.01:
                errors.append(f"La suma de ponderaciones del sílabo debe ser 100% (recibido: {suma_pesos:.1f}%)")

        return cleaned, errors
