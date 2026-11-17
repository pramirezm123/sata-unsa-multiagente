"""
Suite de pruebas unitarias y de integración para la Fase 6:
Corrección selectiva de hallazgos de la Auditoría Final de Aceptación (SATA-UNSA).

Cubre:
1. Prioridad 1 (F5-02): Control de acceso estricto de DOCENTE (propio curso, curso ajeno,
   matrícula ajena, docente sin asignaciones, preservación de permisos ADMIN y AUTORIDAD).
2. Prioridad 2 (F5-01): Regla académica unificada de aprobación por redondeo (>= 10.50 aprueba,
   10.49 reprueba, viabilidad/imposibilidad matemática hacia 10.50 con alerta roja, y
   sustitutorio reemplazando exclusivamente min(EP1, EP2, EP3) sin tocar EC1..EC3).
3. Prioridad 3 (F5-05): Idempotencia de init_database(), seed_initial_data(), recargas de
   módulo y save_student_profile() sobre una base SQLite temporal aislada.
4. Prioridad 4 (F5-04): Eliminación de la constante ficticia fidelidad_r=0.96, persistencia
   de None cuando no se calcula fidelidad local en tiempo real y distinción frente al
   experimento global offline SHAP-LIME (0.7778).
"""
import importlib
import os
import pandas as pd
import pytest

import src.database.db as db_mod
from src.agents.alert_agent import AlertAgent
from src.agents.preprocessing_agent import PreprocessingAgent
from src.agents.xai_agent import (
    get_offline_shap_lime_benchmark,
    normalize_local_fidelity,
)
from src.database.db import (
    enroll_course,
    evaluate_and_persist_enrollment,
    get_connection,
    get_course_risk_summary,
    get_course_sections_summary,
    get_course_students_table,
    get_courses_for_user,
    get_enrollment_by_id,
    get_grades_for_enrollment,
    get_latest_prediction,
    get_recent_bus_messages,
    get_student_profile,
    get_technical_metrics_summary,
    get_tutoring_history,
    init_database,
    persist_acta_row_transactional,
    register_tutoring_session,
    save_grade,
    save_prediction_result,
    save_student_profile,
    schedule_tutoring_session,
    seed_initial_data,
)
from src.security.access_control import (
    AuthorizationError,
    can_access_view,
    validate_course_teacher_access,
    validate_matricula_ownership,
)
from src.security.crypto import hash_cui
from src.services.academic_service import (
    UMBRAL_APROBACION_NORMATIVO,
    calcular_simulacion_sustitutorio,
    evaluar_condicion_academica_normativa,
    validar_y_procesar_acta_masiva,
)


