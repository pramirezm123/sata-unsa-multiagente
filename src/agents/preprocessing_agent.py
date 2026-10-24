"""
Agente de Preprocesamiento y Análisis Académico.
Valida notas, imputa valores faltantes según reglas oficiales y calcula
las variables intra-semestrales exactas para los Checkpoints CP0 a CP3.
"""
import numpy as np
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..messaging.message import AgentMessage


class PreprocessingAgent(BaseAgent):
    """Agente responsable de la validación y transformación de datos en variables predictivas."""
    def __init__(self, agent_id: str, bus):
        super().__init__(agent_id, bus)
        # Medias globales del histórico de entrenamiento para imputación de priors
        self.default_historical = {
            "IRA_ACUM": 12.85,
            "TASA_APROB_ACUM": 0.88,
            "REPROBACIONES_PREVIAS": 0.42,
            "CARGA_ACADEMICA": 5.8,
            "SEMESTRES_DESDE_INGRESO": 4.1,
            "ES_REPETICION": 0,
            "DIFICULTAD_CURSO_HIST": 0.08,
            "DIFICULTAD_DOCENTE_HIST": 0.07,
            "DIFICULTAD_CURSO_DOCENTE_HIST": 0.08
        }
        self.default_weights = {
            "PESO_EC1": 15.0, "PESO_EP1": 15.0,
            "PESO_EC2": 20.0, "PESO_EP2": 20.0,
            "PESO_EC3": 15.0, "PESO_EP3": 15.0
        }

    def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        if message.performative == "REQUEST" and message.content.get("action") == "PREPROCESS":
            raw_data = message.content.get("data", {})
            features_dict, checkpoint = self._compute_features(raw_data)
            
            response_content = {
                "checkpoint": checkpoint,
                "features": features_dict,
                "raw_data": raw_data
            }
            self.send(
                receiver=message.sender,
                performative="INFORM",
                content=response_content,
                conversation_id=message.conversation_id
            )
        return None

    def _compute_features(self, data: Dict[str, Any]):
        """Construye el vector de características dinámico y detecta el Checkpoint."""
        f = {}
        # 1. Variables históricas base
        for k, def_val in self.default_historical.items():
            val = data.get(k)
            if val is None or str(val).strip() == "" or (isinstance(val, float) and np.isnan(val)):
                f[k] = def_val
                f[f"{k}_SIN_DATO"] = 1
            else:
                f[k] = float(val)
                f[f"{k}_SIN_DATO"] = 0

        # 2. Pesos normalizados
        weights = {}
        for comp in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
            w_raw = data.get(f"PESO_{comp}")
            weights[comp] = float(w_raw) if (w_raw is not None and w_raw != "") else self.default_weights[f"PESO_{comp}"]
        
        sum_w = sum(weights.values()) or 100.0
        for comp in weights:
            f[f"PESO_{comp}"] = (weights[comp] / sum_w) * 100.0

        # 3. Lectura de notas y estados
        evals = {}
        for comp in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
            nota = data.get(comp)
            estado = data.get(f"ESTADO_{comp}", "REGULAR")
            
            if nota is None or str(nota).strip() == "" or (isinstance(nota, float) and np.isnan(nota)):
                evals[comp] = None
                f[f"{comp}_VAL"] = 0.0
                f[f"{comp}_SIN_DATO"] = 1
                f[f"{comp}_AUSENTE"] = 1 if estado == "AUSENTE" else 0
            else:
                evals[comp] = float(nota)
                f[f"{comp}_VAL"] = float(nota)
                f[f"{comp}_SIN_DATO"] = 0
                f[f"{comp}_AUSENTE"] = 0

        # 4. Detección automática del Checkpoint
        # CP3: si están presentes notas de Fase 3
        # CP2: si están presentes notas de Fase 2
        # CP1: si están presentes notas de Fase 1
        # CP0: solo historial
        has_f1 = (evals["EC1"] is not None) or (evals["EP1"] is not None)
        has_f2 = (evals["EC2"] is not None) or (evals["EP2"] is not None)
        has_f3 = (evals["EC3"] is not None) or (evals["EP3"] is not None)

        if has_f3 and has_f2 and has_f1:
            checkpoint = "CP3"
        elif has_f2 and has_f1:
            checkpoint = "CP2"
        elif has_f1:
            checkpoint = "CP1"
        else:
            checkpoint = "CP0"

        # 5. Cálculo intra-semestral de Fase 1
        f["PESO_F1"] = f["PESO_EC1"] + f["PESO_EP1"]
        f["PUNTOS_F1"] = (f["EC1_VAL"] * f["PESO_EC1"] + f["EP1_VAL"] * f["PESO_EP1"]) / 100.0
        f["PROM_F1"] = (f["PUNTOS_F1"] * 100.0) / (f["PESO_F1"] or 1.0)
        f["PESO_PEND_F1"] = 100.0 - f["PESO_F1"]
        f["PUNTOS_FALT_F1"] = max(0.0, 11.0 - f["PUNTOS_F1"])
        f["NOTA_MIN_PEND_F1"] = (f["PUNTOS_FALT_F1"] * 100.0) / (f["PESO_PEND_F1"] or 1.0)
        f["IMPOSIBLE_APROBAR_F1"] = 1 if f["NOTA_MIN_PEND_F1"] > 20.0 else 0
        f["FALTANTES_F1"] = f["EC1_SIN_DATO"] + f["EP1_SIN_DATO"]

        # 6. Cálculo intra-semestral de Fase 2
        f["PESO_F2"] = f["PESO_EC2"] + f["PESO_EP2"]
        f["PUNTOS_F2"] = (f["EC2_VAL"] * f["PESO_EC2"] + f["EP2_VAL"] * f["PESO_EP2"]) / 100.0
        f["PROM_F2"] = (f["PUNTOS_F2"] * 100.0) / (f["PESO_F2"] or 1.0)
        f["PESO_F1_F2"] = f["PESO_F1"] + f["PESO_F2"]
        f["PUNTOS_F1_F2"] = f["PUNTOS_F1"] + f["PUNTOS_F2"]
        f["PROM_F1_F2"] = (f["PUNTOS_F1_F2"] * 100.0) / (f["PESO_F1_F2"] or 1.0)
        f["PESO_PEND_F2"] = max(1.0, 100.0 - f["PESO_F1_F2"])
        f["PUNTOS_FALT_F2"] = max(0.0, 11.0 - f["PUNTOS_F1_F2"])
        f["NOTA_MIN_PEND_F2"] = (f["PUNTOS_FALT_F2"] * 100.0) / f["PESO_PEND_F2"]
        f["IMPOSIBLE_APROBAR_F2"] = 1 if f["NOTA_MIN_PEND_F2"] > 20.0 else 0
        f["TENDENCIA_F2_VS_F1"] = f["PROM_F2"] - f["PROM_F1"]
        f["FALTANTES_F1_F2"] = f["FALTANTES_F1"] + f["EC2_SIN_DATO"] + f["EP2_SIN_DATO"]

        # 7. Cálculo intra-semestral de Fase 3
        f["PESO_F3"] = f["PESO_EC3"] + f["PESO_EP3"]
        f["PUNTOS_F3"] = (f["EC3_VAL"] * f["PESO_EC3"] + f["EP3_VAL"] * f["PESO_EP3"]) / 100.0
        f["PUNTOS_TOTAL"] = f["PUNTOS_F1_F2"] + f["PUNTOS_F3"]
        f["PROM_TOTAL"] = f["PUNTOS_TOTAL"]
        f["YA_APROBADO_CP3"] = 1 if f["PUNTOS_TOTAL"] >= 10.5 else 0
        f["TENDENCIA_F3_VS_F2"] = ((f["PUNTOS_F3"] * 100.0) / (f["PESO_F3"] or 1.0)) - f["PROM_F2"]
        f["FALTANTES_TOTAL"] = f["FALTANTES_F1_F2"] + f["EC3_SIN_DATO"] + f["EP3_SIN_DATO"]

        return f, checkpoint
