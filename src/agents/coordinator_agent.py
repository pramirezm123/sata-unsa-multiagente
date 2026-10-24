"""
Agente Coordinador del Sistema Multiagente SATA-UNSA.
Orquesta el ciclo de vida de la predicción, la interacción entre agentes
y garantiza la trazabilidad del proceso sin acoplamiento.
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from ..messaging.bus import MessageBus
from .ingestion_agent import IngestionAgent
from .preprocessing_agent import PreprocessingAgent
from .predictor_agent import PredictorAgent
from .xai_agent import XaiAgent
from .recommendation_agent import RecommendationAgent
from .alert_agent import AlertAgent


class CoordinatorAgent(BaseAgent):
    """Agente director que coordina el flujo secuencial y asíncrono del sistema."""
    def __init__(self, agent_id: str, bus: MessageBus, models_dir: str):
        super().__init__(agent_id, bus)
        
        # Instanciar e inicializar todos los agentes del ecosistema
        self.ingestion = IngestionAgent("IngestionAgent", bus)
        self.preprocessing = PreprocessingAgent("PreprocessingAgent", bus)
        self.predictor = PredictorAgent("PredictorAgent", bus, models_dir)
        self.xai = XaiAgent("XaiAgent", bus, self.predictor)
        self.recommendation = RecommendationAgent("RecommendationAgent", bus)
        self.alert = AlertAgent("AlertAgent", bus)

    def handle_message(self, message):
        return None

    def analyze_student_risk(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la secuencia orquestada completa:
        1. Ingestión y validación de datos
        2. Preprocesamiento y variables de checkpoint
        3. Inferencia de riesgo con Random Forest
        4. Explicabilidad local SHAP
        5. Generación de recomendaciones pedagógicas
        6. Empaquetado final de alerta
        """
        conv_id = f"eval_{raw_payload.get('CUI', 'anon')}_{int(self.bus.history.__len__())}"

        # 1. Solicitar a IngestionAgent
        self.send("IngestionAgent", "REQUEST", {"action": "INGEST", "payload": raw_payload}, conv_id)
        msg_ingest = self.ingestion.receive()
        if not msg_ingest or msg_ingest.performative == "FAILURE":
            return {"status": "ERROR", "errors": msg_ingest.content.get("errors", ["Error en ingestión"]) if msg_ingest else ["Timeout"]}
        
        clean_data = msg_ingest.content["data"]

        # 2. Solicitar a PreprocessingAgent
        self.send("PreprocessingAgent", "REQUEST", {"action": "PREPROCESS", "data": clean_data}, conv_id)
        msg_prep = self.preprocessing.receive()
        prep_data = msg_prep.content

        # 3. Solicitar a PredictorAgent
        self.send("PredictorAgent", "REQUEST", {
            "action": "PREDICT",
            "features": prep_data["features"],
            "checkpoint": prep_data["checkpoint"]
        }, conv_id)
        msg_pred = self.predictor.receive()
        pred_data = msg_pred.content

        # 4. Solicitar a XaiAgent
        self.send("XaiAgent", "REQUEST", {
            "action": "EXPLAIN",
            "input_vector": pred_data["input_vector"],
            "checkpoint": pred_data["checkpoint"],
            "features_used": pred_data["features_used"]
        }, conv_id)
        msg_xai = self.xai.receive()
        xai_data = msg_xai.content

        # 5. Solicitar a RecommendationAgent
        self.send("RecommendationAgent", "REQUEST", {
            "action": "RECOMMEND",
            "xai_data": xai_data,
            "pred_data": pred_data,
            "prep_data": prep_data
        }, conv_id)
        msg_rec = self.recommendation.receive()
        rec_data = msg_rec.content

        # 6. Solicitar a AlertAgent
        self.send("AlertAgent", "REQUEST", {
            "action": "GENERATE_ALERT",
            "pred_data": pred_data,
            "prep_data": prep_data,
            "xai_data": xai_data,
            "rec_data": rec_data
        }, conv_id)
        msg_alert = self.alert.receive()
        alert_data = msg_alert.content

        return {
            "status": "SUCCESS",
            "alert": alert_data,
            "prediction": pred_data,
            "preprocessing": prep_data,
            "xai": xai_data,
            "recommendation": rec_data,
            "history": self.bus.get_history_summary()
        }
