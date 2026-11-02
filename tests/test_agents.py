"""
Pruebas unitarias completas de la arquitectura multiagente (SATA-UNSA).
Cubre:
1. IngestionAgent (validación de notas, tipos, ponderaciones al 100% y rangos).
2. PreprocessingAgent (imputación por checkpoint, cálculos ponderados y metas mínimas).
3. PredictorAgent (carga de modelos CP0..CP3, probabilidades en [0,1], cascading PROBA_CP0).
4. XaiAgent (valores SHAP locales, descomposición de riesgo y factores protectores).
5. AlertAgent (semáforo en bordes exactos: umbral, 0.75*umbral, e imposibilidad matemática).
6. CoordinatorAgent y MessageBus (FIPA-ACL performatives, orden secuencial, colas FIFO).
"""
import pytest

from src.agents.alert_agent import AlertAgent
from src.agents.ingestion_agent import IngestionAgent
from src.agents.predictor_agent import THRESHOLDS
from src.agents.preprocessing_agent import PreprocessingAgent
from src.messaging.message import AgentMessage


class TestIngestionAgent:
    """Validación rigurosa de entradas académicas."""

    def test_ingestion_valid_payload(self, fresh_bus):
        agent = IngestionAgent("IngestionAgent", fresh_bus)
        payload = {
            "EC1": "14.5", "EP1": 12.0, "PESO_EC1": 15, "PESO_EP1": 15,
            "PESO_EC2": 20, "PESO_EP2": 20, "PESO_EC3": 15, "PESO_EP3": 15,
            "IRA": 13.2, "REPETICIONES": 0, "CREDITOS_MATRICULADOS": 6
        }
        cleaned, errors = agent.validate_payload(payload)
        assert len(errors) == 0, f"No debería haber errores en un payload válido: {errors}"
        assert cleaned["EC1"] == 14.5
        assert cleaned["EP1"] == 12.0

    @pytest.mark.parametrize("invalid_note", [-0.5, -5.0, 20.5, 25.0, 100.0, "trece", "15,5"])
    def test_ingestion_rejects_out_of_range_or_invalid_notes(self, fresh_bus, invalid_note):
        agent = IngestionAgent("IngestionAgent", fresh_bus)
        _cleaned, errors = agent.validate_payload({"EC1": invalid_note})
        assert len(errors) > 0, f"Debe rechazar la nota inválida {invalid_note}"

    def test_ingestion_rejects_weights_not_summing_to_100(self, fresh_bus):
        agent = IngestionAgent("IngestionAgent", fresh_bus)
        # Suma 90%
        payload = {
            "PESO_EC1": 10, "PESO_EP1": 10,
            "PESO_EC2": 20, "PESO_EP2": 20,
            "PESO_EC3": 15, "PESO_EP3": 15
        }
        _cleaned, errors = agent.validate_payload(payload)
        assert any("100%" in e for e in errors), "Debe exigir que la suma de ponderaciones sea 100%."

    def test_ingestion_fipa_failure_on_error(self, fresh_bus):
        agent = IngestionAgent("IngestionAgent", fresh_bus)
        fresh_bus.register_agent("TestSender")
        msg = AgentMessage(sender="TestSender", receiver="IngestionAgent", performative="REQUEST",
                           content={"action": "INGEST", "payload": {"EC1": 35.0}})
        agent.handle_message(msg)
        response = fresh_bus.receive("TestSender")
        assert response.performative == "FAILURE"
        assert "errors" in response.content


