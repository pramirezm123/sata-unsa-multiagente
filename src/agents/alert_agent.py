"""
Agente de Alertas y Notificación.
Categoriza el nivel de riesgo en 4 estados operativos y emite fichas de alerta
estructuradas para presentación en el dashboard institucional.
"""
from typing import Any

from ..messaging.message import AgentMessage
from .base_agent import BaseAgent


class AlertAgent(BaseAgent):
    """Agente que gestiona la categorización y entrega de alertas tempranas."""
    def __init__(self, agent_id: str, bus):
        super().__init__(agent_id, bus)

    def handle_message(self, message: AgentMessage) -> AgentMessage | None:
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
        pred: dict[str, Any],
        prep: dict[str, Any],
        xai: dict[str, Any],
        rec: dict[str, Any]
    ) -> dict[str, Any]:
        """Estructura la ficha de alerta institucional."""
        p = pred.get("probability", 0.0)
        u = pred.get("threshold", 0.30)
        checkpoint = pred.get("checkpoint", "CP0")
        f = prep.get("features", {})
        if checkpoint == "CP1" and "IMPOSIBLE_APROBAR_NORM_F1" in f:
            imposible = f.get("IMPOSIBLE_APROBAR_NORM_F1", 0)
        elif checkpoint == "CP2" and "IMPOSIBLE_APROBAR_NORM_F2" in f:
            imposible = f.get("IMPOSIBLE_APROBAR_NORM_F2", 0)
        elif checkpoint == "CP3" and "IMPOSIBLE_APROBAR_NORM_CP3" in f:
            imposible = f.get("IMPOSIBLE_APROBAR_NORM_CP3", 0)
        else:
            imposible = f.get("IMPOSIBLE_APROBAR_F1", 0) or f.get("IMPOSIBLE_APROBAR_F2", 0)

        # Categorización calibrada del Semáforo con Banda Amarilla (0.75 * umbral)
        th_yellow = round(0.75 * u, 4)
        imposible_bool = bool(imposible == 1)

        if imposible_bool or p >= u:
            level = "CRÍTICO" if (imposible_bool or p >= 0.70) else "ALTO"
            color = "#D32F2F" if level == "CRÍTICO" else "#EF4444"
            badge = "Alerta Crítica (Intervención Urgente)" if level == "CRÍTICO" else "Alerta Temprana Activa (Riesgo Alto)"
        elif p >= th_yellow:
            level = "MEDIO"
            color = "#F59E0B"
            badge = "Alerta Preventiva (Banda Amarilla - Riesgo Moderado)"
        else:
            level = "BAJO"
            color = "#22C55E"
            badge = "Desempeño Seguro (Riesgo Bajo)"

        if checkpoint == "CP1":
            meta_raw = f.get("NOTA_MIN_NORM_PEND_F1", f.get("NOTA_MIN_PEND_F1", 10.5))
            meta_nota_min = round(float(meta_raw), 2)
        elif checkpoint == "CP2":
            meta_raw = f.get("NOTA_MIN_NORM_PEND_F2", f.get("NOTA_MIN_PEND_F2", 10.5))
            meta_nota_min = round(float(meta_raw), 2)
        else:
            meta_nota_min = None

        return {
            "risk_level": level,
            "badge": badge,
            "color": color,
            "probability": p,
            "probability_pct": round(p * 100.0, 2),
            "threshold": u,
            "threshold_pct": round(u * 100.0, 2),
            "threshold_yellow": th_yellow,
            "checkpoint": checkpoint,
            "is_alert": bool(pred.get("is_alert", False) or p >= u or imposible_bool),
            "imposible_ordinario": imposible_bool,
            "top_factors": xai.get("top_factors", []),
            "recommendations": rec.get("actions", []),
            "meta_nota_min": meta_nota_min,
            "promedio_acumulado": round(f.get("PROM_F1" if checkpoint == "CP1" else ("PROM_F1_F2" if checkpoint == "CP2" else "PROM_TOTAL"), 0.0), 2)
        }