class TestPrioridad1F502ControlAccesoDocente:
    """Verificación integral del aislamiento horizontal entre docentes y permisos por rol."""

    def test_docente_accesses_own_course_and_students(self, coordinator):
        docente_titular = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        cursos_asignados = get_courses_for_user(docente_titular, "2026-B")
        nombres_cursos = [c["nombre"] for c in cursos_asignados]
        assert "ESTRUCTURAS DE DATOS Y ALGORITMOS" in nombres_cursos

        alumnos = get_course_students_table(
            "ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=docente_titular
        )
        assert len(alumnos) >= 1
        mat_id = alumnos[0]["matricula_id"]

        mat_info = get_enrollment_by_id(mat_id, current_user=docente_titular)
        assert mat_info is not None
        assert mat_info["docente"] == "DOCENTE PRINCIPAL 1"

        notas = get_grades_for_enrollment(mat_id, current_user=docente_titular)
        assert isinstance(notas, dict)

    def test_docente_denied_access_to_other_teacher_course_and_enrollment(self, coordinator):
        # Crear curso y matrícula asignados exclusivamente a 'DOCENTE ASOCIADO 2'
        cui_otro = hash_cui("20268881")
        curso_ajeno = "SEGURIDAD INFORMATICA"
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}

        conn = get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro) VALUES (?, 1, 1, '2026-01-01')",
            (cui_otro,),
        )
        conn.commit()
        conn.close()

        docente_2 = {"id": 22, "username": "DOCENTE ASOCIADO 2", "role": "DOCENTE", "cui_hash": None}
        docente_1 = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}

        mat_ajena = enroll_course(cui_otro, "2026-B", curso_ajeno, "DOCENTE ASOCIADO 2", "A", pesos, 0)
        save_grade(mat_ajena, "EC1", 11.0, False, current_user=docente_2)
        save_grade(mat_ajena, "EP1", 10.0, False, current_user=docente_2)
        evaluate_and_persist_enrollment(mat_ajena, coordinator, current_user=docente_2)

        # DOCENTE 2 sí puede ver su propio curso y su matrícula
        alumnos_doc2 = get_course_students_table(curso_ajeno, "2026-B", current_user=docente_2)
        assert len(alumnos_doc2) == 1
        assert alumnos_doc2[0]["matricula_id"] == mat_ajena

        # DOCENTE 1 ('docente_demo' / 'DOCENTE PRINCIPAL 1') NO puede acceder al curso de DOCENTE 2
        with pytest.raises(AuthorizationError):
            get_course_students_table(curso_ajeno, "2026-B", current_user=docente_1)

        # DOCENTE 1 NO puede consultar ni modificar la matrícula ajena en ningún punto de entrada
        with pytest.raises(AuthorizationError):
            get_enrollment_by_id(mat_ajena, current_user=docente_1)
        with pytest.raises(AuthorizationError):
            get_grades_for_enrollment(mat_ajena, current_user=docente_1)
        with pytest.raises(AuthorizationError):
            get_latest_prediction(mat_ajena, current_user=docente_1)
        with pytest.raises(AuthorizationError):
            save_grade(mat_ajena, "EC1", 18.0, False, current_user=docente_1)
        with pytest.raises(AuthorizationError):
            schedule_tutoring_session(mat_ajena, "2026-11-25", "Intento sobre matrícula ajena", current_user=docente_1)
        with pytest.raises(AuthorizationError):
            register_tutoring_session(
                mat_ajena, "2026-11-25", "REALIZADA", "Intento sobre matrícula ajena",
                True, False, False, current_user=docente_1
            )
        with pytest.raises(AuthorizationError):
            get_tutoring_history(mat_ajena, current_user=docente_1)

        # DOCENTE 1 tampoco puede subir un acta masiva a nombre de DOCENTE ASOCIADO 2
        df_ajena = pd.DataFrame([{
            "ID_ESTUDIANTE": "20268882",
            "CURSO": curso_ajeno,
            "DOCENTE": "DOCENTE ASOCIADO 2",
            "EC1": 12.0,
            "EP1": 12.0,
        }])
        with pytest.raises(AuthorizationError):
            validar_y_procesar_acta_masiva(df_ajena, coordinator, current_user=docente_1)

    def test_docente_without_assignments_denied_by_default(self):
        docente_sin_cursos = {
            "id": 99,
            "username": "docente_sin_asignacion",
            "role": "DOCENTE",
            "cui_hash": None,
        }
        assert get_courses_for_user(docente_sin_cursos, "2026-B") == []

        with pytest.raises(AuthorizationError):
            get_course_students_table(
                "ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=docente_sin_cursos
            )
        with pytest.raises(AuthorizationError):
            get_course_students_table(
                "TEORIA DE LA COMPUTACION", "2026-B", current_user=docente_sin_cursos
            )
        with pytest.raises(AuthorizationError):
            get_enrollment_by_id(1, current_user=docente_sin_cursos)

    def test_admin_and_autoridad_preserve_legitimate_permissions_and_restrictions(self):
        admin_user = {"id": 1, "username": "admin", "role": "ADMIN", "cui_hash": None}
        autoridad_user = {"id": 3, "username": "tutor_epis", "role": "AUTORIDAD", "cui_hash": None}

        # ADMIN mantiene acceso a telemetría técnica y bus FIPA-ACL
        tech_summary = get_technical_metrics_summary()
        assert "total_muestras" in tech_summary
        bus_msgs = get_recent_bus_messages(limit=5)
        assert isinstance(bus_msgs, list)
        assert can_access_view("ADMIN", "Monitor Técnico OBJ5") is True

        # AUTORIDAD mantiene acceso a resúmenes agregados por asignatura y sección
        risk_sum = get_course_risk_summary("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B")
        sec_sum = get_course_sections_summary("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B")
        assert risk_sum["total_alumnos"] >= 1
        assert len(sec_sum) >= 1
        assert "cui_hash" not in sec_sum[0]

        # Ambos continúan bloqueados frente a nóminas y matrículas individuales
        for restricted_user in (admin_user, autoridad_user):
            with pytest.raises(AuthorizationError):
                get_course_students_table(
                    "ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=restricted_user
                )
            with pytest.raises(AuthorizationError):
                get_enrollment_by_id(1, current_user=restricted_user)


