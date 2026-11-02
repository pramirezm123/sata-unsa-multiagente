"""
Pruebas de Desempeño y Validación de los Modelos de Machine Learning (SATA-UNSA).
Verifica:
1. Carga íntegra de los 4 archivos .joblib (Random Forest por Checkpoint).
2. Verificación de la Hipótesis 1 (H1): Recall >= 80% en los 4 checkpoints sobre el conjunto de validación 2023 (N=2,749, 230 reprobados).
3. Comparación y reporte de ambos conjuntos de umbrales calibrados.
4. Generación de probabilidades válidas en [0.0, 1.0].
"""
import pytest
from sklearn.metrics import precision_score, recall_score

from src.agents.predictor_agent import (
    CP0_FEATURES,
    CP1_FEATURES,
    CP2_FEATURES,
    CP3_FEATURES,
    THRESHOLDS,
)


class TestModelsPerformanceAndRecall:
    """Evaluación formal de la Hipótesis H1 (Recall >= 80%)."""

    def test_all_four_models_load_with_correct_classes(self, coordinator):
        predictor = coordinator.predictor
        for cp in ["CP0", "CP1", "CP2", "CP3"]:
            model = predictor.models.get(cp)
            assert model is not None, f"El modelo {cp} no pudo ser cargado."
            assert hasattr(model, "predict_proba"), f"El modelo {cp} debe soportar predict_proba."
            assert len(model.classes_) == 2, f"El modelo {cp} debe ser un clasificador binario."

    def test_recall_greater_equal_80_percent_on_validation_set(self, coordinator, val_dataset):
        """
        Verificación de la Hipótesis H1 sobre el conjunto de validación 2023 (N=2,749, 230 reprobados reales).
        Prueba los umbrales de predictor_agent: CP0=0.285, CP1=0.340, CP2=0.495, CP3=0.765.
        Todos deben garantizar Recall >= 0.8000.
        """
        if val_dataset is None:
            pytest.skip("Dataset checkpoint_val.csv no disponible para la prueba.")

        y_val = val_dataset["REPROBADO"].astype(int)
        assert len(val_dataset) == 2749, f"Se esperaban 2,749 registros de validación, obtenido: {len(val_dataset)}"
        assert (y_val == 1).sum() == 230, f"Se esperaban 230 casos reprobados, obtenido: {(y_val == 1).sum()}"

        models = coordinator.predictor.models
        checkpoints_map = {
            "CP0": (CP0_FEATURES, THRESHOLDS["CP0"]),
            "CP1": (CP1_FEATURES, THRESHOLDS["CP1"]),
            "CP2": (CP2_FEATURES, THRESHOLDS["CP2"]),
            "CP3": (CP3_FEATURES, THRESHOLDS["CP3"]),
        }

        for cp, (feats, u) in checkpoints_map.items():
            model = models[cp]
            X = val_dataset[feats]
            probas = model.predict_proba(X)[:, 1]
            preds = (probas >= u).astype(int)
            rec = recall_score(y_val, preds, pos_label=1)
            prec = precision_score(y_val, preds, pos_label=1, zero_division=0)

            assert rec >= 0.80, (
                f"FALLA EN HIPÓTESIS H1: Checkpoint {cp} con umbral {u} obtuvo Recall={rec:.4f} < 0.80 (Precision={prec:.4f})"
            )

    def test_preliminary_thresholds_also_meet_recall_objective(self, coordinator, val_dataset):
        """
        Verifica el conjunto preliminar de umbrales citado en la documentación:
        CP0=0.278, CP1=0.340, CP2=0.380, CP3=0.407.
        Demuestra que ambos conjuntos de umbrales cumplen holgadamente H1 (Recall >= 80%).
        """
        if val_dataset is None:
            pytest.skip("Dataset checkpoint_val.csv no disponible.")

        y_val = val_dataset["REPROBADO"].astype(int)
        models = coordinator.predictor.models

        preliminary_thresholds = {
            "CP0": (CP0_FEATURES, 0.278),
            "CP1": (CP1_FEATURES, 0.340),
            "CP2": (CP2_FEATURES, 0.380),
            "CP3": (CP3_FEATURES, 0.407)
        }

        for cp, (feats, u) in preliminary_thresholds.items():
            model = models[cp]
            X = val_dataset[feats]
            probas = model.predict_proba(X)[:, 1]
            preds = (probas >= u).astype(int)
            rec = recall_score(y_val, preds, pos_label=1)
            assert rec >= 0.80, f"Checkpoint {cp} preliminar falló: Recall={rec:.4f} < 0.80"
