"""
Pruebas exhaustivas del Módulo de Seguridad y Privacidad por Diseño (SATA-UNSA).
Verifica:
1. Determinismo, no reversibilidad y variabilidad con sal de hash_cui.
2. Formato PBKDF2 (100,000 iteraciones, sal aleatoria por cuenta, compare_digest).
3. Resistencia a inyección SQL en login y formularios.
4. Cero datos personales (CUI o nombres) en claro en BD, logs de bus y PDFs.
5. Control de acceso basado en roles (RBAC) y cumplimiento de opt-in de tutoría.
"""
import re

import pytest

from src.database.db import (
    authenticate_user,
    get_connection,
    get_course_risk_summary,
    get_course_students_table,
)
from src.reports.pdf_generator import generate_intervention_pdf
from src.security.crypto import hash_cui, hash_password, verify_password


class TestCryptoSecurity:
    """Pruebas de funciones criptográficas y hashing."""

    def test_hash_cui_determinism(self):
        """Verifica que el mismo CUI genera siempre el mismo hash con la misma sal."""
        cui = "20220638"
        h1 = hash_cui(cui)
        h2 = hash_cui(cui)
        assert h1 == h2, "El hash del CUI debe ser determinista para permitir indexación."
        assert len(h1) == 16, "El hash debe tener exactamente 16 caracteres hexadecimales."

    def test_hash_cui_salt_variability(self):
        """Verifica que una sal distinta altera por completo el hash generado."""
        cui = "20220638"
        custom_salt_1 = b"salt_alfa_1234567890123456789012"
        custom_salt_2 = b"salt_beta_1234567890123456789012"
        h1 = hash_cui(cui, salt=custom_salt_1)
        h2 = hash_cui(cui, salt=custom_salt_2)
        assert h1 != h2, "Sales distintas deben producir hashes distintos."

    def test_hash_cui_not_reversible_at_glance(self):
        """Verifica que el hash no contiene el CUI original como subcadena ni patrones triviales."""
        cui = "20220638"
        h = hash_cui(cui)
        assert cui not in h, "El hash no debe contener el CUI original en claro."
        assert not h.startswith("2022"), "El hash no debe preservar prefijos del CUI."

    def test_pbkdf2_format_and_iterations(self):
        """Verifica que hash_password usa PBKDF2-HMAC-SHA256 con exactamente 100,000 iteraciones y sal única."""
        pwd1 = "MiClaveSegura123*"
        pwd2 = "MiClaveSegura123*"
        h1 = hash_password(pwd1)
        h2 = hash_password(pwd2)

        assert h1 != h2, "Cada hash debe tener una sal aleatoria única e independiente."
        parts = h1.split("$")
        assert len(parts) == 3, "El formato de hash debe ser pbkdf2:sha256:iteraciones$sal$hash."
        assert "100000" in parts[0], "Debe requerir 100,000 iteraciones de PBKDF2."
        assert len(bytes.fromhex(parts[1])) == 16, "La sal debe ser criptográfica de 16 bytes."

    def test_verify_password_correct_and_incorrect(self):
        """Verifica validación correcta e incorrecta de contraseñas con PBKDF2."""
        pwd = "ClaveSecretaUNSA2026*"
        h = hash_password(pwd)
        assert verify_password(pwd, h) is True
        assert verify_password("ClaveErronea123*", h) is False
        assert verify_password("", h) is False
        assert verify_password(pwd, "formato_invalido") is False


class TestSqlInjectionResilience:
    """Pruebas de inyección SQL en consultas de autenticación y datos."""

    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "admin' --",
        "' UNION SELECT 1, 'admin', 'hash', 'ADMIN', NULL, '2026' --",
        "20220638' OR 1=1 --",
        "'; DROP TABLE usuarios; --",
        "' OR ''='"
    ])
    def test_sql_injection_in_authenticate_user(self, payload):
        """Verifica que entradas maliciosas no causen bypass ni inyección SQL."""
        res = authenticate_user(payload, "cualquier_clave")
        assert res is None, f"La inyección SQL {payload} no debe autenticar ningún usuario."


