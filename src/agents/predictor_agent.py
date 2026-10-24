"""
Agente Predictor de Riesgo Académico.
Carga los modelos entrenados Random Forest para cada Checkpoint (CP0 a CP3)
y genera la probabilidad calibrada de riesgo de reprobación.
"""
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..messaging.message import AgentMessage

HIST_NULOS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS",
    "DIFICULTAD_CURSO_HIST", "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"
]
BASE_HIST_FEATURES = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS", "CARGA_ACADEMICA",
    "SEMESTRES_DESDE_INGRESO", "ES_REPETICION", "DIFICULTAD_CURSO_HIST",
    "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"
] + [f"{c}_SIN_DATO" for c in HIST_NULOS]

CP0_FEATURES = BASE_HIST_FEATURES
CP1_FEATURES = BASE_HIST_FEATURES + [
    "PROBA_CP0", "EC1_VAL", "EP1_VAL", "EC1_AUSENTE", "EP1_AUSENTE",
    "PROM_F1", "PUNTOS_F1", "NOTA_MIN_PEND_F1", "IMPOSIBLE_APROBAR_F1", "FALTANTES_F1"
]
CP2_FEATURES = CP1_FEATURES + [
    "EC2_VAL", "EP2_VAL", "EC2_AUSENTE", "EP2_AUSENTE",
    "PROM_F2", "PUNTOS_F2", "PROM_F1_F2", "PUNTOS_F1_F2",
    "NOTA_MIN_PEND_F2", "IMPOSIBLE_APROBAR_F2", "TENDENCIA_F2_VS_F1", "FALTANTES_F1_F2"
]
CP3_FEATURES = CP2_FEATURES + [
    "EC3_VAL", "EP3_VAL", "EC3_AUSENTE", "EP3_AUSENTE",
    "PUNTOS_TOTAL", "PROM_TOTAL", "YA_APROBADO_CP3", "TENDENCIA_F3_VS_F2", "FALTANTES_TOTAL"
]

THRESHOLDS = {
    "CP0": 0.285,
    "CP1": 0.340,
    "CP2": 0.495,
    "CP3": 0.765
}


class PredictorAgent(BaseAgent):
    """Agente que gestiona los modelos en cascada y ejecuta inferencia."""
    def __init__(self, agent_id: str, bus, models_dir: str):
        super().__init__(agent_id, bus)
        self.models_dir = models_dir
        self.models = {}
        self._load_models()

    def _load_models(self):
        for cp in ["cp0", "cp1", "cp2", "cp3"]:
            path = os.path.join(self.models_dir, f"random_forest_{cp}.joblib")
            if os.path.exists(path):
                self.models[cp.upper()] = joblib.load(path)
            else:
                print(f"[ADVERTENCIA] Modelo {path} no encontrado.")

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        if message.performative == "REQUEST" and message.content.get("action") == "PREDICT":
            features = message.content.get("features", {})
            checkpoint = message.content.get("checkpoint", "CP0")
            
            prediction_result = self.predict(features, checkpoint)
            
            self.send(
                receiver=message.sender,
                performative="INFORM",
                content=prediction_result,
                conversation_id=message.conversation_id
            )
        return None

    def predict(self, features: Dict[str, Any], checkpoint: str) -> Dict[str, Any]:
        """Calcula PROBA_CP0 para stacking y evalúa el modelo del checkpoint."""
        model_cp0 = self.models.get("CP0")
        target_model = self.models.get(checkpoint)
        
        # 1. Calcular PROBA_CP0 si no existe
        df_cp0 = pd.DataFrame([features])[CP0_FEATURES]
        proba_cp0 = float(model_cp0.predict_proba(df_cp0)[0, 1]) if model_cp0 else 0.15
        features["PROBA_CP0"] = proba_cp0

        # 2. Selección de vector según checkpoint
        if checkpoint == "CP3":
            feat_cols = CP3_FEATURES
        elif checkpoint == "CP2":
            feat_cols = CP2_FEATURES
        elif checkpoint == "CP1":
            feat_cols = CP1_FEATURES
        else:
            feat_cols = CP0_FEATURES

        df_input = pd.DataFrame([features])[feat_cols]
        proba_risk = float(target_model.predict_proba(df_input)[0, 1]) if target_model else proba_cp0
        threshold = THRESHOLDS.get(checkpoint, 0.30)
        is_alert = bool(proba_risk >= threshold)

        return {
            "checkpoint": checkpoint,
            "probability": proba_risk,
            "threshold": threshold,
            "is_alert": is_alert,
            "features_used": feat_cols,
            "input_vector": df_input.iloc[0].to_dict()
        }
