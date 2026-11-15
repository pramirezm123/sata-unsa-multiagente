"""
Suite de pruebas de integración y regresión para la Fase 3 (Defectos de Prioridad Alta):
A. Selectores reales de asignatura y estudiante anonimizado para DOCENTE.
B. Integración real del bus FIPA-ACL con persistencia en mensajes_bus y performativas REQUEST, INFORM, PROPOSE y FAILURE.
C. Eliminación de datos ficticios en cabecera común y reportes PDF coherentes con SQLite.
D. Módulo funcional de tutorías, bitácora y checklist persistidos en SQLite con control de acceso y validación.
E. Cuestionario TAM completo y conexión de funciones backend (calcular_simulacion_sustitutorio, save_grade, update_student_consent).
"""
import json
import os
import pytest

from src.database.db import (
    enroll_course,
    evaluate_and_persist_enrollment,
    get_bus_messages_for_student,
    get_connection,
    get_course_students_table,
    get_enrollment_by_id,
    get_grade_change_history,
    get_grades_for_enrollment,
    get_header_metrics,
    get_latest_prediction,
    get_recent_bus_messages,
    get_student_info,
    get_surveys_stats,
    get_tutoring_checklist_state,
    get_tutoring_history,
    register_tutoring_session,
    save_grade,
    save_survey,
    schedule_tutoring_session,
    update_student_consent,
)
from src.reports.pdf_generator import generate_intervention_pdf
from src.security.access_control import AuthorizationError
from src.security.crypto import hash_cui
from src.services.academic_service import calcular_simulacion_sustitutorio

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


class TestGrupoASelectoresDocente:
    """Verifica selectores funcionales para DOCENTE y eliminación de valores hardcodeados."""

    def test_no_hardcoded_student_hash_or_mat_id_in_app_py(self):
        with open(APP_PATH, "r", encoding="utf-8") as f:
            code = f.read()
        assert "7f3a...c91" not in code, "No debe existir el hash hardcodeado '7f3a...c91' en app.py."
        assert "mat_id_act = 1" not in code, "No debe existir 'mat_id_act = 1' hardcodeado en app.py."
        assert "total_est = 18" not in code, "No debe existir 'total_est = 18' hardcodeado en app.py."
        assert "tutorias_sem = 3" not in code, "No debe existir 'tutorias_sem = 3' hardcodeado en app.py."

    def test_docente_course_and_student_selection_respects_opt_in_and_permissions(self, coordinator):
        docente_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        admin_user = {"id": 1, "username": "admin", "role": "ADMIN", "cui_hash": None}
        autoridad_user = {"id": 3, "username": "tutor_epis", "role": "AUTORIDAD", "cui_hash": None}

        cui_raw_optin = "20251111"
        cui_raw_no_optin = "20252222"
        h_optin = hash_cui(cui_raw_optin)
        h_no_optin = hash_cui(cui_raw_no_optin)
        curso_test = "INGENIERIA DE SOFTWARE 1"
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}

        conn = get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro) VALUES (?, 1, 1, '2026-01-01')",
            (h_optin,),
        )
        conn.execute(
            "INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro) VALUES (?, 1, 0, '2026-01-01')",
            (h_no_optin,),
        )
        conn.commit()
        conn.close()

        m1 = enroll_course(h_optin, "2026-B", curso_test, "DOCENTE PRINCIPAL 1", "A", pesos, 0)
        m2 = enroll_course(h_no_optin, "2026-B", curso_test, "DOCENTE PRINCIPAL 1", "B", pesos, 1)

        save_grade(m1, "EC1", 15.0, False, current_user=docente_user)
        save_grade(m1, "EP1", 14.0, False, current_user=docente_user)
        evaluate_and_persist_enrollment(m1, coordinator, current_user=docente_user)

        save_grade(m2, "EC1", 6.0, False, current_user=docente_user)
        save_grade(m2, "EP1", 5.0, False, current_user=docente_user)
        evaluate_and_persist_enrollment(m2, coordinator, current_user=docente_user)

        rows = get_course_students_table(curso_test, "2026-B", current_user=docente_user)
        assert len(rows) == 2

        by_mat = {r["matricula_id"]: r for r in rows}
        assert by_mat[m1]["id_mostrado"] == h_optin
        assert by_mat[m1]["estado_optin"] == "Compartido con tutor"

        assert by_mat[m2]["id_mostrado"] == f"RES-{h_no_optin[:6]}"
        assert by_mat[m2]["estado_optin"] == "No compartido"

        # Verificar que cada matrícula devuelve su propia predicción y metadatos
        mat_info_1 = get_enrollment_by_id(m1, current_user=docente_user)
        pred_1 = get_latest_prediction(m1, current_user=docente_user)
        pred_2 = get_latest_prediction(m2, current_user=docente_user)
        assert mat_info_1["curso"] == curso_test
        assert pred_1["probabilidad"] < pred_2["probabilidad"]

        # ADMIN y AUTORIDAD bloqueados
        with pytest.raises(AuthorizationError):
            get_enrollment_by_id(m1, current_user=admin_user)
        with pytest.raises(AuthorizationError):
            get_enrollment_by_id(m1, current_user=autoridad_user)