class TestPrioridad2F501UmbralAcademicoNormativo:
    """Verificación de la regla académica única de aprobación (>= 10.50) y sustitutorio."""

    PESOS = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}

    def test_final_rounded_grade_10_49_fails_and_triggers_red_alert(self, fresh_bus):
        # Promedio exacto 10.49 -> redondea a entero 10 (DESAPROBADO)
        cond = evaluar_condicion_academica_normativa(
            10.49, 10.49, 10.49, 10.49, 10.49, 10.49, self.PESOS, probabilidad_riesgo=0.20
        )
        assert cond["umbral_aprobacion_normativo"] == UMBRAL_APROBACION_NORMATIVO == 10.50
        assert cond["puntos_acumulados"] == 10.49
        assert cond["nota_entera_acta"] == 10
        assert cond["aprobado"] is False
        assert cond["imposible_aprobar_ordinario"] is True
        assert cond["alerta_roja"] is True
        assert cond["semaforo"] == "ROJO"
        assert cond["sustitutorio"]["aplica"] is True
        assert cond["sustitutorio"]["ya_aprobo"] is False

        # Verificar coherencia en PreprocessingAgent y AlertAgent para CP3 con 10.49
        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        alert_ag = AlertAgent("AlertAgent", fresh_bus)
        feats, cp = prep._compute_features({
            "EC1": 10.49, "EP1": 10.49, "EC2": 10.49, "EP2": 10.49, "EC3": 10.49, "EP3": 10.49
        })
        assert cp == "CP3"
        assert feats["YA_APROBADO_CP3"] == 0
        assert feats["IMPOSIBLE_APROBAR_NORM_CP3"] == 1

        pkg = alert_ag.create_alert_package(
            pred={"probability": 0.20, "threshold": 0.765, "checkpoint": "CP3", "is_alert": False},
            prep={"features": feats},
            xai={},
            rec={},
        )
        assert pkg["imposible_ordinario"] is True
        assert pkg["is_alert"] is True
        assert pkg["risk_level"] == "CRÍTICO"

    def test_final_rounded_grade_10_50_passes(self, fresh_bus):
        # Promedio exacto 10.50 -> redondea a entero 11 (APROBADO)
        cond = evaluar_condicion_academica_normativa(
            10.50, 10.50, 10.50, 10.50, 10.50, 10.50, self.PESOS, probabilidad_riesgo=0.10
        )
        assert cond["puntos_acumulados"] == 10.50
        assert cond["nota_entera_acta"] == 11
        assert cond["aprobado"] is True
        assert cond["puntos_faltantes"] == 0.0
        assert cond["imposible_aprobar_ordinario"] is False
        assert cond["sustitutorio"]["aplica"] is False
        assert cond["sustitutorio"]["ya_aprobo"] is True

        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        feats, cp = prep._compute_features({
            "EC1": 10.50, "EP1": 10.50, "EC2": 10.50, "EP2": 10.50, "EC3": 10.50, "EP3": 10.50
        })
        assert cp == "CP3"
        assert feats["YA_APROBADO_CP3"] == 1
        assert feats["IMPOSIBLE_APROBAR_NORM_CP3"] == 0

    def test_scenarios_still_mathematically_possible_to_pass_towards_10_50(self, fresh_bus):
        # En CP2 (70% evaluado, 30% pendiente en Fase 3):
        # Si acumula 4.50 puntos (ej. EC1=10, EP1=10 [3.0 pts] + EC2=3.75, EP2=3.75 [1.5 pts] = 4.50 pts),
        # para llegar a 10.50 le faltan 6.00 puntos en el 30% pendiente => necesita exactamente 20.00 (POSIBLE).
        # Con la regla antigua de 11.0 habría pedido 21.67 (falsamente imposible).
        cond = evaluar_condicion_academica_normativa(
            ec1=10.0, ep1=10.0, ec2=3.75, ep2=3.75, ec3=None, ep3=None, pesos=self.PESOS, probabilidad_riesgo=0.20
        )
        assert cond["checkpoint"] == "CP2"
        assert cond["puntos_acumulados"] == 4.50
        assert cond["puntos_faltantes"] == 6.00
        assert cond["nota_minima_pendiente"] == 20.00
        assert cond["posible_aprobar_ordinario"] is True
        assert cond["imposible_aprobar_ordinario"] is False

        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        alert_ag = AlertAgent("AlertAgent", fresh_bus)
        feats, cp = prep._compute_features({
            "EC1": 10.0, "EP1": 10.0, "EC2": 3.75, "EP2": 3.75
        })
        assert cp == "CP2"
        # La característica interna del modelo se conserva sin alterar el .joblib
        assert round(feats["NOTA_MIN_PEND_F2"], 2) == 21.67
        # La lógica normativa aplica 10.50 -> nota mínima 20.00 (posible)
        assert feats["NOTA_MIN_NORM_PEND_F2"] == 20.00
        assert feats["IMPOSIBLE_APROBAR_NORM_F2"] == 0

        pkg = alert_ag.create_alert_package(
            pred={"probability": 0.20, "threshold": 0.495, "checkpoint": "CP2", "is_alert": False},
            prep={"features": feats},
            xai={},
            rec={},
        )
        assert pkg["imposible_ordinario"] is False
        assert pkg["meta_nota_min"] == 20.00

    def test_scenarios_mathematically_impossible_to_pass_trigger_red_alert(self, fresh_bus):
        # En CP2 con 4.20 puntos acumulados (faltan 6.30 puntos en 30% pendiente => requiere 21.00 > 20.0)
        cond = evaluar_condicion_academica_normativa(
            ec1=8.0, ep1=8.0, ec2=4.5, ep2=4.5, ec3=None, ep3=None, pesos=self.PESOS, probabilidad_riesgo=0.15
        )
        assert cond["checkpoint"] == "CP2"
        assert cond["puntos_acumulados"] == 4.20
        assert cond["nota_minima_pendiente"] == 21.00
        assert cond["imposible_aprobar_ordinario"] is True
        assert cond["alerta_roja"] is True
        assert cond["semaforo"] == "ROJO"

        prep = PreprocessingAgent("PreprocessingAgent", fresh_bus)
        alert_ag = AlertAgent("AlertAgent", fresh_bus)
        feats, _ = prep._compute_features({"EC1": 8.0, "EP1": 8.0, "EC2": 4.5, "EP2": 4.5})
        assert feats["IMPOSIBLE_APROBAR_NORM_F2"] == 1

        pkg = alert_ag.create_alert_package(
            pred={"probability": 0.15, "threshold": 0.495, "checkpoint": "CP2", "is_alert": False},
            prep={"features": feats},
            xai={},
            rec={},
        )
        assert pkg["imposible_ordinario"] is True
        assert pkg["is_alert"] is True
        assert pkg["risk_level"] == "CRÍTICO"
        assert pkg["color"] == "#D32F2F"

    def test_substitutory_replaces_only_lowest_partial_and_never_continuous(self):
        # EC1=0.0, EC2=0.0, EC3=0.0 (continuas muy bajas), EP1=14.0, EP2=10.0, EP3=15.0
        # Debe elegir exclusivamente min(EP1, EP2, EP3) = EP2 (10.0), jamás EC1/EC2/EC3 (0.0)
        sim = calcular_simulacion_sustitutorio(
            ec1=0.0, ep1=14.0, ec2=0.0, ep2=10.0, ec3=0.0, ep3=15.0, pesos=self.PESOS
        )
        assert sim["aplica"] is True
        assert sim["parcial_a_reemplazar"] == "EP2"
        assert sim["nota_reemplazada"] == 10.0
        assert sim["parcial_a_reemplazar"] not in ("EC1", "EC2", "EC3")


