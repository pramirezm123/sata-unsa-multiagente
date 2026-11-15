"""
Suite de pruebas de regresión y verificación para los 5 Defectos Críticos corregidos en Fase 2:
1. Problema Crítico 1: Autorización del rol ADMIN (sin crash ni acceso a datos individuales).
2. Problema Crítico 2: Esquema homogéneo y telemetría real en Monitor Técnico OBJ5.
3. Problema Crítico 3: Explicabilidad SHAP con impacto real, signo, color y magnitud proporcional.
4. Problema Crítico 4: Persistencia transaccional en SQLite de Carga Masiva de Actas e idempotencia.
5. Problema Crítico 5: Privacidad estricta del rol AUTORIDAD (exclusivamente métricas agregadas).
"""
import json
import pandas as pd
import pytest

from src.agents.xai_agent import format_shap_factor_for_ui
from src.database.db import (
    get_connection,
    get_course_risk_summary,
    get_course_sections_summary,
    get_course_students_table,
    get_grades_for_enrollment,
    get_latest_prediction,
    get_student_enrollments,
    get_student_profile,
    get_technical_metrics_summary,
    persist_acta_row_transactional,
)
from src.security.access_control import (
    AuthorizationError,
    can_access_view,
    validate_student_access,
)
from src.security.crypto import ensure_cui_hash, hash_cui
from src.services.academic_service import validar_y_procesar_acta_masiva


