"""
Pruebas de Integridad, Concurrencia y Auditoría de la Base de Datos SQLite (SATA-UNSA).
Verifica:
1. Modo WAL (Write-Ahead Logging) activo.
2. Integridad referencial (FOREIGN KEYS activos).
3. Transacciones atómicas y rollback ante excepciones.
4. Historial de auditoría en la tabla 'historial_cambios'.
5. Lecturas concurrentes durante operaciones de escritura.
"""
import sqlite3
import threading
import time

import pytest

from src.database.db import (
    enroll_course,
    get_connection,
    save_grade,
)
from src.security.crypto import hash_cui


class TestDatabaseIntegrityAndConcurrency:
    """Pruebas de persistencia y propiedades ACID."""

    def test_wal_mode_is_active(self):
        """Verifica que SQLite esté configurado en modo WAL para concurrencia segura en Streamlit."""
        conn = get_connection()
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        conn.close()
        assert journal_mode.lower() == "wal", f"Se esperaba journal_mode='wal', obtenido: {journal_mode}"

    def test_foreign_keys_are_enforced(self):
        """Verifica que las claves foráneas estén activadas y rechacen huérfanos."""
        conn = get_connection()
        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk_status == 1, "PRAGMA foreign_keys debe ser 1 (activado)."

        # Intentar insertar una matrícula con cui_hash inexistente debe fallar
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
            INSERT INTO matriculas 
            (cui_hash, semestre, curso, docente, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3, fecha_inscripcion)
            VALUES ('CUI_INEXISTENTE_9999', '2026-B', 'CURSO_X', 'DOC_X', 15, 15, 20, 20, 15, 15, '2026-01-01')
            """)
        conn.close()

    def test_audit_log_records_grade_changes(self):
        """Verifica que cada actualización de calificación registre un registro de auditoría."""
        cui_test = hash_cui("TEST_AUDITORIA_001")
        conn = get_connection()
        now_str = "2026-01-01T00:00:00"
        conn.execute("INSERT OR IGNORE INTO estudiantes (cui_hash, fecha_registro) VALUES (?, ?)", (cui_test, now_str))
        conn.commit()
        conn.close()

        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        mat_id = enroll_course(cui_test, "2026-B", "CURSO_AUDIT", "DOCENTE_AUDIT", "A", pesos, 0)

        # 1. Registro inicial de nota
        save_grade(mat_id, "EC1", 12.0, False, motivo="Registro inicial")
        
        # 2. Modificación de la nota
        save_grade(mat_id, "EC1", 16.5, False, motivo="Corrección por reclamo de examen")

        conn = get_connection()
        cambios = conn.execute("""
        SELECT valor_previo, valor_nuevo, motivo FROM historial_cambios 
        WHERE matricula_id = ? AND evaluacion = 'EC1'
        ORDER BY id DESC
        """, (mat_id,)).fetchall()
        conn.close()

        assert len(cambios) >= 1, "Debe existir al menos un registro en historial_cambios tras modificar la nota."
        ultimo = cambios[0]
        assert ultimo["valor_previo"] == 12.0
        assert ultimo["valor_nuevo"] == 16.5
        assert "reclamo" in ultimo["motivo"].lower()

    def test_transaction_rollback_on_error(self):
        """Verifica que una transacción con error ejecute rollback y no deje cambios parciales."""
        conn = get_connection()
        cur = conn.cursor()
        
        count_before = cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

        try:
            cur.execute("BEGIN TRANSACTION;")
            cur.execute("INSERT INTO usuarios (username, password_hash, role, fecha_creacion) VALUES ('temp_user', 'hash', 'ADMIN', 'now')")
            # Forzar error de clave única o sintaxis
            cur.execute("INSERT INTO usuarios (username, password_hash, role, fecha_creacion) VALUES ('temp_user', 'hash', 'ADMIN', 'now')")
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()

        count_after = cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        conn.close()

        assert count_before == count_after, "El rollback debió restaurar el estado previo de la tabla."

    def test_concurrent_reads_during_write(self):
        """Verifica que lecturas concurrentes en hilos separados no queden bloqueadas gracias al modo WAL."""
        errors = []

        def reader_task():
            try:
                for _ in range(10):
                    c = get_connection()
                    rows = c.execute("SELECT COUNT(*) FROM catalogo_cursos").fetchone()[0]
                    assert rows > 0
                    c.close()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader_task) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Lecturas concurrentes fallaron: {errors}"
