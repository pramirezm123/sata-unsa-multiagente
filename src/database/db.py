"""
Capa de Persistencia y Base de Datos Local SQLite para SATA-UNSA.
Garantiza:
- Cero costo y portabilidad total (sin requerir servidores externos).
- Modo WAL (Write-Ahead Logging) para concurrencia segura en Streamlit.
- Tablas completas según Sección 8 de la especificación técnica.
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Any

from ..security.crypto import hash_cui, hash_password, verify_password

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "sata_unsa.db")


def get_connection() -> sqlite3.Connection:
    """Retorna una conexión a SQLite configurada con modo WAL y Row factory."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Crea el esquema de base de datos relacional si no existe."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Usuarios y Autenticación
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- 'ESTUDIANTE', 'DOCENTE', 'AUTORIDAD', 'ADMIN'
        cui_hash TEXT,      -- Solo para ESTUDIANTE
        fecha_creacion TEXT NOT NULL
    );
    """)

    # 2. Estudiantes y Consentimiento Informado
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estudiantes (
        cui_hash TEXT PRIMARY KEY,
        consentimiento_aceptado INTEGER DEFAULT 0, -- 1: Sí, 0: No
        comparte_con_tutor INTEGER DEFAULT 0,     -- 1: Sí (Opt-in), 0: No
        fecha_registro TEXT NOT NULL,
        fecha_consentimiento TEXT
    );
    """)

    # 3. Perfil Basal del Semestre
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS perfil_semestre (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cui_hash TEXT NOT NULL,
        semestre TEXT NOT NULL,
        ira_acum REAL NOT NULL,
        repeticiones_previas INTEGER NOT NULL,
        creditos_matriculados INTEGER NOT NULL,
        semestre_ingreso REAL NOT NULL,
        origen TEXT DEFAULT 'DECLARADO', -- 'DECLARADO', 'ACTA'
        fecha_actualizacion TEXT NOT NULL,
        FOREIGN KEY (cui_hash) REFERENCES estudiantes(cui_hash)
    );
    """)

    # 4. Catálogos: Asignaturas y Docentes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalogo_cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nombre TEXT UNIQUE NOT NULL,
        semestre_malla INTEGER DEFAULT 5,
        peso_ec1 INTEGER DEFAULT 15,
        peso_ep1 INTEGER DEFAULT 15,
        peso_ec2 INTEGER DEFAULT 20,
        peso_ep2 INTEGER DEFAULT 20,
        peso_ec3 INTEGER DEFAULT 15,
        peso_ep3 INTEGER DEFAULT 15
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalogo_docentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        departamento TEXT DEFAULT 'Ingeniería de Sistemas e Informática'
    );
    """)

    # 5. Matrícula de Curso por Estudiante
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cui_hash TEXT NOT NULL,
        semestre TEXT NOT NULL,
        curso TEXT NOT NULL,
        docente TEXT NOT NULL,
        seccion TEXT DEFAULT 'A',
        peso_ec1 INTEGER NOT NULL,
        peso_ep1 INTEGER NOT NULL,
        peso_ec2 INTEGER NOT NULL,
        peso_ep2 INTEGER NOT NULL,
        peso_ec3 INTEGER NOT NULL,
        peso_ep3 INTEGER NOT NULL,
        es_repeticion INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'ACTIVO', -- 'ACTIVO', 'CERRADO'
        fecha_inscripcion TEXT NOT NULL,
        FOREIGN KEY (cui_hash) REFERENCES estudiantes(cui_hash)
    );
    """)

    # 6. Calificaciones de Evaluaciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        evaluacion TEXT NOT NULL, -- 'EC1', 'EP1', 'EC2', 'EP2', 'EC3', 'EP3'
        valor_num REAL,          -- 0.0 a 20.0 (None si ausente o pendiente)
        es_ausente INTEGER DEFAULT 0, -- 1: Sí (NSP/AUSENTE), 0: No (rindió)
        fecha_registro TEXT NOT NULL,
        origen TEXT DEFAULT 'ESTUDIANTE', -- 'ESTUDIANTE', 'DOCENTE_ACTA'
        UNIQUE(matricula_id, evaluacion),
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    );
    """)

    # 7. Historial de Auditoría de Cambios de Nota
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial_cambios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        evaluacion TEXT NOT NULL,
        valor_previo REAL,
        valor_nuevo REAL,
        motivo TEXT,
        fecha_cambio TEXT NOT NULL,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    );
    """)

    # 8. Predicciones Generadas por Checkpoint
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predicciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        checkpoint TEXT NOT NULL, -- 'CP0', 'CP1', 'CP2', 'CP3'
        probabilidad REAL NOT NULL,
        umbral REAL NOT NULL,
        semaforo TEXT NOT NULL,   -- 'VERDE', 'AMARILLO', 'ROJO'
        meta_nota_min REAL,
        promedio_acumulado REAL,
        imposible_ordinario INTEGER DEFAULT 0,
        version_modelo TEXT DEFAULT 'v1.0-RF',
        fecha TEXT NOT NULL,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    );
    """)

    # 9. Explicabilidad Almacenada (SHAP)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS explicaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediccion_id INTEGER NOT NULL,
        top_factors_json TEXT NOT NULL,
        recomendaciones_json TEXT NOT NULL,
        fidelidad_r REAL,
        fecha TEXT NOT NULL,
        FOREIGN KEY (prediccion_id) REFERENCES predicciones(id)
    );
    """)

    # 10. Bitácora de Mensajería FIPA-ACL del Bus
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensajes_bus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL,
        emisor TEXT NOT NULL,
        receptor TEXT NOT NULL,
        performativa TEXT NOT NULL,
        topico TEXT NOT NULL,
        contenido_json TEXT,
        duracion_ms REAL,
        timestamp TEXT NOT NULL
    );
    """)

    # 11. Métricas Técnicas de Desempeño (OBJ5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metricas_tecnicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL,
        checkpoint TEXT NOT NULL,
        latencia_inferencia_ms REAL NOT NULL,
        latencia_xai_ms REAL,
        latencia_total_ms REAL NOT NULL,
        ram_mb REAL NOT NULL,
        overhead_bus_ms REAL,
        timestamp TEXT NOT NULL
    );
    """)

    # 12. Encuestas Psicométricas de Usabilidad (SUS y TAM)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_anonimo TEXT NOT NULL,
        rol TEXT NOT NULL,
        tipo_encuesta TEXT NOT NULL, -- 'SUS', 'TAM'
        respuestas_json TEXT NOT NULL,
        puntaje_total REAL,
        fecha TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()


def seed_initial_data():
    """Siembra los catálogos oficiales y usuarios demo para pruebas técnicas."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Catálogo de Cursos Emblemáticos de la EPIS-UNSA
    cursos_default = [
        ("ANALISIS Y DISENO DE ALGORITMOS", 4, 15, 15, 20, 20, 15, 15),
        ("TEORIA DE LA COMPUTACION", 5, 15, 15, 20, 20, 15, 15),
        ("SEGURIDAD INFORMATICA", 8, 15, 15, 20, 20, 15, 15),
        ("BASE DE DATOS 1", 5, 15, 15, 20, 20, 15, 15),
        ("INGENIERIA DE SOFTWARE 1", 6, 15, 15, 20, 20, 15, 15),
        ("SISTEMAS OPERATIVOS", 5, 15, 15, 20, 20, 15, 15),
        ("REDES Y COMUNICACION DE DATOS", 6, 15, 15, 20, 20, 15, 15),
        ("ESTRUCTURAS DE DATOS Y ALGORITMOS", 3, 15, 15, 20, 20, 15, 15),
        ("INTELIGENCIA ARTIFICIAL", 7, 15, 15, 20, 20, 15, 15)
    ]
    for nombre, ciclo, ec1, ep1, ec2, ep2, ec3, ep3 in cursos_default:
        cursor.execute("""
        INSERT OR IGNORE INTO catalogo_cursos 
        (nombre, semestre_malla, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, ciclo, ec1, ep1, ec2, ep2, ec3, ep3))

    # 2. Catálogo de Docentes (Docente Titular / Principal)
    docentes_default = [
        "DOCENTE PRINCIPAL 1",
        "DOCENTE ASOCIADO 2",
        "DOCENTE AUXILIAR 3",
        "DOCENTE TITULAR EPIS",
        "CO-DICTADO GRUPO A"
    ]
    for doc in docentes_default:
        cursor.execute("INSERT OR IGNORE INTO catalogo_docentes (nombre) VALUES (?)", (doc,))

    # 3. Usuarios Demo Pre-sembrados
    now_str = datetime.now().isoformat()
    cui_demo_1 = hash_cui("20220638")
    cui_demo_2 = hash_cui("20190638")
    usuarios_demo = [
        ("admin", hash_password("Admin123*"), "ADMIN", None),
        ("docente_demo", hash_password("Docente123*"), "DOCENTE", None),
        ("tutor_epis", hash_password("Tutor123*"), "AUTORIDAD", None),
        # Estudiantes con CUI hash irreversible (cero CUI en claro)
        (cui_demo_1, hash_password("Alumno123*"), "ESTUDIANTE", cui_demo_1),
        (cui_demo_2, hash_password("Alumno123*"), "ESTUDIANTE", cui_demo_2)
    ]
    for u, p_hash, r, cui_h in usuarios_demo:
        cursor.execute("""
        INSERT OR IGNORE INTO usuarios (username, password_hash, role, cui_hash, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
        """, (u, p_hash, r, cui_h, now_str))

    # Asegurar registro del estudiante demo en tabla estudiantes
    for c_hash in [cui_demo_1, cui_demo_2]:
        cursor.execute("""
        INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro)
        VALUES (?, 1, 1, ?)
        """, (c_hash, now_str))

    # Perfil basal demo
    cursor.execute("""
    INSERT OR IGNORE INTO perfil_semestre 
    (cui_hash, semestre, ira_acum, repeticiones_previas, creditos_matriculados, semestre_ingreso, origen, fecha_actualizacion)
    VALUES (?, '2026-B', 11.5, 1, 6, 4.0, 'DECLARADO', ?)
    """, (cui_demo_1, now_str))

    # Matrícula demo
    cursor.execute("""
    INSERT OR IGNORE INTO matriculas 
    (id, cui_hash, semestre, curso, docente, seccion, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3, es_repeticion, fecha_inscripcion)
    VALUES (1, ?, '2026-B', 'ESTRUCTURAS DE DATOS Y ALGORITMOS', 'DOCENTE PRINCIPAL 1', 'A', 15, 15, 20, 20, 15, 15, 1, ?)
    """, (cui_demo_1, now_str))

    # Notas demo Fase 1
    cursor.execute("""
    INSERT OR IGNORE INTO notas (matricula_id, evaluacion, valor_num, es_ausente, fecha_registro)
    VALUES (1, 'EC1', 9.0, 0, ?), (1, 'EP1', 8.0, 0, ?)
    """, (now_str, now_str))

    # Predicción y explicación demo
    cursor.execute("""
    INSERT OR IGNORE INTO predicciones 
    (id, matricula_id, checkpoint, probabilidad, umbral, semaforo, meta_nota_min, promedio_acumulado, imposible_ordinario, fecha)
    VALUES (1, 1, 'CP1', 0.78, 0.340, 'ROJO', 13.5, 8.5, 0, ?)
    """, (now_str,))

    top_factors_demo = json.dumps([
        {"label": "Evaluación Continua 1", "value": 9.0, "impact": 0.28, "direction": "Riesgo"},
        {"label": "Examen Parcial 1", "value": 8.0, "impact": 0.24, "direction": "Riesgo"},
        {"label": "Índice de Rendimiento Acumulado (IRA)", "value": 11.5, "impact": 0.12, "direction": "Riesgo"},
        {"label": "Carga de cursos matriculados", "value": 6, "impact": -0.05, "direction": "Protección"}
    ])
    recs_demo = json.dumps([
        "Coordinar sesión de tutoría individualizada y reforzar conceptos de árboles y grafos.",
        "Monitorear la entrega de prácticas calificadas en Evaluación Continua 2."
    ])
    cursor.execute("""
    INSERT OR IGNORE INTO explicaciones (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
    VALUES (1, ?, ?, 0.96, ?)
    """, (top_factors_demo, recs_demo, now_str))

    conn.commit()
    conn.close()


# ------------------ FUNCIONES DE NEGOCIO Y ACCESO A DATOS ------------------

def authenticate_user(username: str, password_raw: str) -> dict[str, Any] | None:
    """Autentica a un usuario por username o por cui_hash (calculado al vuelo) y retorna su perfil."""
    conn = get_connection()
    ident = username.strip()
    ident_hash = hash_cui(ident)
    row = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? OR cui_hash = ? OR username = ? OR cui_hash = ?",
        (ident, ident, ident_hash, ident_hash)
    ).fetchone()
    conn.close()
    if not row:
        return None
    if verify_password(password_raw, row["password_hash"]):
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "cui_hash": row["cui_hash"] or row["username"]
        }
    return None


def register_student_user(cui_raw: str, password_raw: str) -> tuple[bool, str]:
    """Registra una nueva cuenta de estudiante transformando el CUI en hash irreversible."""
    cui_clean = cui_raw.strip().upper()
    if len(cui_clean) < 6:
        return False, "El CUI debe contener al menos 6 caracteres."
    cui_h = hash_cui(cui_clean)
    now_str = datetime.now().isoformat()
    
    conn = get_connection()
    try:
        # Verificar si el usuario ya existe
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE username = ? OR cui_hash = ?", (cui_clean, cui_h))
        if cursor.fetchone():
            conn.close()
            return False, "Este CUI ya se encuentra registrado en el sistema."
        
        # Guardar en usuarios (el username no guarda el CUI si preferimos estricta privacidad, o username = cui_h[:8])
        # Para que el estudiante pueda entrar con su CUI habitual, usamos username=cui_clean O un alias seguro.
        # Según la especificación: "El estudiante ingresa su CUI y una clave. El sistema calcula el hash y descarta el CUI."
        # Por tanto, el username se almacena ÚNICAMENTE como el hash irreversible.
        p_hash = hash_password(password_raw)
        cursor.execute("""
        INSERT INTO usuarios (username, password_hash, role, cui_hash, fecha_creacion)
        VALUES (?, ?, 'ESTUDIANTE', ?, ?)
        """, (cui_h, p_hash, cui_h, now_str))

        cursor.execute("""
        INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro)
        VALUES (?, 0, 0, ?)
        """, (cui_h, now_str))

        conn.commit()
        conn.close()
        return True, "Cuenta de estudiante registrada con éxito."
    except Exception as e:
        conn.close()
        return False, f"Error al registrar: {e!s}"


def get_student_info(cui_hash: str) -> dict[str, Any] | None:
    """Obtiene los datos de consentimiento de un estudiante por su hash."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM estudiantes WHERE cui_hash = ?", (cui_hash,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_student_consent(cui_hash: str, aceptado: bool, comparte_tutor: bool):
    """Actualiza el consentimiento y la opción de compartir con tutor."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    conn.execute("""
    UPDATE estudiantes 
    SET consentimiento_aceptado = ?, comparte_con_tutor = ?, fecha_consentimiento = ?
    WHERE cui_hash = ?
    """, (1 if aceptado else 0, 1 if comparte_tutor else 0, now_str, cui_hash))
    conn.commit()
    conn.close()


def get_student_profile(cui_hash: str, semestre: str = "2026-B") -> dict[str, Any] | None:
    """Obtiene el perfil basal del estudiante para un semestre."""
    conn = get_connection()
    row = conn.execute("""
    SELECT * FROM perfil_semestre 
    WHERE cui_hash = ? AND semestre = ?
    ORDER BY id DESC LIMIT 1
    """, (cui_hash, semestre)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_student_profile(cui_hash: str, semestre: str, ira: float, repeticiones: int, 
                         creditos: int, semestre_ingreso: float) -> bool:
    """Guarda o actualiza el perfil basal del estudiante."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    conn.execute("""
    INSERT INTO perfil_semestre 
    (cui_hash, semestre, ira_acum, repeticiones_previas, creditos_matriculados, semestre_ingreso, origen, fecha_actualizacion)
    VALUES (?, ?, ?, ?, ?, ?, 'DECLARADO', ?)
    """, (cui_hash, semestre, ira, repeticiones, creditos, semestre_ingreso, now_str))
    conn.commit()
    conn.close()
    return True


def get_all_courses() -> list[dict[str, Any]]:
    """Retorna la lista de cursos del catálogo oficial."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM catalogo_cursos ORDER BY nombre ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_teachers() -> list[str]:
    """Retorna la lista de docentes disponibles."""
    conn = get_connection()
    rows = conn.execute("SELECT nombre FROM catalogo_docentes ORDER BY nombre ASC").fetchall()
    conn.close()
    return [r["nombre"] for r in rows]


def enroll_course(cui_hash: str, semestre: str, curso: str, docente: str, 
                  seccion: str, pesos: dict[str, int], es_repeticion: int) -> int:
    """Inscribe un curso para el estudiante y retorna el ID de la matrícula."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO matriculas 
    (cui_hash, semestre, curso, docente, seccion, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3, es_repeticion, fecha_inscripcion)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cui_hash, semestre, curso, docente, seccion,
        pesos.get("EC1", 15), pesos.get("EP1", 15),
        pesos.get("EC2", 20), pesos.get("EP2", 20),
        pesos.get("EC3", 15), pesos.get("EP3", 15),
        es_repeticion, now_str
    ))
    mat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mat_id


def get_student_enrollments(cui_hash: str, semestre: str = "2026-B") -> list[dict[str, Any]]:
    """Retorna las asignaturas matriculadas por el estudiante."""
    conn = get_connection()
    rows = conn.execute("""
    SELECT * FROM matriculas 
    WHERE cui_hash = ? AND semestre = ?
    ORDER BY id DESC
    """, (cui_hash, semestre)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_grade(matricula_id: int, evaluacion: str, valor: float | None, 
               es_ausente: bool, motivo: str = "Registro regular") -> bool:
    """Registra o actualiza una nota intra-semestral con auditoría de cambios."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    # Verificar si ya existía valor previo
    prev_row = cursor.execute("""
    SELECT valor_num, es_ausente FROM notas 
    WHERE matricula_id = ? AND evaluacion = ?
    """, (matricula_id, evaluacion)).fetchone()

    if prev_row:
        prev_val = prev_row["valor_num"]
        # Solo registrar auditoría si cambió
        if prev_val != valor or prev_row["es_ausente"] != (1 if es_ausente else 0):
            cursor.execute("""
            INSERT INTO historial_cambios (matricula_id, evaluacion, valor_previo, valor_nuevo, motivo, fecha_cambio)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (matricula_id, evaluacion, prev_val, valor, motivo, now_str))

            cursor.execute("""
            UPDATE notas 
            SET valor_num = ?, es_ausente = ?, fecha_registro = ?
            WHERE matricula_id = ? AND evaluacion = ?
            """, (valor, 1 if es_ausente else 0, now_str, matricula_id, evaluacion))
    else:
        cursor.execute("""
        INSERT INTO notas (matricula_id, evaluacion, valor_num, es_ausente, fecha_registro)
        VALUES (?, ?, ?, ?, ?)
        """, (matricula_id, evaluacion, valor, 1 if es_ausente else 0, now_str))

    conn.commit()
    conn.close()
    return True


def get_grades_for_enrollment(matricula_id: int) -> dict[str, dict[str, Any]]:
    """Retorna un diccionario de notas { 'EC1': {'valor': 12.0, 'ausente': False}, ... }."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notas WHERE matricula_id = ?", (matricula_id,)).fetchall()
    conn.close()
    res = {}
    for r in rows:
        res[r["evaluacion"]] = {
            "valor": r["valor_num"],
            "es_ausente": bool(r["es_ausente"]),
            "fecha": r["fecha_registro"]
        }
    return res


def save_prediction_result(matricula_id: int, checkpoint: str, proba: float, 
                           umbral: float, semaforo: str, meta_nota: float | None, 
                           promedio: float, imposible: bool, top_factors: list, 
                           recs: list, fidelidad: float | None = None) -> int:
    """Guarda la predicción y las explicaciones XAI asociadas."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO predicciones 
    (matricula_id, checkpoint, probabilidad, umbral, semaforo, meta_nota_min, promedio_acumulado, imposible_ordinario, fecha)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (matricula_id, checkpoint, proba, umbral, semaforo, meta_nota, promedio, 1 if imposible else 0, now_str))
    
    pred_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO explicaciones (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
    VALUES (?, ?, ?, ?, ?)
    """, (pred_id, json.dumps(top_factors), json.dumps(recs), fidelidad, now_str))

    conn.commit()
    conn.close()
    return pred_id


def get_latest_prediction(matricula_id: int) -> dict[str, Any] | None:
    """Obtiene la predicción más reciente de una matrícula junto con sus explicaciones."""
    conn = get_connection()
    row = conn.execute("""
    SELECT p.*, e.top_factors_json, e.recomendaciones_json, e.fidelidad_r
    FROM predicciones p
    LEFT JOIN explicaciones e ON p.id = e.prediccion_id
    WHERE p.matricula_id = ?
    ORDER BY p.id DESC LIMIT 1
    """, (matricula_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["top_factors"] = json.loads(d.get("top_factors_json") or "[]")
    d["recommendations"] = json.loads(d.get("recomendaciones_json") or "[]")
    return d


def get_prediction_history(matricula_id: int) -> list[dict[str, Any]]:
    """Obtiene el historial cronológico de predicciones por checkpoint para graficar evolución."""
    conn = get_connection()
    rows = conn.execute("""
    SELECT checkpoint, probabilidad, umbral, semaforo, fecha
    FROM predicciones
    WHERE matricula_id = ?
    ORDER BY id ASC
    """, (matricula_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_course_risk_summary(curso: str, semestre: str = "2026-B") -> dict[str, Any]:
    """Retorna el resumen agregado para docentes/autoridades de un curso."""
    conn = get_connection()
    rows = conn.execute("""
    SELECT p.semaforo, p.probabilidad, m.cui_hash, e.comparte_con_tutor, m.seccion
    FROM matriculas m
    JOIN (
        SELECT matricula_id, MAX(id) as max_id
        FROM predicciones GROUP BY matricula_id
    ) latest ON m.id = latest.matricula_id
    JOIN predicciones p ON latest.max_id = p.id
    JOIN estudiantes e ON m.cui_hash = e.cui_hash
    WHERE m.curso = ? AND m.semestre = ?
    """, (curso, semestre)).fetchall()
    conn.close()

    total = len(rows)
    rojos = sum(1 for r in rows if r["semaforo"] == "ROJO")
    amarillos = sum(1 for r in rows if r["semaforo"] == "AMARILLO")
    verdes = sum(1 for r in rows if r["semaforo"] == "VERDE")

    return {
        "curso": curso,
        "semestre": semestre,
        "total_alumnos": total,
        "rojos": rojos,
        "amarillos": amarillos,
        "verdes": verdes,
        "tasa_riesgo_pct": round((rojos / total * 100) if total > 0 else 0.0, 1)
    }


def get_course_students_table(curso: str, semestre: str = "2026-B") -> list[dict[str, Any]]:
    """
    Retorna la lista de estudiantes para el docente/tutor.
    Si el estudiante NO dio consentimiento (opt-in comparte_con_tutor=0),
    sus datos individuales se anonimizan como 'ALUMNO_RESERVADO'.
    """
    conn = get_connection()
    rows = conn.execute("""
    SELECT m.id as matricula_id, m.cui_hash, m.seccion, e.comparte_con_tutor,
           p.checkpoint, p.probabilidad, p.umbral, p.semaforo, p.meta_nota_min,
           p.promedio_acumulado, p.imposible_ordinario, p.fecha
    FROM matriculas m
    JOIN (
        SELECT matricula_id, MAX(id) as max_id
        FROM predicciones GROUP BY matricula_id
    ) latest ON m.id = latest.matricula_id
    JOIN predicciones p ON latest.max_id = p.id
    JOIN estudiantes e ON m.cui_hash = e.cui_hash
    WHERE m.curso = ? AND m.semestre = ?
    ORDER BY p.probabilidad DESC
    """, (curso, semestre)).fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        if not bool(r["comparte_con_tutor"]):
            item["id_mostrado"] = f"RES-{r['cui_hash'][:6]}"
            item["estado_optin"] = "No compartido"
        else:
            item["id_mostrado"] = r["cui_hash"]
            item["estado_optin"] = "Compartido con tutor"
        result.append(item)
    return result


def log_bus_message(request_id: str, emisor: str, receptor: str, 
                    performativa: str, topico: str, contenido: dict[str, Any], duracion_ms: float = 0.0):
    """Registra en la base de datos cada mensaje FIPA-ACL para auditoría y monitor técnico."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    conn.execute("""
    INSERT INTO mensajes_bus (request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (request_id, emisor, receptor, performativa, topico, json.dumps(contenido), duracion_ms, now_str))
    conn.commit()
    conn.close()


def get_recent_bus_messages(limit: int = 50) -> list[dict[str, Any]]:
    """Obtiene los mensajes más recientes del bus FIPA-ACL."""
    conn = get_connection()
    rows = conn.execute("""
    SELECT id, request_id, emisor, receptor, performativa, topico, duracion_ms, timestamp 
    FROM mensajes_bus ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_technical_metrics(request_id: str, checkpoint: str, lat_inf_ms: float, 
                          lat_xai_ms: float | None, lat_total_ms: float, 
                          ram_mb: float, overhead_bus_ms: float):
    """Guarda las mediciones de latencia y recursos computacionales para el OBJ5."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    conn.execute("""
    INSERT INTO metricas_tecnicas 
    (request_id, checkpoint, latencia_inferencia_ms, latencia_xai_ms, latencia_total_ms, ram_mb, overhead_bus_ms, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (request_id, checkpoint, lat_inf_ms, lat_xai_ms, lat_total_ms, ram_mb, overhead_bus_ms, now_str))
    conn.commit()
    conn.close()


def get_technical_metrics_summary() -> dict[str, Any]:
    """Calcula estadísticas descriptivas para la Ficha de Desempeño Técnico del OBJ5."""
    conn = get_connection()
    rows = conn.execute("""
    SELECT latencia_inferencia_ms, latencia_xai_ms, latencia_total_ms, ram_mb, overhead_bus_ms
    FROM metricas_tecnicas
    """).fetchall()
    conn.close()

    if not rows:
        return {
            "total_muestras": 0,
            "latencia_inf_media": 0.0,
            "latencia_xai_media": 0.0,
            "ram_media": 0.0,
            "overhead_media": 0.0
        }

    inf_vals = [r["latencia_inferencia_ms"] for r in rows]
    xai_vals = [r["latencia_xai_ms"] for r in rows if r["latencia_xai_ms"] is not None]
    ram_vals = [r["ram_mb"] for r in rows]
    over_vals = [r["overhead_bus_ms"] for r in rows if r["overhead_bus_ms"] is not None]

    return {
        "total_muestras": len(rows),
        "latencia_inf_media_ms": round(sum(inf_vals) / len(inf_vals), 2),
        "latencia_inf_p95_ms": round(sorted(inf_vals)[int(len(inf_vals) * 0.95)] if len(inf_vals) >= 20 else max(inf_vals), 2),
        "latencia_xai_media_ms": round(sum(xai_vals) / len(xai_vals), 2) if xai_vals else 0.0,
        "ram_media_mb": round(sum(ram_vals) / len(ram_vals), 1),
        "overhead_media_ms": round(sum(over_vals) / len(over_vals), 3) if over_vals else 0.0
    }


def save_survey(id_anonimo: str, rol: str, tipo: str, respuestas: dict[str, Any], puntaje: float):
    """Guarda una respuesta de cuestionario SUS o TAM."""
    conn = get_connection()
    now_str = datetime.now().isoformat()
    conn.execute("""
    INSERT INTO encuestas (id_anonimo, rol, tipo_encuesta, respuestas_json, puntaje_total, fecha)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (id_anonimo, rol, tipo, json.dumps(respuestas), puntaje, now_str))
    conn.commit()
    conn.close()


def get_surveys_stats(tipo: str) -> dict[str, Any]:
    """Calcula el promedio de puntajes SUS o TAM recopilados."""
    conn = get_connection()
    rows = conn.execute("SELECT puntaje_total FROM encuestas WHERE tipo_encuesta = ?", (tipo,)).fetchall()
    conn.close()
    if not rows:
        return {"total": 0, "promedio": 0.0}
    vals = [r["puntaje_total"] for r in rows]
    return {
        "total": len(vals),
        "promedio": round(sum(vals) / len(vals), 2)
    }

# Inicializar y sembrar la base de datos al importar el módulo
init_database()
seed_initial_data()