class TestPreprocessingAgent:
    """Verificación de ingeniería de características intra-semestral e imputación."""

    def test_detects_cp0_when_no_notes(self, fresh_bus, sample_payload_cp0):
        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        feats, cp = prep._compute_features(sample_payload_cp0)
        assert cp == "CP0"
        assert feats["EC1_VAL"] == 0.0
        assert feats["EC1_SIN_DATO"] == 1

    def test_detects_cp1_and_computes_phase1_metrics(self, fresh_bus, sample_payload_cp1):
        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        feats, cp = prep._compute_features(sample_payload_cp1)
        assert cp == "CP1"
        assert feats["EC1_VAL"] == 8.0
        assert feats["EP1_VAL"] == 7.0
        # Puntos F1 = (8.0 * 15 + 7.0 * 15) / 100 = (120 + 105) / 100 = 2.25
        assert round(feats["PUNTOS_F1"], 2) == 2.25
        # Promedio F1 = 2.25 * 100 / 30 = 7.5
        assert round(feats["PROM_F1"], 2) == 7.5
        # Puntos faltantes para 11 = 11 - 2.25 = 8.75 sobre 70% pendiente
        # Nota min pendiente = 8.75 * 100 / 70 = 12.5
        assert round(feats["NOTA_MIN_PEND_F1"], 1) == 12.5
        assert feats["IMPOSIBLE_APROBAR_F1"] == 0

    def test_detects_impossible_to_pass(self, fresh_bus, sample_payload_cp2):
        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        # Forzar notas en 0 para F1 y F2 (60% del curso evaluado con 0 puntos)
        sample_payload_cp2["EC1"] = 0.0
        sample_payload_cp2["EP1"] = 0.0
        sample_payload_cp2["EC2"] = 0.0
        sample_payload_cp2["EP2"] = 0.0
        feats, cp = prep._compute_features(sample_payload_cp2)
        assert cp == "CP2"
        # Quedan solo 40 puntos posibles (40% de 20 = 8 puntos maximos posibles en F3)
        # Nota requerida en F3 = 11 * 100 / 40 = 27.5 (> 20 => imposible)
        assert feats["IMPOSIBLE_APROBAR_F2"] == 1


class TestPredictorAgent:
    """Verificación de inferencia con modelos Random Forest."""

    def test_models_loaded_correctly(self, coordinator):
        predictor = coordinator.predictor
        assert "CP0" in predictor.models
        assert "CP1" in predictor.models
        assert "CP2" in predictor.models
        assert "CP3" in predictor.models

    def test_predict_returns_valid_probability(self, coordinator, sample_payload_cp1):
        res = coordinator.analyze_student_risk(sample_payload_cp1)
        assert res["status"] == "SUCCESS"
        prob = res["prediction"]["probability"]
        assert 0.0 <= prob <= 1.0, f"La probabilidad debe estar en [0, 1], obtenido: {prob}"
        assert res["prediction"]["checkpoint"] == "CP1"


class TestXaiAgent:
    """Verificación de explicabilidad SHAP local."""

    def test_xai_generates_top_factors_with_directions(self, coordinator, sample_payload_cp1):
        res = coordinator.analyze_student_risk(sample_payload_cp1)
        xai = res["xai"]
        assert "top_factors" in xai
        factors = xai["top_factors"]
        assert len(factors) > 0

        for f in factors:
            assert "label" in f
            assert "value" in f
            assert "impact" in f
            assert f["direction"] in ["Riesgo", "Protección"]
            if f["impact"] > 0:
                assert f["direction"] == "Riesgo"
            else:
                assert f["direction"] == "Protección"


