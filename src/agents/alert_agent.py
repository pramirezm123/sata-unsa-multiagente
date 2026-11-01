"""
Agente de Alertas y Notificación.
Categoriza el nivel de riesgo en 4 estados operativos y emite fichas de alerta
estructuradas para presentación en el dashboard institucional.
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..messaging.message import AgentMessage


class AlertAgent(BaseAgent):
    """Agente que gestiona la categorización y entrega de alertas tempranas."""
    def __init__(self, agent_id: str, bus):
        super().__init__(agent_id, bus)

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        if message.performative == "REQUEST" and message.content.get("action") == "GENERATE_ALERT":
            pred = message.content.get("pred_data", {})
            prep = message.content.get("prep_data", {})
            xai = message.content.get("xai_data", {})
            rec = message.content.get("rec_data", {})

            alert_package = self.create_alert_package(pred, prep, xai, rec)

            self.send(
                receiver=message.sender,
                performative="INFORM",
                content=alert_package,
                conversation_id=message.conversation_id
            )
        return None

    def create_alert_package(
        self,
        pred: Dict[str, Any],
        prep: Dict[str, Any],
        xai: Dict[str, Any],
        rec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estructura la ficha de alerta institucional."""
        p = pred.get("probability", 0.0)
        u = pred.get("threshold", 0.30)
        checkpoint = pred.get("checkpoint", "CP0")
        f = prep.get("features", {})
        imposible = f.get("IMPOSIBLE_APROBAR_F1", 0) or f.get("IMPOSIBLE_APROBAR_F2", 0)

        # Categorización en 4 niveles operativos
        if imposible == 1 or p >= 0.70:
            level = "CRÍTICO"
            color = "#D32F2F"  # Rojo oscuro
            badge = "Alerta Crítica (Intervención Urgente)"
        elif p >= u:
            level = "ALTO"
            color = "#F57C00"  # Naranja
            badge = "Alerta Temprana Activa (Riesgo Significativo)"
        elif p >= 0.20:
            level = "MEDIO"
            color = "#FBC02D"  # Amarillo/Ámbar
            badge = "Seguimiento Preventivo (Riesgo Moderado)"
        else:
            level = "BAJO"
            color = "#388E3C"  # Verde
            badge = "Desempeño Seguro (Sin Riesgo Aparente)"

        return {
            "risk_level": level,
            "badge": badge,
            "color": color,
            "probability_pct": round(p * 100.0, 2),
            "threshold_pct": round(u * 100.0, 2),
            "checkpoint": checkpoint,
            "is_alert": pred.get("is_alert", False),
            "top_factors": xai.get("top_factors", []),
            "recommendations": rec.get("actions", []),
            "meta_nota_min": round(f.get("NOTA_MIN_PEND_F1" if checkpoint == "CP1" else "NOTA_MIN_PEND_F2", 11.0), 2) if checkpoint in ["CP1", "CP2"] else None,
            "promedio_acumulado": round(f.get("PROM_F1" if checkpoint == "CP1" else ("PROM_F1_F2" if checkpoint == "CP2" else "PROM_TOTAL"), 0.0), 2)
        }
