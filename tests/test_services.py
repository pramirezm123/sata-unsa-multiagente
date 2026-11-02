"""
Pruebas exhaustivas de los servicios de soporte:
1. Validador y procesador de cargas masivas CSV (validación fila por fila, errores de encoding, inyección de fórmulas).
2. Generador de reportes PDF de intervención tutorial (fpdf2, anonimización, acentos, ñ y textos largos).
"""
import pandas as pd

from src.reports.pdf_generator import generate_intervention_pdf
from src.services.academic_service import (
    generar_plantilla_carga_masiva_csv,
    validar_y_procesar_acta_masiva,
)


class TestCsvBatchProcessing:
    """Pruebas del validador de actas masivas."""

    def test_missing_required_columns_reported(self, coordinator):
        # Falta columna 'DOCENTE'
        df = pd.DataFrame([{
            "ID_ESTUDIANTE": "EST_001",
            "CURSO": "INTELIGENCIA ARTIFICIAL",
            "EC1": 15.0
        }])
        proc, err = validar_y_procesar_acta_masiva(df, coordinator)
        assert len(proc) == 0
        assert len(err) > 0
        assert "Columnas obligatorias faltantes" in err[0]["error"]

    def test_csv_injection_formula_rejected(self, coordinator):
        """Verifica que celdas maliciosas con =cmd| o @ sum sean rechazadas."""
        df = pd.DataFrame([{
            "ID_ESTUDIANTE": "=cmd|' /C calc'!A0",
            "CURSO": "BASE DE DATOS",
            "DOCENTE": "DOCENTE 1",
            "EC1": 14.0,
            "EP1": 12.0
        }])
        proc, err = validar_y_procesar_acta_masiva(df, coordinator)
        assert len(proc) == 0
        assert any("fórmula CSV" in e["error"] for e in err)

    def test_csv_out_of_range_and_invalid_data_reported_row_by_row(self, coordinator):
        df = pd.DataFrame([
            # Fila 1 válida
            {"ID_ESTUDIANTE": "EST_OK", "CURSO": "CURSO A", "DOCENTE": "DOC 1", "EC1": 14.0, "EP1": 12.0},
            # Fila 2 con nota fuera de rango (25.0)
            {"ID_ESTUDIANTE": "EST_FAIL1", "CURSO": "CURSO A", "DOCENTE": "DOC 1", "EC1": 25.0, "EP1": 12.0},
            # Fila 3 con IRA fuera de rango (35.0)
            {"ID_ESTUDIANTE": "EST_FAIL2", "CURSO": "CURSO A", "DOCENTE": "DOC 1", "IRA": 35.0, "EC1": 12.0, "EP1": 10.0},
            # Fila 4 con ponderaciones que no suman 100%
            {"ID_ESTUDIANTE": "EST_FAIL3", "CURSO": "CURSO A", "DOCENTE": "DOC 1", "POND_EC1": 50, "POND_EP1": 60, "EC1": 12.0, "EP1": 10.0}
        ])
        proc, err = validar_y_procesar_acta_masiva(df, coordinator)
        assert len(proc) == 1, "Solo la fila válida debe procesarse."
        assert len(err) == 3, "Las 3 filas con error deben ser reportadas fila por fila."
        assert proc[0]["id_estudiante"] == "EST_OK"

    def test_template_generation_contains_required_headers(self):
        template = generar_plantilla_carga_masiva_csv()
        assert "id_estudiante" in template
        assert "curso" in template
        assert "docente" in template
        assert "EC1,EP1,EC2,EP2,EC3,EP3" in template.replace(" ", "")


class TestPdfReportGeneration:
    """Pruebas del generador de PDF (fpdf2)."""

    def test_pdf_generates_successfully_with_spanish_accents_and_enye(self):
        """Verifica que el PDF maneje tildes y la letra eñe sin romper."""
        pdf_bytes = generate_intervention_pdf(
            student_id_anon="HASH_9876543210ABCDEF",
            curso="PROGRAMACIÓN DE MÓVILES Y SISTEMAS DISTRIBUIDOS",
            docente="ING. ÁLVARO PEÑA NÚÑEZ",
            checkpoint="CP2",
            probabilidad_pct=82.4,
            umbral_pct=49.5,
            semaforo="ROJO",
            meta_nota_min=16.5,
            promedio_acumulado=7.8,
            imposible=False,
            top_factors=[
                {"label": "Evaluación Continua 2 (Prácticas y Laboratorios)", "value": 5.0, "impact": 0.32, "direction": "Riesgo"},
                {"label": "Antigüedad del estudiante en años académicos", "value": 4.5, "impact": -0.08, "direction": "Protección"}
            ],
            recommendations=[
                "Coordinar sesión de tutoría individualizada y diseñar plan de recuperación.",
                "Programar asesoría técnica para la entrega de tareas en la plataforma institucional."
            ]
        )
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")

    def test_pdf_handles_very_long_text_without_overflow(self):
        """Verifica que textos largos en recomendaciones y factores no rompan el layout."""
        long_recommendation = "Esta es una recomendación pedagógica extraordinariamente extensa y detallada " * 15
        pdf_bytes = generate_intervention_pdf(
            student_id_anon="HASH_LONGTEXT",
            curso="CURSO EXTENSO DE PRUEBA DE LAYOUT",
            docente="DOCENTE PRINCIPAL",
            checkpoint="CP3",
            probabilidad_pct=90.0,
            umbral_pct=76.5,
            semaforo="ROJO",
            meta_nota_min=None,
            promedio_acumulado=9.0,
            imposible=True,
            top_factors=[{"label": "Factor con nombre muy extenso " * 4, "value": 10.0, "impact": 0.5, "direction": "Riesgo"}],
            recommendations=[long_recommendation]
        )
        assert pdf_bytes is not None
        assert pdf_bytes.startswith(b"%PDF-")
