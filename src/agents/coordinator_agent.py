"""
Agente Coordinador del Sistema Multiagente SATA-UNSA.
Orquesta el ciclo de vida de la predicción, la interacción entre agentes
y garantiza la trazabilidad del proceso sin acoplamiento.
"""
import os
import time
from typing import Any

import psutil

from ..database.db import get_connection, log_bus_message, log_technical_metrics
from ..messaging.bus import MessageBus
from ..security.crypto import ensure_cui_hash
from .alert_agent import AlertAgent
from .base_agent import BaseAgent
from .ingestion_agent import IngestionAgent
from .predictor_agent import PredictorAgent
from .preprocessing_agent import PreprocessingAgent
from .recommendation_agent import RecommendationAgent
from .xai_agent import XaiAgent


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

    def analyze_student_risk(self, raw_payload: dict[str, Any], persist_telemetry: bool = True) -> dict[str, Any]:
        """
        Ejecuta la secuencia orquestada completa:
        1. Ingestión y validación de datos
        2. Preprocesamiento y variables de checkpoint
        3. Inferencia de riesgo con Random Forest
        4. Explicabilidad local SHAP
        5. Generación de recomendaciones pedagógicas
        6. Empaquetado final de alerta
        Instrumenta mediciones reales de latencia, RAM y overhead del bus FIPA-ACL.
        """
        t_total_start = time.perf_counter()
        overhead_bus_s = 0.0

        raw_id = str(raw_payload.get("CUI_HASH") or raw_payload.get("CUI") or "anon").strip()
        anon_id = ensure_cui_hash(raw_id) if (raw_id and raw_id.lower() != "anon") else "anon"
        conv_id = f"eval_{anon_id}_{len(self.bus.history)}"

        safe_payload = dict(raw_payload)
        if "CUI" in safe_payload:
            safe_payload["CUI"] = anon_id
        if "ID_ESTUDIANTE" in safe_payload:
            safe_payload["ID_ESTUDIANTE"] = anon_id

        # 1. Solicitar a IngestionAgent
        tb0 = time.perf_counter()
        self.send("IngestionAgent", "REQUEST", {"action": "INGEST", "payload": safe_payload}, conv_id)
        req_ingest = self.ingestion.receive()
        overhead_bus_s += time.perf_counter() - tb0
        if req_ingest:
            self.ingestion.handle_message(req_ingest)
        tb1 = time.perf_counter()
        msg_ingest = self.receive()
        overhead_bus_s += time.perf_counter() - tb1
        if not msg_ingest or msg_ingest.performative == "FAILURE":
            if persist_telemetry:
                try:
                    conn = get_connection()
                    for h_msg in self.bus.get_history_summary(conv_id):
                        log_bus_message(
                            request_id=conv_id,
                            emisor=str(h_msg.get("sender", "CoordinatorAgent")),
                            receptor=str(h_msg.get("receiver", "IngestionAgent")),
                            performativa=str(h_msg.get("performative", "FAILURE")),
                            topico=str(h_msg.get("topic") or h_msg.get("action") or "VALIDATION_FAILURE"),
                            contenido={
                                "cui_hash": anon_id,
                                "status": "FAILURE",
                                "topic": str(h_msg.get("topic") or "VALIDATION_FAILURE"),
                            },
                            duracion_ms=round(overhead_bus_s * 1000.0, 3),
                            conn=conn,
                        )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            return {"status": "ERROR", "errors": msg_ingest.content.get("errors", ["Error en ingestión"]) if msg_ingest else ["Timeout"]}
        
        clean_data = msg_ingest.content["data"]

        # 2. Solicitar a PreprocessingAgent
        tb0 = time.perf_counter()
        self.send("PreprocessingAgent", "REQUEST", {"action": "PREPROCESS", "data": clean_data}, conv_id)
        req_prep = self.preprocessing.receive()
        overhead_bus_s += time.perf_counter() - tb0
        if req_prep:
            self.preprocessing.handle_message(req_prep)
        tb1 = time.perf_counter()
        msg_prep = self.receive()
        overhead_bus_s += time.perf_counter() - tb1
        prep_data = msg_prep.content

        # 3. Solicitar a PredictorAgent (medición real de inferencia Random Forest)
        tb0 = time.perf_counter()
        self.send("PredictorAgent", "REQUEST", {
            "action": "PREDICT",
            "features": prep_data["features"],
            "checkpoint": prep_data["checkpoint"]
        }, conv_id)
        req_pred = self.predictor.receive()
        overhead_bus_s += time.perf_counter() - tb0
        t_inf_start = time.perf_counter()
        if req_pred:
            self.predictor.handle_message(req_pred)
        lat_inf_ms = (time.perf_counter() - t_inf_start) * 1000.0
        tb1 = time.perf_counter()
        msg_pred = self.receive()
        overhead_bus_s += time.perf_counter() - tb1
        pred_data = msg_pred.content

        # 4. Solicitar a XaiAgent (medición real de explicabilidad SHAP TreeExplainer)
        tb0 = time.perf_counter()
        self.send("XaiAgent", "REQUEST", {
            "action": "EXPLAIN",
            "input_vector": pred_data["input_vector"],
            "checkpoint": pred_data["checkpoint"],
            "features_used": pred_data["features_used"]
        }, conv_id)
        req_xai = self.xai.receive()
        overhead_bus_s += time.perf_counter() - tb0
        t_xai_start = time.perf_counter()
        if req_xai:
            self.xai.handle_message(req_xai)
        lat_xai_ms = (time.perf_counter() - t_xai_start) * 1000.0
        tb1 = time.perf_counter()
        msg_xai = self.receive()
        overhead_bus_s += time.perf_counter() - tb1
        xai_data = msg_xai.content

        # 5. Solicitar a RecommendationAgent
        tb0 = time.perf_counter()
        self.send("RecommendationAgent", "REQUEST", {
            "action": "RECOMMEND",
            "xai_data": xai_data,
            "pred_data": pred_data,
            "prep_data": prep_data
        }, conv_id)
        req_rec = self.recommendation.receive()
        overhead_bus_s += time.perf_counter() - tb0
        if req_rec:
            self.recommendation.handle_message(req_rec)
        tb1 = time.perf_counter()
        msg_rec = self.receive()
        overhead_bus_s += time.perf_counter() - tb1
        rec_data = msg_rec.content

        # 6. Solicitar a AlertAgent
        tb0 = time.perf_counter()
        self.send("AlertAgent", "REQUEST", {
            "action": "GENERATE_ALERT",
            "pred_data": pred_data,
            "prep_data": prep_data,
            "xai_data": xai_data,
            "rec_data": rec_data
        }, conv_id)
        req_alert = self.alert.receive()
        overhead_bus_s += time.perf_counter() - tb0
        if req_alert:
            self.alert.handle_message(req_alert)
        tb1 = time.perf_counter()
        msg_alert = self.receive()
        overhead_bus_s += time.perf_counter() - tb1
        alert_data = msg_alert.content

        lat_total_ms = (time.perf_counter() - t_total_start) * 1000.0
        overhead_bus_ms = overhead_bus_s * 1000.0
        ram_mb = round(psutil.Process(os.getpid()).memory_info().rss / (1024.0 * 1024.0), 2)

        telemetry = {
            "request_id": conv_id,
            "checkpoint": pred_data["checkpoint"],
            "latencia_inferencia_ms": round(lat_inf_ms, 3),
            "latencia_xai_ms": round(lat_xai_ms, 3),
            "latencia_total_ms": round(lat_total_ms, 3),
            "ram_mb": ram_mb,
            "overhead_bus_ms": round(overhead_bus_ms, 3),
        }

        history_summary = self.bus.get_history_summary(conv_id)

        if persist_telemetry:
            try:
                log_technical_metrics(
                    request_id=conv_id,
                    checkpoint=pred_data["checkpoint"],
                    lat_inf_ms=telemetry["latencia_inferencia_ms"],
                    lat_xai_ms=telemetry["latencia_xai_ms"],
                    lat_total_ms=telemetry["latencia_total_ms"],
                    ram_mb=telemetry["ram_mb"],
                    overhead_bus_ms=telemetry["overhead_bus_ms"],
                )
                step_dur = round(telemetry["overhead_bus_ms"] / max(len(history_summary), 1), 3)
                conn = get_connection()
                for h_msg in history_summary:
                    log_bus_message(
                        request_id=conv_id,
                        emisor=str(h_msg.get("sender", "CoordinatorAgent")),
                        receptor=str(h_msg.get("receiver", "Agent")),
                        performativa=str(h_msg.get("performative", "INFORM")),
                        topico=str(h_msg.get("topic") or h_msg.get("action") or "INFORM"),
                        contenido={
                            "cui_hash": anon_id,
                            "checkpoint": pred_data["checkpoint"],
                            "topic": str(h_msg.get("topic") or "INFORM"),
                            "performative": str(h_msg.get("performative", "INFORM")),
                        },
                        duracion_ms=step_dur,
                        conn=conn,
                    )
                conn.commit()
                conn.close()
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "alert": alert_data,
            "prediction": pred_data,
            "preprocessing": prep_data,
            "xai": xai_data,
            "recommendation": rec_data,
            "history": history_summary,
            "telemetry": telemetry,
        }