class TestGrupoBBusFipaAclReal:
    """Verifica el registro y lectura real de mensajes FIPA-ACL con performativas REQUEST, INFORM, PROPOSE y FAILURE."""

    def test_real_fipa_acl_performatives_persisted_in_sqlite(self, coordinator, sample_payload_cp1):
        raw_cui = "20253333"
        h_cui = hash_cui(raw_cui)
        payload_ok = dict(sample_payload_cp1)
        payload_ok["CUI"] = raw_cui

        res = coordinator.analyze_student_risk(payload_ok, persist_telemetry=True)
        assert res["status"] == "SUCCESS"

        msgs_student = get_bus_messages_for_student(h_cui, limit=20)
        assert len(msgs_student) >= 12
        performatives = {m["performativa"] for m in msgs_student}
        assert "REQUEST" in performatives
        assert "INFORM" in performatives
        assert "PROPOSE" in performatives

        # Verificar cero CUI en texto claro en mensajes persistidos
        serialized = json.dumps(msgs_student)
        assert raw_cui not in serialized
        assert h_cui in serialized

    def test_fipa_acl_failure_performative_persisted_on_invalid_payload(self, coordinator):
        raw_cui = "20254444"
        h_cui = hash_cui(raw_cui)
        bad_payload = {"CUI": raw_cui, "EC1": 99.0}  # Fuera de rango [0, 20]

        res = coordinator.analyze_student_risk(bad_payload, persist_telemetry=True)
        assert res["status"] == "ERROR"

        msgs = get_bus_messages_for_student(h_cui, limit=10)
        perfs = {m["performativa"] for m in msgs}
        assert "REQUEST" in perfs
        assert "FAILURE" in perfs
        assert raw_cui not in json.dumps(msgs)


class TestGrupoCCabeceraYReportePdfReales:
    """Verifica coherencia entre cabecera, base de datos SQLite y exportación PDF."""

    def test_header_metrics_reflect_real_sqlite_counts_by_role(self):
        cui_demo = hash_cui("20220638")
        est_user = {"id": 4, "username": cui_demo, "role": "ESTUDIANTE", "cui_hash": cui_demo}
        doc_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        aut_user = {"id": 3, "username": "tutor_epis", "role": "AUTORIDAD", "cui_hash": None}

        m_est = get_header_metrics(est_user, semestre="2026-B")
        assert m_est["label_col1"] == "ASIGNATURAS INSCRITAS"
        assert m_est["valor_col1"] >= 1
        assert m_est["ultima_actualizacion"] != "Sin registros"

        m_doc = get_header_metrics(doc_user, semestre="2026-B")
        assert m_doc["label_col1"] == "ESTUDIANTES EN SEGUIMIENTO"
        assert m_doc["valor_col1"] >= 1
        assert m_doc["valor_col1"] != 18  # Nunca el valor ficticio 18

        m_aut = get_header_metrics(aut_user, semestre="2026-B")
        assert m_aut["valor_col1"] == m_doc["valor_col1"]

    def test_pdf_export_uses_persisted_prediction_and_enforces_privacy(self):
        doc_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        admin_user = {"id": 1, "username": "admin", "role": "ADMIN", "cui_hash": None}

        mat_info = get_enrollment_by_id(1, current_user=doc_user)
        pred_info = get_latest_prediction(1, current_user=doc_user)
        assert mat_info is not None
        assert pred_info is not None

        pdf_bytes = generate_intervention_pdf(
            student_id_anon=mat_info["cui_hash"],
            curso=mat_info["curso"],
            docente=mat_info["docente"],
            checkpoint=pred_info["checkpoint"],
            probabilidad_pct=float(pred_info["probabilidad"]) * 100.0,
            umbral_pct=float(pred_info["umbral"]) * 100.0,
            semaforo=pred_info["semaforo"],
            meta_nota_min=pred_info["meta_nota_min"],
            promedio_acumulado=float(pred_info["promedio_acumulado"] or 0.0),
            imposible=bool(pred_info["imposible_ordinario"]),
            top_factors=pred_info["top_factors"],
            recommendations=pred_info["recommendations"],
            current_user=doc_user,
        )
        assert pdf_bytes.startswith(b"%PDF-")
        assert b"20220638" not in pdf_bytes

        with pytest.raises(AuthorizationError):
            generate_intervention_pdf(
                student_id_anon=mat_info["cui_hash"],
                curso=mat_info["curso"],
                docente=mat_info["docente"],
                checkpoint="CP1",
                probabilidad_pct=78.0,
                umbral_pct=34.0,
                semaforo="ROJO",
                meta_nota_min=13.5,
                promedio_acumulado=8.5,
                imposible=False,
                top_factors=[],
                recommendations=[],
                current_user=admin_user,
            )


