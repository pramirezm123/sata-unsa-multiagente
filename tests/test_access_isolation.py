"""
Pruebas de Aislamiento de Datos por Estudiante y Control de Acceso (SATA-UNSA).
Verifica que ningún estudiante pueda acceder, modificar ni consultar datos de otro estudiante.
"""
import pytest

from src.database.db import (
    enroll_course,
    get_bus_messages_for_student,
    get_course_students_table,
    get_student_enrollments,
    get_student_profile,
    log_bus_message,
    save_student_profile,
)
from src.reports.pdf_generator import generate_intervention_pdf
from src.security.access_control import (
    AuthorizationError,
    require_role,
    validate_student_access,
)


@pytest.fixture
def student_user_a():
    return {
        "id": 101,
        "username": "cui_hash_aaa",
        "cui_hash": "cui_hash_aaa",
        "role": "ESTUDIANTE"
    }


@pytest.fixture
def student_user_b():
    return {
        "id": 102,
        "username": "cui_hash_bbb",
        "cui_hash": "cui_hash_bbb",
        "role": "ESTUDIANTE"
    }


@pytest.fixture
def teacher_user():
    return {
        "id": 201,
        "username": "docente_demo",
        "cui_hash": None,
        "role": "DOCENTE"
    }


@pytest.fixture
def admin_user():
    return {
        "id": 301,
        "username": "admin",
        "cui_hash": None,
        "role": "ADMIN"
    }


class TestAccessControlHelpers:
    """Verifica los guardias de acceso a nivel de módulo security."""

    def test_student_can_access_own_data(self, student_user_a):
        # No debe lanzar excepción
        validate_student_access(student_user_a, "cui_hash_aaa")

    def test_student_cannot_access_other_student_data(self, student_user_a):
        with pytest.raises(AuthorizationError) as exc_info:
            validate_student_access(student_user_a, "cui_hash_bbb")
        assert "Violación de aislamiento de datos" in str(exc_info.value)

    def test_teacher_can_access_student_data(self, teacher_user):
        # Los docentes tienen rol autorizado para supervisar
        validate_student_access(teacher_user, "cui_hash_aaa")

    def test_require_role_enforcement(self, student_user_a, teacher_user):
        # Estudiante no tiene rol DOCENTE
        with pytest.raises(AuthorizationError):
            require_role(student_user_a, ["DOCENTE", "AUTORIDAD", "ADMIN"])
        # Docente sí lo tiene
        require_role(teacher_user, ["DOCENTE", "AUTORIDAD", "ADMIN"])


class TestDatabaseStudentIsolation:
    """Verifica que las consultas en db.py bloqueen el acceso cruzado."""

    def test_student_cannot_view_other_profile(self, student_user_a):
        with pytest.raises(AuthorizationError):
            get_student_profile("cui_hash_bbb", "2026-B", current_user=student_user_a)

    def test_student_cannot_save_other_profile(self, student_user_a):
        with pytest.raises(AuthorizationError):
            save_student_profile("cui_hash_bbb", "2026-B", 14.0, 0, 20, 4.0, current_user=student_user_a)

    def test_student_cannot_enroll_other_student(self, student_user_a):
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        with pytest.raises(AuthorizationError):
            enroll_course("cui_hash_bbb", "2026-B", "Estructuras de Datos", "Docente A", "A", pesos, 0, current_user=student_user_a)

    def test_student_cannot_view_other_enrollments(self, student_user_a):
        with pytest.raises(AuthorizationError):
            get_student_enrollments("cui_hash_bbb", "2026-B", current_user=student_user_a)

    def test_student_cannot_view_all_course_students(self, student_user_a):
        with pytest.raises(AuthorizationError):
            get_course_students_table("Estructuras de Datos", "2026-B", current_user=student_user_a)

    def test_teacher_can_view_course_students(self, teacher_user):
        # No debe lanzar AuthorizationError
        result = get_course_students_table("Estructuras de Datos", "2026-B", current_user=teacher_user)
        assert isinstance(result, list)


class TestPdfStudentIsolation:
    """Verifica que el generador de PDF impida generar fichas de otro estudiante."""

    def test_student_generates_own_pdf(self, student_user_a):
        pdf = generate_intervention_pdf(
            student_id_anon="cui_hash_aaa",
            curso="Estructuras de Datos",
            docente="Docente A",
            checkpoint="CP1",
            probabilidad_pct=75.0,
            umbral_pct=34.0,
            semaforo="ROJO",
            meta_nota_min=13.0,
            promedio_acumulado=9.5,
            imposible=False,
            top_factors=[{"label": "Asistencia", "value": 0.4, "direction": "Riesgo"}],
            recommendations=["Asistir a tutoría"],
            current_user=student_user_a
        )
        assert pdf.startswith(b"%PDF")

    def test_student_cannot_generate_other_student_pdf(self, student_user_a):
        with pytest.raises(AuthorizationError) as exc_info:
            generate_intervention_pdf(
                student_id_anon="cui_hash_bbb",
                curso="Estructuras de Datos",
                docente="Docente A",
                checkpoint="CP1",
                probabilidad_pct=75.0,
                umbral_pct=34.0,
                semaforo="ROJO",
                meta_nota_min=13.0,
                promedio_acumulado=9.5,
                imposible=False,
                top_factors=[{"label": "Asistencia", "value": 0.4, "direction": "Riesgo"}],
                recommendations=["Asistir a tutoría"],
                current_user=student_user_a
            )
        assert "Violación de aislamiento de datos" in str(exc_info.value)

    def test_bus_messages_filtered_by_student(self, student_user_a, student_user_b):
        cui_a = student_user_a["cui_hash"]
        cui_b = student_user_b["cui_hash"]

        # Insertar mensajes en el bus simulando inferencia para A y B
        log_bus_message("req-101", "PredictorAgent", "XaiAgent", "INFORM", "PREDICCION_CALCULADA", {"cui_hash": cui_a, "prob": 0.75})
        log_bus_message("req-102", "PredictorAgent", "XaiAgent", "INFORM", "PREDICCION_CALCULADA", {"cui_hash": cui_b, "prob": 0.20})

        msgs_a = get_bus_messages_for_student(cui_a, limit=10)
        assert len(msgs_a) > 0
        for m in msgs_a:
            assert cui_a in m["contenido_json"]
            assert cui_b not in m["contenido_json"]