class TestPrioridad3F505IdempotenciaSeedInitialData:
    """Verifica idempotencia estricta de inicialización en base SQLite temporal aislada."""

    def test_first_second_and_repeated_module_initializations_create_zero_duplicates(self, tmp_path, monkeypatch):
        isolated_db = str(tmp_path / "sata_idempotency_test.db")
        monkeypatch.setenv("SATA_DB_PATH", isolated_db)
        monkeypatch.setattr(db_mod, "DB_PATH", isolated_db)

        # 1. Primera inicialización
        init_database()
        seed_initial_data()

        conn = get_connection()
        c_perf_1 = conn.execute("SELECT COUNT(*) FROM perfil_semestre").fetchone()[0]
        c_exp_1 = conn.execute("SELECT COUNT(*) FROM explicaciones").fetchone()[0]
        c_mat_1 = conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0]
        c_pred_1 = conn.execute("SELECT COUNT(*) FROM predicciones").fetchone()[0]
        c_bus_1 = conn.execute("SELECT COUNT(*) FROM mensajes_bus").fetchone()[0]
        c_tut_1 = conn.execute("SELECT COUNT(*) FROM tutorias").fetchone()[0]
        conn.close()

        assert c_perf_1 == 1
        assert c_exp_1 == 1
        assert c_mat_1 == 1
        assert c_pred_1 == 1
        assert c_bus_1 == 12
        assert c_tut_1 == 1

        # 2. Segunda inicialización consecutiva
        init_database()
        seed_initial_data()

        conn = get_connection()
        assert conn.execute("SELECT COUNT(*) FROM perfil_semestre").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM explicaciones").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM predicciones").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM mensajes_bus").fetchone()[0] == 12
        assert conn.execute("SELECT COUNT(*) FROM tutorias").fetchone()[0] == 1
        conn.close()

        # 3. Insertar registros legítimos preexistentes de un segundo estudiante
        cui_legit = hash_cui("20190638")
        save_student_profile(cui_legit, "2026-B", 15.2, 0, 5, 6.0)
        # Actualizar el mismo perfil semestral no debe duplicar la fila
        save_student_profile(cui_legit, "2026-B", 15.8, 0, 5, 6.0)

        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        mat_legit = enroll_course(cui_legit, "2026-B", "INTELIGENCIA ARTIFICIAL", "DOCENTE PRINCIPAL 1", "A", pesos, 0)
        pred_legit = save_prediction_result(
            matricula_id=mat_legit,
            checkpoint="CP0",
            proba=0.18,
            umbral=0.285,
            semaforo="VERDE",
            meta_nota=None,
            promedio=15.8,
            imposible=False,
            top_factors=[{"label": "IRA", "value": 15.8, "impact": -0.10, "direction": "Protección"}],
            recs=["Continuar seguimiento regular."],
        )
        assert pred_legit > 1

        # 4. Importaciones / recargas repetidas del módulo db
        importlib.reload(db_mod)
        seed_initial_data()

        conn = get_connection()
        assert conn.execute("SELECT COUNT(*) FROM perfil_semestre").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM explicaciones").fetchone()[0] == 2
        conn.close()

        prof_legit = get_student_profile(cui_legit, "2026-B")
        assert prof_legit["ira_acum"] == 15.8