class TestGrupoDTutoriasYBitacora:
    """Verifica programación, registro, validación, historial y permisos del módulo de tutorías."""

    def test_schedule_and_register_tutoring_persists_in_sqlite_and_validates_fields(self):
        doc_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        admin_user = {"id": 1, "username": "admin", "role": "ADMIN", "cui_hash": None}

        # 1. Validación de campos obligatorios (observaciones vacías debe rechazarse)
        ok_empty, msg_empty = register_tutoring_session(
            matricula_id=1,
            fecha_sesion="2026-11-15",
            estado="REALIZADA",
            observaciones="   ",
            accion_1=True,
            accion_2=True,
            accion_3=False,
            current_user=doc_user,
        )
        assert ok_empty is False
        assert "observaciones" in msg_empty.lower()

        # 2. Programar tutoría válida
        before_hist = get_tutoring_history(1, current_user=doc_user)
        ok_prog, msg_prog = schedule_tutoring_session(
            matricula_id=1,
            fecha_sesion="2026-11-18",
            observaciones="Sesión programada para revisión de ejercicios prácticos de grafos.",
            current_user=doc_user,
        )
        assert ok_prog is True
        assert "persistida en sqlite" in msg_prog.lower()

        # 3. Registrar tutoría realizada con actualización de checklist
        ok_reg, msg_reg = register_tutoring_session(
            matricula_id=1,
            fecha_sesion="2026-11-20",
            estado="REALIZADA",
            observaciones="Estudiante asistió a asesoría y resolvió guía de laboratorio.",
            accion_1=True,
            accion_2=True,
            accion_3=True,
            current_user=doc_user,
        )
        assert ok_reg is True

        after_hist = get_tutoring_history(1, current_user=doc_user)
        assert len(after_hist) == len(before_hist) + 2
        assert after_hist[0]["estado"] == "REALIZADA"
        assert "guía de laboratorio" in after_hist[0]["observaciones"]

        chk = get_tutoring_checklist_state(1, current_user=doc_user)
        assert chk["accion_1"] is True
        assert chk["accion_2"] is True
        assert chk["accion_3"] is True

        # 4. Verificar que ADMIN no puede programar ni consultar tutorías individuales
        with pytest.raises(AuthorizationError):
            schedule_tutoring_session(1, "2026-11-22", "Intento no autorizado", current_user=admin_user)
        with pytest.raises(AuthorizationError):
            get_tutoring_history(1, current_user=admin_user)