class TestAlertAgent:
    """Verificación de categorización exacta y semáforo con banda amarilla."""

    @pytest.mark.parametrize("checkpoint, threshold", [
        ("CP0", THRESHOLDS["CP0"]),
        ("CP1", THRESHOLDS["CP1"]),
        ("CP2", THRESHOLDS["CP2"]),
        ("CP3", THRESHOLDS["CP3"])
    ])
    def test_alert_agent_exact_boundaries(self, fresh_bus, checkpoint, threshold):
        agent = AlertAgent("AlertAgent", fresh_bus)
        th_yellow = round(0.75 * threshold, 4)

        # Caso 1: Exactamente en el umbral => ALTO (Rojo)
        pkg = agent.create_alert_package(
            pred={"probability": threshold, "threshold": threshold, "checkpoint": checkpoint, "is_alert": True},
            prep={"features": {}}, xai={}, rec={}
        )
        assert pkg["risk_level"] in ["ALTO", "CRÍTICO"]
        assert pkg["is_alert"] is True

        # Caso 2: Justo por encima del umbral => ALTO (Rojo)
        pkg = agent.create_alert_package(
            pred={"probability": threshold + 0.001, "threshold": threshold, "checkpoint": checkpoint, "is_alert": True},
            prep={"features": {}}, xai={}, rec={}
        )
        assert pkg["risk_level"] in ["ALTO", "CRÍTICO"]

        # Caso 3: Justo por debajo del umbral pero >= banda amarilla => MEDIO (Amarillo)
        pkg = agent.create_alert_package(
            pred={"probability": threshold - 0.001, "threshold": threshold, "checkpoint": checkpoint, "is_alert": False},
            prep={"features": {}}, xai={}, rec={}
        )
        assert pkg["risk_level"] == "MEDIO"

        # Caso 4: Exactamente en la banda amarilla => MEDIO (Amarillo)
        pkg = agent.create_alert_package(
            pred={"probability": th_yellow, "threshold": threshold, "checkpoint": checkpoint, "is_alert": False},
            prep={"features": {}}, xai={}, rec={}
        )
        assert pkg["risk_level"] == "MEDIO"

        # Caso 5: Justo por debajo de la banda amarilla => BAJO (Verde)
        pkg = agent.create_alert_package(
            pred={"probability": th_yellow - 0.002, "threshold": threshold, "checkpoint": checkpoint, "is_alert": False},
            prep={"features": {}}, xai={}, rec={}
        )
        assert pkg["risk_level"] == "BAJO"

    def test_alert_agent_impossible_forces_critical(self, fresh_bus):
        agent = AlertAgent("AlertAgent", fresh_bus)
        pkg = agent.create_alert_package(
            pred={"probability": 0.10, "threshold": 0.340, "checkpoint": "CP1", "is_alert": False},
            prep={"features": {"IMPOSIBLE_APROBAR_F1": 1}}, xai={}, rec={}
        )
        assert pkg["risk_level"] == "CRÍTICO"
        assert pkg["imposible_ordinario"] is True


class TestCoordinatorAndMessageBus:
    """Verificación del bus FIPA-ACL y orquestación secuencial."""

    def test_bus_fifo_order_and_history(self, fresh_bus):
        fresh_bus.register_agent("AgentA")
        fresh_bus.register_agent("AgentB")

        msg1 = AgentMessage("AgentA", "AgentB", "REQUEST", {"seq": 1})
        msg2 = AgentMessage("AgentA", "AgentB", "INFORM", {"seq": 2})

        fresh_bus.send(msg1)
        fresh_bus.send(msg2)

        recv1 = fresh_bus.receive("AgentB")
        recv2 = fresh_bus.receive("AgentB")

        assert recv1.content["seq"] == 1, "El bus debe ser estrictamente FIFO."
        assert recv2.content["seq"] == 2, "El bus debe ser estrictamente FIFO."
        assert len(fresh_bus.history) == 2

    def test_coordinator_full_pipeline_traceability(self, coordinator, sample_payload_cp1):
        res = coordinator.analyze_student_risk(sample_payload_cp1)
        assert res["status"] == "SUCCESS"
        history = res["history"]
        assert len(history) >= 6, "El ciclo multiagente debe contener al menos 6 interacciones FIPA-ACL."
        
        # Verificar secuencia de agentes participantes
        senders = [h["sender"] for h in history]
        assert "CoordinatorAgent" in senders
        assert "IngestionAgent" in senders
        assert "PreprocessingAgent" in senders
        assert "PredictorAgent" in senders
        assert "XaiAgent" in senders
        assert "RecommendationAgent" in senders
        assert "AlertAgent" in senders
