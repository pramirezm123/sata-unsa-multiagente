"""
Agente de Explicabilidad (XAI).
Genera explicaciones locales interpretables mediante SHAP TreeExplainer
para descomponer las causas de riesgo de cada estudiante individual.
"""
from typing import Any

import pandas as pd
import shap

from ..messaging.message import AgentMessage
from .base_agent import BaseAgent

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

    def handle_message(self, message: AgentMessage) -> AgentMessage | None:
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

    def explain(self, input_vector: dict[str, Any], checkpoint: str, features_used: list[str]) -> dict[str, Any]:
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
            val_clean = 0.0 if pd.isna(val) else round(float(val), 2)
            imp_clean = 0.0 if pd.isna(impact) else round(float(impact), 4)
            factors.append({
                "feature": feat_name,
                "label": FEATURE_TRANSLATIONS.get(feat_name, feat_name),
                "value": val_clean,
                "impact": imp_clean,
                "direction": "Riesgo" if imp_clean > 0 else "Protección"
            })

        # Ordenar por magnitud de impacto
        factors = sorted(factors, key=lambda x: abs(x["impact"]), reverse=True)
        top_factors = factors[:6]

        return {
            "checkpoint": checkpoint,
            "top_factors": top_factors,
            "all_factors": factors
        }


def format_shap_factor_for_ui(factor: dict[str, Any] | None, max_abs_impact: float = 1.0) -> dict[str, Any]:
    """
    Normaliza y formatea un factor explicativo SHAP para su representación visual.
    Utiliza estrictamente la contribución SHAP ('impact') para signo, color y magnitud,
    separando el valor observado de la variable ('value').
    Maneja estructuras incompletas o valores nulos sin lanzar excepciones.
    """
    if not isinstance(factor, dict):
        return {
            "label": "Factor evaluado",
            "impact": 0.0,
            "impact_text": "+0.00",
            "observed_value": None,
            "direction": "Riesgo",
            "is_risk": True,
            "color_css": "var(--granate)",
            "width_pct": 0,
        }

    label = str(factor.get("label") or factor.get("feature") or "Factor evaluado")
    raw_impact = factor.get("impact")
    raw_value = factor.get("value")

    observed_str: str | None = None
    if raw_impact is not None and not (isinstance(raw_impact, float) and pd.isna(raw_impact)):
        try:
            impact_val = float(raw_impact)
            if pd.isna(impact_val):
                impact_val = 0.0
        except (ValueError, TypeError):
            impact_val = 0.0

        if raw_value is not None and not (isinstance(raw_value, float) and pd.isna(raw_value)):
            try:
                if isinstance(raw_value, int):
                    observed_str = str(raw_value)
                else:
                    val_f = float(raw_value)
                    if not pd.isna(val_f):
                        observed_str = str(int(val_f)) if val_f.is_integer() and isinstance(raw_value, int) else f"{val_f:g}" if val_f.is_integer() else f"{val_f:.1f}"
            except (ValueError, TypeError):
                observed_str = str(raw_value)
    else:
        # Compatibilidad con estructuras heredadas donde solo existía 'value' como impacto
        try:
            impact_val = float(raw_value) if raw_value is not None else 0.0
            if pd.isna(impact_val):
                impact_val = 0.0
        except (ValueError, TypeError):
            impact_val = 0.0

    if impact_val > 0:
        is_risk = True
    elif impact_val < 0:
        is_risk = False
    else:
        dir_raw = str(factor.get("direction") or "").strip().lower()
        is_risk = dir_raw not in ("protección", "proteccion", "protector")

    direction = "Riesgo" if is_risk else "Protección"
    color_css = "var(--granate)" if is_risk else "var(--azul-factor)"

    if 0.0 < abs(impact_val) < 0.005:
        impact_text = f"{impact_val:+.4f}"
    elif impact_val != 0.0:
        impact_text = f"{impact_val:+.2f}"
    else:
        impact_text = "+0.00" if is_risk else "-0.00"

    denom = max_abs_impact if (max_abs_impact and max_abs_impact > 0.0) else (abs(impact_val) if abs(impact_val) > 0.0 else 1.0)
    if abs(impact_val) == 0.0:
        width_pct = 0
    else:
        width_pct = max(4, min(100, int(round((abs(impact_val) / denom) * 100))))

    return {
        "label": label,
        "impact": impact_val,
        "impact_text": impact_text,
        "observed_value": observed_str,
        "direction": direction,
        "is_risk": is_risk,
        "color_css": color_css,
        "width_pct": width_pct,
    }
