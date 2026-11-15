"""
Agente de Recomendación Pedagógica.
Mapea los factores determinantes identificados por el Agente XAI (SHAP)
hacia intervenciones académicas concretas y metas cuantitativas.
"""
from typing import Any

from ..messaging.message import AgentMessage
from .base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    """Agente que genera recomendaciones de apoyo académico personalizadas."""
    def __init__(self, agent_id: str, bus):
        super().__init__(agent_id, bus)

    def handle_message(self, message: AgentMessage) -> AgentMessage | None:
        if message.performative == "REQUEST" and message.content.get("action") == "RECOMMEND":
            xai_data = message.content.get("xai_data", {})
            pred_data = message.content.get("pred_data", {})
            prep_data = message.content.get("prep_data", {})

            recommendations = self.generate_recommendations(xai_data, pred_data, prep_data)

            self.send(
                receiver=message.sender,
                performative="PROPOSE",
                content=recommendations,
                conversation_id=message.conversation_id
            )
        return None

    def generate_recommendations(
        self,
        xai_data: dict[str, Any],
        pred_data: dict[str, Any],
        prep_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Aplica reglas pedagógicas basadas en causas raíz explicadas por XAI."""
        recs: list[str] = []
        checkpoint = pred_data.get("checkpoint", "CP0")
        is_alert = pred_data.get("is_alert", False)
        f = prep_data.get("features", {})
        top_factors = xai_data.get("top_factors", [])

        # 1. Regla por nota mínima requerida en pendientes
        if checkpoint in ["CP1", "CP2"]:
            nota_min = f.get("NOTA_MIN_PEND_F1" if checkpoint == "CP1" else "NOTA_MIN_PEND_F2", 11.0)
            imposible = f.get("IMPOSIBLE_APROBAR_F1" if checkpoint == "CP1" else "IMPOSIBLE_APROBAR_F2", 0)
            
            if imposible == 1:
                recs.append(
                    "Situación Crítica: Con el sistema de evaluación ordinario, el estudiante no alcanza nota 11. "
                    "Se debe activar orientación inmediata para preparar el Examen Sustitutorio al cierre de ciclo."
                )
            elif nota_min > 14.0:
                recs.append(
                    f"Meta de Aprobación Alta: El alumno necesita un promedio de {nota_min:.1f} en las evaluaciones restantes. "
                    "Se recomienda agendar tutoría semanal y reforzar temas clave previo al siguiente examen."
                )
            elif nota_min > 11.0:
                recs.append(
                    f"Meta Moderada: Requiere un promedio de {nota_min:.1f} en lo pendiente para asegurar la aprobación."
                )

        # 2. Regla por inasistencia / ausencias
        if f.get("EC1_AUSENTE") == 1 or f.get("EP1_AUSENTE") == 1:
            recs.append(
                "Alerta de Inasistencia: Se registra ausencia en evaluaciones de Fase 1. "
                "Docente debe verificar motivos de inasistencia (justificación médica o problema de conectividad)."
            )

        # 3. Regla por disparidad Continua vs Examen (Tensión evaluativa)
        if checkpoint in ["CP1", "CP2"]:
            ep1 = f.get("EP1_VAL", 11.0)
            ec1 = f.get("EC1_VAL", 11.0)
            if ec1 >= 14.0 and ep1 <= 7.0:
                recs.append(
                    "Disparidad de Rendimiento: El estudiante presenta buen trabajo práctico (Continua) pero caída severa en el examen teórico. "
                    "Se sugiere reforzar técnicas de estudio para pruebas escritas y resolución de ejercicios bajo límite de tiempo."
                )

        # 4. Regla por dificultad histórica del curso o docente
        if f.get("DIFICULTAD_CURSO_HIST", 0) > 0.15:
            recs.append(
                "Asignatura de Alta Exigencia: Esta materia tiene una tasa histórica de reprobación superior al promedio. "
                "Priorizar al estudiante para talleres de nivelación de la escuela profesional."
            )

        # 5. Regla por factor dominante identificado por XAI
        if is_alert and top_factors:
            primer_factor = top_factors[0]
            if primer_factor.get("direction") == "Riesgo" and len(recs) == 0:
                recs.append(
                    f"Atención en factor crítico: {primer_factor.get('label', 'Variable')} es el elemento que más eleva el riesgo estimado."
                )

        # Si no hay alertas de riesgo
        if not is_alert and not recs:
            recs.append("Desempeño Satisfactorio: El estudiante mantiene un ritmo adecuado de aprobación. Mantener el seguimiento regular.")

        return {
            "checkpoint": checkpoint,
            "actions": recs,
            "priority": "Alta" if is_alert else "Baja"
        }