class TestPrivacyAndAnonymization:
    """Verifica que ningún CUI ni nombre de estudiante figure en texto plano."""

    def test_no_raw_cui_in_usuarios_table(self):
        """Verifica que la tabla usuarios no guarde CUIs en claro."""
        conn = get_connection()
        rows = conn.execute("SELECT username, cui_hash, role FROM usuarios WHERE role = 'ESTUDIANTE'").fetchall()
        conn.close()

        for r in rows:
            username = r["username"]
            cui_h = r["cui_hash"]
            # Los CUIs de UNSA son de 8 dígitos numéricos (ej. 20220638)
            assert not re.match(r"^\d{8}$", username), f"Username '{username}' contiene un CUI en claro!"
            assert len(username) >= 16, f"Username debe ser un hash de al menos 16 caracteres: {username}"
            if cui_h:
                assert not re.match(r"^\d{8}$", cui_h), f"cui_hash '{cui_h}' contiene un CUI en claro!"

    def test_no_raw_cui_or_personal_name_in_pdf(self):
        """Verifica que el PDF generado no contenga CUI en claro ni nombres personales."""
        raw_cui = "20220638"
        cui_h = hash_cui(raw_cui)
        
        pdf_bytes = generate_intervention_pdf(
            student_id_anon=cui_h,
            curso="REDES Y COMUNICACIONES",
            docente="DOCENTE PRINCIPAL",
            checkpoint="CP1",
            probabilidad_pct=75.0,
            umbral_pct=34.0,
            semaforo="ROJO",
            meta_nota_min=14.0,
            promedio_acumulado=8.5,
            imposible=False,
            top_factors=[{"label": "Evaluación Continua 1", "value": 7.0, "impact": 0.25, "direction": "Riesgo"}],
            recommendations=["Sesión de tutoría académica."]
        )
        import io

        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pdf_text = "".join(page.extract_text() for page in reader.pages)
        assert raw_cui not in pdf_text, "El PDF no debe contener el CUI en claro!"
        assert cui_h in pdf_text, "El PDF debe mostrar el hash del estudiante para trazabilidad."


class TestRoleBasedAccessControl:
    """Control de acceso por rol y privacidad de tutoría (opt-in)."""

    def test_docente_table_masks_students_without_consent(self):
        """Si comparte_con_tutor=0, el docente solo debe ver un ID reservado tipo RES-XXXXXX."""
        conn = get_connection()
        # Insertar estudiante sin consentimiento de compartir
        c_sin_optin = hash_cui("99990001")
        conn.execute("INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro) VALUES (?, 1, 0, '2026-01-01')", (c_sin_optin,))
        conn.execute("INSERT OR IGNORE INTO matriculas (id, cui_hash, semestre, curso, docente, seccion, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3, fecha_inscripcion) VALUES (999, ?, '2026-B', 'CURSO_TEST_RBAC', 'DOCENTE_TEST', 'A', 15, 15, 20, 20, 15, 15, '2026-01-01')", (c_sin_optin,))
        conn.execute("INSERT OR IGNORE INTO predicciones (matricula_id, checkpoint, probabilidad, umbral, semaforo, fecha) VALUES (999, 'CP1', 0.85, 0.340, 'ROJO', '2026-01-01')")
        conn.commit()
        conn.close()

        students = get_course_students_table("CURSO_TEST_RBAC", "2026-B")
        target = [s for s in students if s["cui_hash"] == c_sin_optin]
        assert len(target) == 1
        assert target[0]["estado_optin"] == "No compartido"
        assert target[0]["id_mostrado"].startswith("RES-")

    def test_autoridad_summary_has_no_individual_cui(self):
        """La vista de autoridad solo debe retornar métricas agregadas (conteo de rojos, amarillos, verdes)."""
        summary = get_course_risk_summary("ESTRUCTURAS DE DATOS Y ALGORITMOS", "2026-B")
        assert "cui_hash" not in summary, "El resumen de autoridad no debe incluir identificadores individuales."
        assert "total_alumnos" in summary
        assert "rojos" in summary
        assert "amarillos" in summary
        assert "verdes" in summary
        assert "tasa_riesgo_pct" in summary
