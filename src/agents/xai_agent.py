"""
Agente de Explicabilidad (XAI).
Genera explicaciones locales interpretables mediante SHAP TreeExplainer
para descomponer las causas de riesgo de cada estudiante individual.
"""
import shap
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..messaging.message import AgentMessage

FEATURE_TRANSLATIONS = {
    "PROBA_CP0": "Riesgo histórico base (pre-semestre)",
    "NOTA_MIN_PEND_F1": "Nota mínima requerida en lo pendiente (Fase 1)",
    "NOTA_MIN_PEND_F2": "Nota mínima requerida en lo pendiente (Fase 2)",
    "PROM_F1": "Promedio ponderado en Fase 1",
    "PROM_F2": "Promedio ponderado en Fase 2",
    "PROM_F1_F2": "Promedio acumulado Fase 1 y 2",
    "EC1_VAL": "Evaluación Continua 1",
    "EP1_VAL": "Examen Parcial 1",
    "EC2_VAL": "Evaluación Continua 2",
    "EP2_VAL": "Examen Parcial 2",
    "EC3_VAL": "Evaluación Continua 3",
    "EP3_VAL": "Examen Parcial 3",
    "PROM_TOTAL": "Promedio ponderado final acumulado",
    "PUNTOS_TOTAL": "Puntos acumulados sobre 20",
    "TENDENCIA_F2_VS_F1": "Tendencia de rendimiento (Fase 2 vs 1)",
    "IMPOSIBLE_APROBAR_F1": "Imposibilidad matemática ordinaria (Fase 1)",
    "IMPOSIBLE_APROBAR_F2": "Imposibilidad matemática ordinaria (Fase 2)",
    "EC1_AUSENTE": "Inasistencia en Evaluación Continua 1",
    "EP1_AUSENTE": "Inasistencia en Examen Parcial 1",
    "EC2_AUSENTE": "Inasistencia en Evaluación Continua 2",
    "EP2_AUSENTE": "Inasistencia en Examen Parcial 2",
    "DIFICULTAD_CURSO_HIST": "Dificultad histórica de la asignatura",
    "DIFICULTAD_DOCENTE_HIST": "Dificultad histórica del docente",
    "DIFICULTAD_CURSO_DOCENTE_HIST": "Exigencia histórica docente-curso",
    "IRA_ACUM": "Índice de Rendimiento Acumulado (IRA)",
    "TASA_APROB_ACUM": "Tasa histórica de asignaturas aprobadas",
    "REPROBACIONES_PREVIAS": "Total de cursos reprobados previamente",
    "CARGA_ACADEMICA": "Carga de cursos matriculados",
    "SEMESTRES_DESDE_INGRESO": "Antigüedad en la carrera",
    "ES_REPETICION": "Asignatura llevada en segunda/tercera matrícula"
}


class XaiAgent(BaseAgent):
    """Agente que traduce predicciones complejas en explicaciones SHAP comprensibles."""
    def __init__(self, agent_id: str, bus, predictor_agent):
        super().__init__(agent_id, bus)
        self.predictor_agent = predictor_agent
        self.explainers = {}

    def _get_explainer(self, checkpoint: str):
        if checkpoint not in self.explainers:
            model = self.predictor_agent.models.get(checkpoint)
            if model:
                self.explainers[checkpoint] = shap.TreeExplainer(model)
        return self.explainers.get(checkpoint)

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        if message.performative == "REQUEST" and message.content.get("action") == "EXPLAIN":
            input_vector = message.content.get("input_vector", {})
            checkpoint = message.content.get("checkpoint", "CP0")
            features_used = message.content.get("features_used", [])

            explanation = self.explain(input_vector, checkpoint, features_used)

            self.send(
                receiver=message.sender,
                performative="INFORM",
                content=explanation,
                conversation_id=message.conversation_id
            )
        return None

    def explain(self, input_vector: Dict[str, Any], checkpoint: str, features_used: List[str]) -> Dict[str, Any]:
        """Calcula los valores SHAP locales de la instancia."""
        explainer = self._get_explainer(checkpoint)
        if not explainer:
            return {"factors": [], "summary": "Explicador no disponible."}

        df_row = pd.DataFrame([input_vector])[features_used]
        shap_vals = explainer.shap_values(df_row)

        if isinstance(shap_vals, list):
            sv = shap_vals[1][0]
        elif len(shap_vals.shape) == 3:
            sv = shap_vals[0, :, 1]
        else:
            sv = shap_vals[0]

        factors = []
        for feat_name, val, impact in zip(features_used, df_row.iloc[0], sv):
            factors.append({
                "feature": feat_name,
                "label": FEATURE_TRANSLATIONS.get(feat_name, feat_name),
                "value": round(float(val), 2),
                "impact": round(float(impact), 4),
                "direction": "Riesgo" if impact > 0 else "Protección"
            })

        # Ordenar por magnitud de impacto
        factors = sorted(factors, key=lambda x: abs(x["impact"]), reverse=True)
        top_factors = factors[:6]

        return {
            "checkpoint": checkpoint,
            "top_factors": top_factors,
            "all_factors": factors
        }