class TestGrupoEEncuestaTamYFuncionesConectadas:
    """Verifica cuestionario TAM, simulador de sustitutorio, save_grade y update_student_consent."""

    def test_sus_and_tam_surveys_persist_and_compute_real_averages(self):
        before_sus = get_surveys_stats("SUS")
        before_tam = get_surveys_stats("TAM")

        save_survey("docente_demo", "DOCENTE", "SUS", {"p1": 5, "p2": 1}, 90.0)
        save_survey("docente_demo", "DOCENTE", "TAM", {"pu1": 5, "pu2": 5, "pu3": 5, "peou1": 4, "peou2": 5, "bi1": 5}, 4.83)

        after_sus = get_surveys_stats("SUS")
        after_tam = get_surveys_stats("TAM")

        assert after_sus["total"] == before_sus["total"] + 1
        assert after_sus["promedio"] > 0.0
        assert after_tam["total"] == before_tam["total"] + 1
        assert 1.0 <= after_tam["promedio"] <= 5.0

    def test_substitutory_exam_simulator_normative_rules(self):
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}

        # Caso 1: Falta algún parcial -> no aplica aún
        res_incompleto = calcular_simulacion_sustitutorio(12.0, 10.0, 12.0, 10.0, 12.0, None, pesos)
        assert res_incompleto["aplica"] is False

        # Caso 2: Ya aprobó en ordinario (>= 10.50)
        res_aprobado = calcular_simulacion_sustitutorio(14.0, 13.0, 14.0, 13.0, 14.0, 13.0, pesos)
        assert res_aprobado["aplica"] is False
        assert res_aprobado["ya_aprobo"] is True

        # Caso 3: Desaprobado pero viable reemplazando el parcial más bajo (EP2=4.0 con peso 20%)
        # EC1=12(1.8) + EP1=11(1.65) + EC2=11(2.2) + EP2=4(0.8) + EC3=12(1.8) + EP3=10(1.5) = 9.75
        # Falta 10.50 - 9.75 = 0.75 puntos sobre peso 0.20 => incremento 3.75 => nota en susti = ceil(4 + 3.75) = 8
        res_viable = calcular_simulacion_sustitutorio(12.0, 11.0, 11.0, 4.0, 12.0, 10.0, pesos)
        assert res_viable["aplica"] is True
        assert res_viable["es_viable"] is True
        assert res_viable["parcial_a_reemplazar"] == "EP2"
        assert res_viable["nota_minima_requerida"] == 8

        # Caso 4: Matemáticamente inalcanzable incluso con 20 en el sustitutorio
        res_imposible = calcular_simulacion_sustitutorio(0.0, 2.0, 0.0, 2.0, 0.0, 2.0, pesos)
        assert res_imposible["aplica"] is True
        assert res_imposible["es_viable"] is False
        assert res_imposible["nota_minima_requerida"] is None

    def test_save_grade_and_reevaluation_updates_prediction_and_audit_log(self, coordinator):
        doc_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}
        save_grade(1, "EC2", 14.0, False, motivo="Registro de continua 2", current_user=doc_user)
        save_grade(1, "EP2", 13.0, False, motivo="Registro de parcial 2", current_user=doc_user)
        # Modificar EP2 para disparar auditoría en historial_cambios
        save_grade(1, "EP2", 15.0, False, motivo="Rectificación por revisión de examen", current_user=doc_user)

        grades = get_grades_for_enrollment(1, current_user=doc_user)
        assert grades["EP2"]["valor"] == 15.0

        audit = get_grade_change_history(1, current_user=doc_user)
        assert any(a["evaluacion"] == "EP2" and a["valor_previo"] == 13.0 and a["valor_nuevo"] == 15.0 for a in audit)

        res_eval = evaluate_and_persist_enrollment(1, coordinator, current_user=doc_user)
        assert res_eval["status"] == "SUCCESS"
        assert res_eval["prediction"]["checkpoint"] == "CP2"

        latest_pred = get_latest_prediction(1, current_user=doc_user)
        assert latest_pred["checkpoint"] == "CP2"

    def test_update_student_consent_toggles_optin_visibility_for_teacher(self):
        cui_demo = hash_cui("20220638")
        doc_user = {"id": 2, "username": "docente_demo", "role": "DOCENTE", "cui_hash": None}

        # Desactivar comparte_con_tutor
        update_student_consent(cui_demo, aceptado=True, comparte_tutor=False)
        info_off = get_student_info(cui_demo)
        assert info_off["consentimiento_aceptado"] == 1
        assert info_off["comparte_con_tutor"] == 0

        rows_off = get_course_students_table("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=doc_user)
        target_off = next(r for r in rows_off if r["cui_hash"] == cui_demo)
        assert target_off["id_mostrado"] == f"RES-{cui_demo[:6]}"
        assert target_off["estado_optin"] == "No compartido"

        # Restaurar comparte_con_tutor=True
        update_student_consent(cui_demo, aceptado=True, comparte_tutor=True)
        rows_on = get_course_students_table("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B", current_user=doc_user)
        target_on = next(r for r in rows_on if r["cui_hash"] == cui_demo)
        assert target_on["id_mostrado"] == cui_demo
        assert target_on["estado_optin"] == "Compartido con tutor"


class TestAppUiHighPriorityFlows:
    """Pruebas de interfaz Streamlit AppTest recorriendo las pantallas corregidas por rol."""

    def test_docente_ui_navigation_and_views_without_exceptions(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.session_state["usuario"] = {
            "id": 2,
            "username": "docente_demo",
            "role": "DOCENTE",
            "cui_hash": None,
        }
        at.run()
        assert len(at.exception) == 0

        for view_name in [
            "Detalle con explicabilidad",
            "Trazabilidad multiagente",
            "Seguimiento y plan de tutoría",
            "Carga Masiva de Actas",
        ]:
            at.sidebar.radio[0].set_value(view_name).run()
            assert len(at.exception) == 0, f"Excepción en vista DOCENTE '{view_name}': {at.exception}"

    def test_estudiante_ui_navigation_and_views_without_exceptions(self):
        from streamlit.testing.v1 import AppTest

        cui_demo = hash_cui("20220638")
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.session_state["usuario"] = {
            "id": 4,
            "username": cui_demo,
            "role": "ESTUDIANTE",
            "cui_hash": cui_demo,
        }
        at.run()
        assert len(at.exception) == 0

        for view_name in [
            "Detalle con explicabilidad",
            "Trazabilidad multiagente",
            "Seguimiento y plan de tutoría",
            "Inscribir Asignatura",
            "Perfil Basal",
        ]:
            at.sidebar.radio[0].set_value(view_name).run()
            assert len(at.exception) == 0, f"Excepción en vista ESTUDIANTE '{view_name}': {at.exception}"

    def test_admin_and_autoridad_ui_views_without_exceptions(self):
        from streamlit.testing.v1 import AppTest

        at_admin = AppTest.from_file(APP_PATH, default_timeout=30)
        at_admin.session_state["usuario"] = {
            "id": 1,
            "username": "admin",
            "role": "ADMIN",
            "cui_hash": None,
        }
        at_admin.run()
        assert len(at_admin.exception) == 0

        for view_name in [
            "Monitor Técnico OBJ5",
            "Trazabilidad multiagente",
            "Encuestas SUS / TAM",
        ]:
            at_admin.sidebar.radio[0].set_value(view_name).run()
            assert len(at_admin.exception) == 0, f"Excepción en vista ADMIN '{view_name}': {at_admin.exception}"

        at_aut = AppTest.from_file(APP_PATH, default_timeout=30)
        at_aut.session_state["usuario"] = {
            "id": 3,
            "username": "tutor_epis",
            "role": "AUTORIDAD",
            "cui_hash": None,
        }
        at_aut.run()
        assert len(at_aut.exception) == 0

        for view_name in [
            "Métricas Institucionales",
            "Trazabilidad multiagente",
        ]:
            at_aut.sidebar.radio[0].set_value(view_name).run()
            assert len(at_aut.exception) == 0, f"Excepción en vista AUTORIDAD '{view_name}': {at_aut.exception}"

    def test_phase4_visual_ux_and_responsive_css_contract(self):
        with open(APP_PATH, encoding="utf-8") as f:
            app_src = f.read()

        # A. Botones principales con selectores modernos de Streamlit
        assert 'button[data-testid="stBaseButton-primary"]' in app_src
        assert '[data-testid="stFormSubmitButton"] button' in app_src
        # No debe existir el selector antiguo defectuoso que sobreescribía todos los botones
        assert '.stButton button:not([data-testid="baseButton-primary"])' not in app_src

        # B. Sidebar con alcance aislado y botón Cerrar Sesión de alto contraste
        assert '[data-testid="stSidebar"] .stButton button' in app_src
        assert '[data-testid="stSidebar"] .stRadio label p' in app_src

        # C. Preservación de Material Symbols para evitar ligadura rota keyboard_double_
        assert 'span:not([data-testid="stIconMaterial"])' in app_src
        assert "font-family: 'Material Symbols Rounded', 'Material Icons' !important;" in app_src

        # D. Terminal FIPA-ACL con fondo oscuro y clases semánticas por performativa
        assert "fipa-perf-request" in app_src
        assert "fipa-perf-inform" in app_src
        assert "fipa-perf-propose" in app_src
        assert "fipa-perf-failure" in app_src
        assert "background-color: #1E0709 !important;" in app_src

        # G. Columna Semestre capitalizada en Métricas Institucionales
        assert '"semestre": "Semestre"' in app_src

        # H. Breakpoints responsive para tablet (768px) y móvil (480px)
        assert "@media (max-width: 768px)" in app_src
        assert "@media (max-width: 480px)" in app_src