class TestPrioridad4F504FidelidadXaiCoherente:
    """Verifica que no se persista el valor ficticio 0.96 ni se confunda con el benchmark global offline."""

    def test_normalize_local_fidelity_rejects_fictitious_or_invalid_values(self):
        assert normalize_local_fidelity(None) is None
        assert normalize_local_fidelity(True) is None
        assert normalize_local_fidelity("no_disponible") is None
        assert normalize_local_fidelity(1.5) is None
        assert normalize_local_fidelity(-1.2) is None
        assert normalize_local_fidelity(0.81234) == 0.8123

    def test_runtime_predictions_persist_null_fidelidad_instead_of_fictitious_096(self, coordinator):
        cui_test = hash_cui("20267771")
        conn = get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro) VALUES (?, 1, 1, '2026-01-01')",
            (cui_test,),
        )
        conn.commit()
        conn.close()

        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        doc_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        mat_id = enroll_course(cui_test, "2026-B", "BASE DE DATOS 1", "DOCENTE PRINCIPAL 1", "A", pesos, 0)
        save_grade(mat_id, "EC1", 10.0, False, current_user=doc_user)
        save_grade(mat_id, "EP1", 9.0, False, current_user=doc_user)

        res_sma = evaluate_and_persist_enrollment(mat_id, coordinator, current_user=doc_user)
        assert res_sma["status"] == "SUCCESS"
        assert res_sma["xai"]["fidelidad_r"] is None

        pred_db = get_latest_prediction(mat_id, current_user=doc_user)
        assert pred_db is not None
        assert pred_db["fidelidad_r"] is None, "No debe persistirse la constante ficticia 0.96."

        # Verificar también en carga transaccional de actas
        res_tx = persist_acta_row_transactional(
            raw_student_id="20267772",
            semestre="2026-B",
            curso="BASE DE DATOS 1",
            docente="DOCENTE PRINCIPAL 1",
            seccion="A",
            pesos=pesos,
            ira=12.0,
            repeticiones=0,
            creditos_matriculados=6,
            eval_vals={"EC1": 11.0, "EP1": 11.0, "EC2": None, "EP2": None, "EC3": None, "EP3": None},
            eval_ausentes={},
            sma_result=res_sma,
            semaforo_color="AMARILLO",
        )
        pred_tx = get_latest_prediction(res_tx["matricula_id"], current_user=doc_user)
        assert pred_tx["fidelidad_r"] is None

    def test_offline_global_shap_lime_benchmark_is_distinct_and_accessible(self, models_dir):
        benchmark = get_offline_shap_lime_benchmark(models_dir)
        assert benchmark["available"] is True
        assert benchmark["scope"] == "OFFLINE_GLOBAL_BENCHMARK"
        assert benchmark["checkpoint"] == "CP1"
        assert benchmark["correlacion_pearson"] == 0.7778
        assert benchmark["n_estudiantes"] == 100
