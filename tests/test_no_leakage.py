"""
Pruebas de Integridad Metodológica: Ausencia Total de Fuga de Información (No Data Leakage).
Verifica:
1. En Checkpoint 0 (CP0) no interviene ninguna nota ni métrica del semestre en curso.
2. En Checkpoint 1 (CP1) solo intervienen notas de Fase 1 (EC1, EP1) y stacking PROBA_CP0.
3. En Checkpoint 2 (CP2) intervienen notas de Fase 1 y 2, pero NUNCA de Fase 3.
4. En Checkpoint 3 (CP3) intervienen todas las fases.
5. El número de características requeridas por cada Random Forest coincide exactamente con la especificación.
"""
from src.agents.predictor_agent import (
    CP0_FEATURES,
    CP1_FEATURES,
    CP2_FEATURES,
    CP3_FEATURES,
)


class TestNoDataLeakage:
    """Verificación formal de no fuga de información intra-semestral."""

    def test_cp0_contains_zero_in_semester_grades(self):
        """CP0 debe contener exclusivamente variables históricas y basales previas al semestre."""
        in_semester_keywords = ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3", "F1", "F2", "F3", "TOTAL", "APROBADO"]
        for feat in CP0_FEATURES:
            for kw in in_semester_keywords:
                assert kw not in feat, f"Fuga detectada en CP0: variable '{feat}' contiene referencia a '{kw}'."
        assert len(CP0_FEATURES) == 15, f"CP0 debe tener exactamente 15 características basales, obtenido: {len(CP0_FEATURES)}"

    def test_cp1_contains_only_phase1_and_no_future_phases(self):
        """CP1 puede usar Fase 1 pero NINGUNA variable de Fase 2 ni Fase 3."""
        future_keywords = ["EC2", "EP2", "EC3", "EP3", "F2", "F3", "TOTAL"]
        for feat in CP1_FEATURES:
            for kw in future_keywords:
                assert kw not in feat, f"Fuga futura detectada en CP1: variable '{feat}' contiene referencia a '{kw}'."
        assert len(CP1_FEATURES) == 25, f"CP1 debe tener exactamente 25 características, obtenido: {len(CP1_FEATURES)}"

    def test_cp2_contains_phases_1_and_2_and_no_phase_3(self):
        """CP2 puede usar Fase 1 y Fase 2 pero NINGUNA variable de Fase 3 ni cierre."""
        future_keywords = ["EC3", "EP3", "F3", "TOTAL", "YA_APROBADO_CP3"]
        for feat in CP2_FEATURES:
            for kw in future_keywords:
                assert kw not in feat, f"Fuga futura detectada en CP2: variable '{feat}' contiene referencia a '{kw}'."
        assert len(CP2_FEATURES) == 37, f"CP2 debe tener exactamente 37 características, obtenido: {len(CP2_FEATURES)}"

    def test_cp3_all_phases_present(self):
        """CP3 integra las 3 fases completadas."""
        assert len(CP3_FEATURES) == 46, f"CP3 debe tener exactamente 46 características, obtenido: {len(CP3_FEATURES)}"

    def test_serialized_models_feature_dimension_matches_rule(self, coordinator):
        """Verifica que los archivos .joblib reales cargados coinciden en número de features de entrada."""
        models = coordinator.predictor.models
        assert models["CP0"].n_features_in_ == len(CP0_FEATURES) == 15
        assert models["CP1"].n_features_in_ == len(CP1_FEATURES) == 25
        assert models["CP2"].n_features_in_ == len(CP2_FEATURES) == 37
        assert models["CP3"].n_features_in_ == len(CP3_FEATURES) == 46