class TestProblemaCritico1AdminAuthorization:
    """Verificación del control de acceso estricto para el rol ADMIN."""

    def test_admin_blocked_from_individual_student_records(self):
        admin_user = {"id": 1, "username": "admin", "role": "ADMIN", "cui_hash": None}

        with pytest.raises(AuthorizationError):
            get_course_students_table("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=admin_user)

        with pytest.raises(AuthorizationError):
            get_student_profile(hash_cui("20220638"), "2026-B", current_user=admin_user)

        with pytest.raises(AuthorizationError):
            get_student_enrollments(hash_cui("20220638"), "2026-B", current_user=admin_user)

        with pytest.raises(AuthorizationError):
            get_grades_for_enrollment(1, current_user=admin_user)

        with pytest.raises(AuthorizationError):
            get_latest_prediction(1, current_user=admin_user)

    def test_admin_authorized_views_and_restrictions(self):
        assert can_access_view("ADMIN", "Monitor Técnico OBJ5") is True
        assert can_access_view("ADMIN", "Panel de seguimiento") is True
        assert can_access_view("ADMIN", "Trazabilidad multiagente") is True
        assert can_access_view("ADMIN", "Encuestas SUS / TAM") is True
        assert can_access_view("ADMIN", "Detalle con explicabilidad") is False
        assert can_access_view("ADMIN", "Seguimiento y plan de tutoría") is False

    def test_docente_retains_authorized_access_to_students_table(self):
        docente_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        rows = get_course_students_table("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=docente_user)
        assert isinstance(rows, list)
        assert len(rows) >= 1


class TestProblemaCritico2MonitorTecnicoOBJ5:
    """Verificación del esquema homogéneo y telemetría real para Monitor Técnico OBJ5."""

    REQUIRED_KEYS = {
        "total_muestras",
        "latencia_inf_media_ms",
        "latencia_inf_p95_ms",
        "latencia_xai_media_ms",
        "latencia_total_media_ms",
        "ram_media_mb",
        "overhead_media_ms",
    }

    def test_summary_schema_when_table_is_empty(self):
        conn = get_connection()
        conn.execute("DELETE FROM metricas_tecnicas")
        conn.commit()
        conn.close()

        summary_empty = get_technical_metrics_summary()
        assert self.REQUIRED_KEYS.issubset(summary_empty.keys())
        assert summary_empty["total_muestras"] == 0
        assert summary_empty["latencia_inf_media_ms"] == 0.0
        assert summary_empty["latencia_inf_p95_ms"] == 0.0
        assert summary_empty["ram_media_mb"] == 0.0
        assert summary_empty["overhead_media_ms"] == 0.0

    def test_real_telemetry_persisted_on_coordinator_inference(self, coordinator, sample_payload_cp1):
        conn = get_connection()
        conn.execute("DELETE FROM metricas_tecnicas")
        conn.commit()
        conn.close()

        res = coordinator.analyze_student_risk(sample_payload_cp1, persist_telemetry=True)
        assert res["status"] == "SUCCESS"
        assert "telemetry" in res
        tel = res["telemetry"]
        assert tel["latencia_inferencia_ms"] > 0.0
        assert tel["latencia_xai_ms"] > 0.0
        assert tel["latencia_total_ms"] >= tel["latencia_inferencia_ms"]
        assert tel["ram_mb"] > 0.0
        assert tel["overhead_bus_ms"] >= 0.0

        summary = get_technical_metrics_summary()
        assert self.REQUIRED_KEYS.issubset(summary.keys())
        assert summary["total_muestras"] == 1
        assert summary["latencia_inf_media_ms"] > 0.0
        assert summary["latencia_inf_p95_ms"] > 0.0
        assert summary["ram_media_mb"] > 0.0


class TestProblemaCritico3ExplicabilidadSHAP:
    """Verificación del uso de impacto SHAP real, signos, colores y proporciones."""

    def test_positive_and_negative_shap_impacts_formatted_correctly(self):
        demo_factors = [
            {"label": "Evaluación Continua 1", "value": 9.0, "impact": 0.28, "direction": "Riesgo"},
            {"label": "Examen Parcial 1", "value": 8.0, "impact": 0.24, "direction": "Riesgo"},
            {"label": "Índice de Rendimiento Acumulado (IRA)", "value": 11.5, "impact": 0.12, "direction": "Riesgo"},
            {"label": "Carga de cursos matriculados", "value": 6, "impact": -0.05, "direction": "Protección"},
        ]
        max_imp = max(abs(f["impact"]) for f in demo_factors)
        ui_factors = [format_shap_factor_for_ui(f, max_imp) for f in demo_factors]

        # Factor 1: +0.28 -> Granate, 100%, valor observado 9
        assert ui_factors[0]["impact"] == 0.28
        assert ui_factors[0]["impact_text"] == "+0.28"
        assert ui_factors[0]["color_css"] == "var(--granate)"
        assert ui_factors[0]["is_risk"] is True
        assert ui_factors[0]["width_pct"] == 100
        assert ui_factors[0]["observed_value"] == "9"

        # Factor 2: +0.24 -> Granate, 86%
        assert ui_factors[1]["impact_text"] == "+0.24"
        assert ui_factors[1]["color_css"] == "var(--granate)"
        assert ui_factors[1]["width_pct"] == 86

        # Factor 3: +0.12 -> Granate, 43%, valor observado 11.5
        assert ui_factors[2]["impact_text"] == "+0.12"
        assert ui_factors[2]["color_css"] == "var(--granate)"
        assert ui_factors[2]["width_pct"] == 43
        assert ui_factors[2]["observed_value"] == "11.5"

        # Factor 4 (Protector): -0.05 -> Azul, 18%, valor observado 6 (NO +6.00!)
        assert ui_factors[3]["impact"] == -0.05
        assert ui_factors[3]["impact_text"] == "-0.05"
        assert ui_factors[3]["color_css"] == "var(--azul-factor)"
        assert ui_factors[3]["is_risk"] is False
        assert ui_factors[3]["direction"] == "Protección"
        assert ui_factors[3]["width_pct"] == 18
        assert ui_factors[3]["observed_value"] == "6"

        # Proporcionalidad estricta
        assert ui_factors[0]["width_pct"] > ui_factors[1]["width_pct"] > ui_factors[2]["width_pct"] > ui_factors[3]["width_pct"]

    def test_handles_nulls_and_incomplete_structures_safely(self):
        res_none = format_shap_factor_for_ui(None)
        assert res_none["impact"] == 0.0
        assert res_none["width_pct"] == 0

        res_legacy = format_shap_factor_for_ui({"label": "Factor Legacy", "value": -0.15, "direction": "Protector"}, 0.30)
        assert res_legacy["impact"] == -0.15
        assert res_legacy["impact_text"] == "-0.15"
        assert res_legacy["color_css"] == "var(--azul-factor)"
        assert res_legacy["width_pct"] == 50


class TestProblemaCritico4PersistenciaCargaMasiva:
    """Verificación de la persistencia transaccional e idempotencia de Carga Masiva de Actas."""

    def test_bulk_upload_persists_all_entities_and_anonymizes_cui(self, coordinator):
        raw_cui_1 = "20269001"
        raw_cui_2 = "20269002"
        hash_1 = hash_cui(raw_cui_1)
        hash_2 = hash_cui(raw_cui_2)
        curso_test = "SISTEMAS OPERATIVOS"

        df_acta = pd.DataFrame([
            {
                "id_estudiante": raw_cui_1,
                "curso": curso_test,
                "docente": "DOCENTE PRINCIPAL 1",
                "seccion": "A",
                "pond_EC1": 15, "pond_EP1": 15, "pond_EC2": 20, "pond_EP2": 20, "pond_EC3": 15, "pond_EP3": 15,
                "IRA": 11.2, "repeticiones": 1, "creditos_matriculados": 6,
                "EC1": 8.0, "EP1": 7.0, "EC2": "", "EP2": "", "EC3": "", "EP3": "",
            },
            {
                "id_estudiante": raw_cui_2,
                "curso": curso_test,
                "docente": "DOCENTE PRINCIPAL 1",
                "seccion": "A",
                "pond_EC1": 15, "pond_EP1": 15, "pond_EC2": 20, "pond_EP2": 20, "pond_EC3": 15, "pond_EP3": 15,
                "IRA": 15.4, "repeticiones": 0, "creditos_matriculados": 6,
                "EC1": 16.0, "EP1": 15.0, "EC2": "", "EP2": "", "EC3": "", "EP3": "",
            },
            {
                # Fila inválida (nota fuera de rango) que debe rechazarse sin impedir las demás
                "id_estudiante": "20269003",
                "curso": curso_test,
                "docente": "DOCENTE PRINCIPAL 1",
                "seccion": "A",
                "EC1": 28.0, "EP1": 12.0,
            },
        ])

        proc, err = validar_y_procesar_acta_masiva(df_acta, coordinator, semestre="2026-B", persist=True)
        assert len(proc) == 2
        assert len(err) == 1

        # Verificar que la tabla de resultados NO contiene CUI en texto claro
        ids_retornados = {r["id_estudiante"] for r in proc}
        assert ids_retornados == {hash_1, hash_2}
        assert raw_cui_1 not in str(proc)
        assert raw_cui_2 not in str(proc)

        # Verificar persistencia real en SQLite en todas las tablas
        conn = get_connection()
        est_rows = conn.execute(
            "SELECT cui_hash FROM estudiantes WHERE cui_hash IN (?, ?)", (hash_1, hash_2)
        ).fetchall()
        assert len(est_rows) == 2

        mat_rows = conn.execute(
            "SELECT id, cui_hash FROM matriculas WHERE curso = ? AND cui_hash IN (?, ?)",
            (curso_test, hash_1, hash_2),
        ).fetchall()
        assert len(mat_rows) == 2
        mat_ids = [r["id"] for r in mat_rows]

        notas_rows = conn.execute(
            f"SELECT * FROM notas WHERE matricula_id IN ({','.join('?' for _ in mat_ids)})",
            mat_ids,
        ).fetchall()
        assert len(notas_rows) == 4  # EC1 y EP1 para cada uno de los 2 estudiantes

        pred_rows = conn.execute(
            f"SELECT id, semaforo FROM predicciones WHERE matricula_id IN ({','.join('?' for _ in mat_ids)})",
            mat_ids,
        ).fetchall()
        assert len(pred_rows) == 2
        pred_ids = [r["id"] for r in pred_rows]

        exp_rows = conn.execute(
            f"SELECT * FROM explicaciones WHERE prediccion_id IN ({','.join('?' for _ in pred_ids)})",
            pred_ids,
        ).fetchall()
        assert len(exp_rows) == 2

        bus_rows = conn.execute(
            "SELECT * FROM mensajes_bus WHERE request_id LIKE ?", (f"%{hash_1}%",)
        ).fetchall()
        assert len(bus_rows) >= 6
        assert raw_cui_1 not in json.dumps([dict(b) for b in bus_rows])

        tec_rows = conn.execute(
            "SELECT * FROM metricas_tecnicas WHERE request_id LIKE ?", (f"%{hash_1}%",)
        ).fetchall()
        assert len(tec_rows) == 1

        # Verificar que reimportar el mismo archivo NO duplica matrículas, notas ni predicciones
        proc2, err2 = validar_y_procesar_acta_masiva(df_acta, coordinator, semestre="2026-B", persist=True)
        assert len(proc2) == 2
        assert len(err2) == 1

        mat_rows_after = conn.execute(
            "SELECT id FROM matriculas WHERE curso = ? AND cui_hash IN (?, ?)",
            (curso_test, hash_1, hash_2),
        ).fetchall()
        pred_rows_after = conn.execute(
            f"SELECT id FROM predicciones WHERE matricula_id IN ({','.join('?' for _ in mat_ids)})",
            mat_ids,
        ).fetchall()
        conn.close()

        assert len(mat_rows_after) == 2, "Reimportar la misma acta no debe duplicar matrículas."
        assert len(pred_rows_after) == 2, "Reimportar la misma acta no debe duplicar predicciones del mismo checkpoint."

        # Verificar que el Panel de seguimiento refleja los nuevos resultados
        resumen = get_course_risk_summary(curso_test, "2026-B")
        assert resumen["total_alumnos"] == 2

    def test_transactional_rollback_leaves_no_partial_records_on_failure(self):
        cui_fail = hash_cui("20269999")
        conn = get_connection()
        before_est = conn.execute("SELECT COUNT(*) FROM estudiantes WHERE cui_hash = ?", (cui_fail,)).fetchone()[0]
        conn.close()
        assert before_est == 0

        # Forzar fallo pasando sma_result con probabilidad inválida no convertible a float dentro de la transacción
        # o provocando un error de tipo al insertar en metricas_tecnicas/notas
        with pytest.raises(Exception):
            persist_acta_row_transactional(
                raw_student_id="20269999",
                semestre="2026-B",
                curso="CURSO_ROLLBACK",
                docente="DOCENTE_X",
                seccion="A",
                pesos={"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15},
                ira=12.0,
                repeticiones=0,
                creditos_matriculados=6,
                eval_vals={"EC1": 12.0, "EP1": None, "EC2": None, "EP2": None, "EC3": None, "EP3": None},
                eval_ausentes={},
                sma_result={
                    "alert": {"checkpoint": "CP1", "probability_pct": 50.0, "top_factors": [{"unserializable": object()}]},
                    "prediction": {"checkpoint": "CP1", "probability": 0.5, "threshold": 0.34},
                },
                semaforo_color="ROJO",
            )

        conn = get_connection()
        after_est = conn.execute("SELECT COUNT(*) FROM estudiantes WHERE cui_hash = ?", (cui_fail,)).fetchone()[0]
        after_mat = conn.execute("SELECT COUNT(*) FROM matriculas WHERE cui_hash = ?", (cui_fail,)).fetchone()[0]
        conn.close()
        assert after_est == 0, "El rollback transaccional debe evitar registros parciales en estudiantes."
        assert after_mat == 0, "El rollback transaccional debe evitar registros parciales en matriculas."


class TestProblemaCritico5PrivacidadAutoridad:
    """Verificación del aislamiento de privacidad para el rol AUTORIDAD."""

    def test_autoridad_blocked_from_individual_student_queries(self):
        autoridad_user = {"id": 3, "username": "tutor_epis", "role": "AUTORIDAD", "cui_hash": None}

        with pytest.raises(AuthorizationError):
            get_course_students_table("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=autoridad_user)

        with pytest.raises(AuthorizationError):
            validate_student_access(autoridad_user, hash_cui("20220638"))

        with pytest.raises(AuthorizationError):
            get_student_profile(hash_cui("20220638"), "2026-B", current_user=autoridad_user)

        with pytest.raises(AuthorizationError):
            get_student_enrollments(hash_cui("20220638"), "2026-B", current_user=autoridad_user)

        with pytest.raises(AuthorizationError):
            get_grades_for_enrollment(1, current_user=autoridad_user)

        with pytest.raises(AuthorizationError):
            get_latest_prediction(1, current_user=autoridad_user)

    def test_autoridad_sections_summary_contains_only_aggregates(self):
        sections = get_course_sections_summary("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B")
        assert len(sections) >= 1
        for sec in sections:
            assert "cui_hash" not in sec
            assert "id_estudiante" not in sec
            assert "id_mostrado" not in sec
            assert "seccion" in sec
            assert "docente" in sec
            assert "total_alumnos" in sec
            assert "rojos" in sec
            assert "amarillos" in sec
            assert "verdes" in sec
            assert "tasa_riesgo_pct" in sec
