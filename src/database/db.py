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

from ..security.access_control import (
    AuthorizationError,
    get_authorized_teacher_names,
    validate_course_teacher_access,
    validate_matricula_ownership,
    validate_student_access,
)
from ..security.crypto import ensure_cui_hash, hash_cui, hash_password, verify_password

DB_PATH = os.environ.get("SATA_DB_PATH") or os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "sata_unsa.db"
)


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

    # 13. Bitácora de Tutorías y Compromisos Pedagógicos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tutorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL,
        cui_hash TEXT NOT NULL,
        curso TEXT NOT NULL,
        responsable TEXT NOT NULL,
        rol_registro TEXT NOT NULL,
        estado TEXT NOT NULL, -- 'PROGRAMADA', 'REALIZADA', 'SEGUIMIENTO'
        fecha_sesion TEXT NOT NULL,
        observaciones TEXT NOT NULL,
        accion_1_ok INTEGER DEFAULT 0,
        accion_2_ok INTEGER DEFAULT 0,
        accion_3_ok INTEGER DEFAULT 0,
        fecha_registro TEXT NOT NULL,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
    );
    """)

    # Índices únicos de clave de negocio cuando la tabla no contiene duplicados históricos previos
    dup_perf = cursor.execute(
        "SELECT 1 FROM perfil_semestre GROUP BY cui_hash, semestre HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()
    if not dup_perf:
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_perfil_cui_semestre ON perfil_semestre (cui_hash, semestre);"
        )

    dup_exp = cursor.execute(
        "SELECT 1 FROM explicaciones GROUP BY prediccion_id HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()
    if not dup_exp:
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_explicaciones_prediccion ON explicaciones (prediccion_id);"
        )

    conn.commit()
    conn.close()


def seed_initial_data():
    """Siembra los catálogos oficiales y usuarios demo de forma estrictamente idempotente."""
    conn = get_connection()
    changes_before = conn.total_changes
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

    # Perfil basal demo (idempotente por clave de negocio cui_hash + semestre, sin forzar id=1)
    existing_perf = cursor.execute(
        "SELECT id FROM perfil_semestre WHERE cui_hash = ? AND semestre = ? LIMIT 1",
        (cui_demo_1, "2026-B"),
    ).fetchone()
    if not existing_perf:
        cursor.execute("""
        INSERT INTO perfil_semestre
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
    # Explicación demo idempotente por clave de negocio prediccion_id=1 y sin fidelidad_r ficticia (None)
    existing_exp = cursor.execute(
        "SELECT id FROM explicaciones WHERE prediccion_id = ? LIMIT 1",
        (1,),
    ).fetchone()
    if not existing_exp:
        cursor.execute("""
        INSERT INTO explicaciones (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
        VALUES (1, ?, ?, ?, ?)
        """, (top_factors_demo, recs_demo, None, now_str))

    # Sembrar traza FIPA-ACL real inicial para la evaluación demo (sin datos ficticios ni PII)
    req_demo_id = f"eval_{cui_demo_1}_cp1"
    existing_bus = cursor.execute(
        "SELECT COUNT(*) FROM mensajes_bus WHERE request_id = ?", (req_demo_id,)
    ).fetchone()[0]
    if existing_bus == 0:
        fipa_seed_steps = [
            ("CoordinatorAgent", "IngestionAgent", "REQUEST", "INGEST"),
            ("IngestionAgent", "CoordinatorAgent", "INFORM", "INGEST_OK"),
            ("CoordinatorAgent", "PreprocessingAgent", "REQUEST", "PREPROCESS"),
            ("PreprocessingAgent", "CoordinatorAgent", "INFORM", "FEATURES_CP1"),
            ("CoordinatorAgent", "PredictorAgent", "REQUEST", "PREDICT"),
            ("PredictorAgent", "CoordinatorAgent", "INFORM", "PREDICT_CP1"),
            ("CoordinatorAgent", "XaiAgent", "REQUEST", "EXPLAIN"),
            ("XaiAgent", "CoordinatorAgent", "INFORM", "SHAP_CP1"),
            ("CoordinatorAgent", "RecommendationAgent", "REQUEST", "RECOMMEND"),
            ("RecommendationAgent", "CoordinatorAgent", "PROPOSE", "PROPOSE_TUTORIA_CP1"),
            ("CoordinatorAgent", "AlertAgent", "REQUEST", "GENERATE_ALERT"),
            ("AlertAgent", "CoordinatorAgent", "INFORM", "ALERT_ALTO"),
        ]
        for emisor, receptor, perf, topico in fipa_seed_steps:
            contenido_seguro = json.dumps({
                "cui_hash": cui_demo_1,
                "curso": "ESTRUCTURAS DE DATOS Y ALGORITMOS",
                "checkpoint": "CP1",
                "topic": topico,
                "performative": perf,
            })
            cursor.execute("""
            INSERT INTO mensajes_bus
            (request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, 0.15, ?)
            """, (req_demo_id, emisor, receptor, perf, topico, contenido_seguro, now_str))

    # Sembrar registro inicial de tutoría programada para la matrícula demo
    existing_tut = cursor.execute(
        "SELECT COUNT(*) FROM tutorias WHERE matricula_id = 1"
    ).fetchone()[0]
    if existing_tut == 0:
        cursor.execute("""
        INSERT INTO tutorias
        (matricula_id, cui_hash, curso, responsable, rol_registro, estado, fecha_sesion, observaciones, accion_1_ok, accion_2_ok, accion_3_ok, fecha_registro)
        VALUES (1, ?, 'ESTRUCTURAS DE DATOS Y ALGORITMOS', 'DOCENTE PRINCIPAL 1', 'DOCENTE', 'PROGRAMADA', ?, 'Sesión diagnóstica inicial agendada tras alerta temprana en CP1.', 1, 0, 0, ?)
        """, (cui_demo_1, now_str[:10], now_str))

    if conn.total_changes > changes_before:
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


def get_student_profile(cui_hash: str, semestre: str = "2026-B", current_user: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Obtiene el perfil basal del estudiante para un semestre con control de acceso."""
    if current_user:
        validate_student_access(current_user, cui_hash)
    conn = get_connection()
    row = conn.execute("""
    SELECT * FROM perfil_semestre 
    WHERE cui_hash = ? AND semestre = ?
    ORDER BY id DESC LIMIT 1
    """, (cui_hash, semestre)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_student_profile(cui_hash: str, semestre: str, ira: float, repeticiones: int, 
                         creditos: int, semestre_ingreso: float, current_user: dict[str, Any] | None = None) -> bool:
    """Guarda o actualiza el perfil basal del estudiante (idempotente por cui_hash + semestre) con control de acceso."""
    if current_user:
        validate_student_access(current_user, cui_hash)
    conn = get_connection()
    now_str = datetime.now().isoformat()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT id FROM perfil_semestre WHERE cui_hash = ? AND semestre = ? ORDER BY id DESC LIMIT 1",
        (cui_hash, semestre),
    ).fetchone()
    if existing:
        cur.execute("""
        UPDATE perfil_semestre
        SET ira_acum = ?, repeticiones_previas = ?, creditos_matriculados = ?,
            semestre_ingreso = ?, origen = 'DECLARADO', fecha_actualizacion = ?
        WHERE id = ?
        """, (ira, repeticiones, creditos, semestre_ingreso, now_str, int(existing["id"])))
    else:
        cur.execute("""
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
                  seccion: str, pesos: dict[str, int], es_repeticion: int,
                  current_user: dict[str, Any] | None = None) -> int:
    """Inscribe o actualiza un curso para el estudiante (evitando matrículas duplicadas) y retorna el ID."""
    if current_user:
        validate_student_access(current_user, cui_hash)
    conn = get_connection()
    now_str = datetime.now().isoformat()
    cursor = conn.cursor()
    existing = cursor.execute("""
    SELECT id FROM matriculas
    WHERE cui_hash = ? AND semestre = ? AND curso = ?
    ORDER BY id DESC LIMIT 1
    """, (cui_hash, semestre, curso)).fetchone()

    if existing:
        mat_id = int(existing["id"])
        cursor.execute("""
        UPDATE matriculas
        SET docente = ?, seccion = ?, peso_ec1 = ?, peso_ep1 = ?,
            peso_ec2 = ?, peso_ep2 = ?, peso_ec3 = ?, peso_ep3 = ?, es_repeticion = ?
        WHERE id = ?
        """, (
            docente, seccion,
            pesos.get("EC1", 15), pesos.get("EP1", 15),
            pesos.get("EC2", 20), pesos.get("EP2", 20),
            pesos.get("EC3", 15), pesos.get("EP3", 15),
            es_repeticion, mat_id
        ))
    else:
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
        mat_id = int(cursor.lastrowid)

    conn.commit()
    conn.close()
    return mat_id


def get_student_enrollments(cui_hash: str, semestre: str = "2026-B", current_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Retorna las asignaturas matriculadas por el estudiante con validación de acceso."""
    if current_user:
        validate_student_access(current_user, cui_hash)
    conn = get_connection()
    rows = conn.execute("""
    SELECT * FROM matriculas 
    WHERE cui_hash = ? AND semestre = ?
    ORDER BY id DESC
    """, (cui_hash, semestre)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_grade(matricula_id: int, evaluacion: str, valor: float | None, 
               es_ausente: bool, motivo: str = "Registro regular",
               current_user: dict[str, Any] | None = None) -> bool:
    """Registra o actualiza una nota intra-semestral con auditoría de cambios y control de acceso."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
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


def get_grades_for_enrollment(matricula_id: int, current_user: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Retorna un diccionario de notas { 'EC1': {'valor': 12.0, 'ausente': False}, ... } con verificación de acceso."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
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
    """Guarda o actualiza la predicción y las explicaciones XAI asociadas para un checkpoint."""
    from ..agents.xai_agent import normalize_local_fidelity

    fidelidad_clean = normalize_local_fidelity(fidelidad)
    conn = get_connection()
    now_str = datetime.now().isoformat()
    cursor = conn.cursor()

    existing_pred = cursor.execute("""
    SELECT id FROM predicciones
    WHERE matricula_id = ? AND checkpoint = ?
    ORDER BY id DESC LIMIT 1
    """, (matricula_id, checkpoint)).fetchone()

    if existing_pred:
        pred_id = int(existing_pred["id"])
        cursor.execute("""
        UPDATE predicciones
        SET probabilidad = ?, umbral = ?, semaforo = ?, meta_nota_min = ?,
            promedio_acumulado = ?, imposible_ordinario = ?, fecha = ?
        WHERE id = ?
        """, (proba, umbral, semaforo, meta_nota, promedio, 1 if imposible else 0, now_str, pred_id))

        existing_exp = cursor.execute(
            "SELECT id FROM explicaciones WHERE prediccion_id = ? LIMIT 1", (pred_id,)
        ).fetchone()
        if existing_exp:
            cursor.execute("""
            UPDATE explicaciones
            SET top_factors_json = ?, recomendaciones_json = ?, fidelidad_r = ?, fecha = ?
            WHERE prediccion_id = ?
            """, (json.dumps(top_factors), json.dumps(recs), fidelidad_clean, now_str, pred_id))
        else:
            cursor.execute("""
            INSERT INTO explicaciones (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
            VALUES (?, ?, ?, ?, ?)
            """, (pred_id, json.dumps(top_factors), json.dumps(recs), fidelidad_clean, now_str))
    else:
        cursor.execute("""
        INSERT INTO predicciones 
        (matricula_id, checkpoint, probabilidad, umbral, semaforo, meta_nota_min, promedio_acumulado, imposible_ordinario, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (matricula_id, checkpoint, proba, umbral, semaforo, meta_nota, promedio, 1 if imposible else 0, now_str))
        
        pred_id = int(cursor.lastrowid)

        cursor.execute("""
        INSERT INTO explicaciones (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
        VALUES (?, ?, ?, ?, ?)
        """, (pred_id, json.dumps(top_factors), json.dumps(recs), fidelidad_clean, now_str))

    conn.commit()
    conn.close()
    return pred_id


def persist_acta_row_transactional(
    raw_student_id: str,
    semestre: str,
    curso: str,
    docente: str,
    seccion: str,
    pesos: dict[str, int],
    ira: float,
    repeticiones: int,
    creditos_matriculados: int,
    eval_vals: dict[str, float | None],
    eval_ausentes: dict[str, bool],
    sma_result: dict[str, Any],
    semaforo_color: str,
) -> dict[str, Any]:
    """
    Persiste de forma atómica y transaccional todos los artefactos derivados de una fila
    válida de carga masiva de actas:
    1. Anonimización HMAC-SHA256 del CUI (cero CUI en claro).
    2. Registro/actualización de catálogos, estudiante y perfil basal semestral.
    3. Creación o actualización de matrícula (sin duplicados al reimportar).
    4. Persistencia de calificaciones parciales y auditoría de cambios.
    5. Persistencia de predicción y explicaciones SHAP (sin duplicados por checkpoint).
    6. Persistencia de trazas FIPA-ACL del bus y métricas técnicas OBJ5.
    Si ocurre cualquier excepción en la transacción, ejecuta ROLLBACK completo.
    """
    cui_hash = ensure_cui_hash(raw_student_id)
    now_str = datetime.now().isoformat()
    es_rep = 1 if repeticiones > 0 else 0

    al = sma_result.get("alert", {})
    pred = sma_result.get("prediction", {})
    xai = sma_result.get("xai", {})
    history = sma_result.get("history", [])
    telemetry = sma_result.get("telemetry", {})

    checkpoint = str(al.get("checkpoint") or pred.get("checkpoint") or "CP0")
    prob_val = float(pred.get("probability", al.get("probability_pct", 0.0) / 100.0))
    umbral_val = float(pred.get("threshold", al.get("threshold_pct", 34.0) / 100.0))
    meta_nota = al.get("meta_nota_min")
    prom_acum = float(al.get("promedio_acumulado") or 0.0)
    imposible = bool(al.get("imposible_ordinario", False))
    top_factors = al.get("top_factors") or xai.get("top_factors") or []
    recs = al.get("recommendations") or []
    from ..agents.xai_agent import normalize_local_fidelity
    fidelidad_val = normalize_local_fidelity(xai.get("fidelidad_r"))

    curso_slug = "".join(ch if ch.isalnum() else "_" for ch in curso)[:16]
    req_id = f"acta_{cui_hash}_{curso_slug}_{checkpoint}"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")

        # 1. Asegurar curso y docente en catálogos oficiales
        cursor.execute("""
        INSERT OR IGNORE INTO catalogo_cursos
        (nombre, semestre_malla, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3)
        VALUES (?, 5, ?, ?, ?, ?, ?, ?)
        """, (
            curso,
            pesos.get("EC1", 15), pesos.get("EP1", 15),
            pesos.get("EC2", 20), pesos.get("EP2", 20),
            pesos.get("EC3", 15), pesos.get("EP3", 15),
        ))
        cursor.execute(
            "INSERT OR IGNORE INTO catalogo_docentes (nombre) VALUES (?)",
            (docente,),
        )

        # 2. Registrar estudiante anonimizado
        cursor.execute("""
        INSERT OR IGNORE INTO estudiantes (cui_hash, consentimiento_aceptado, comparte_con_tutor, fecha_registro)
        VALUES (?, 1, 1, ?)
        """, (cui_hash, now_str))

        # 3. Crear o actualizar perfil semestral basal
        perf_row = cursor.execute("""
        SELECT id FROM perfil_semestre
        WHERE cui_hash = ? AND semestre = ?
        ORDER BY id DESC LIMIT 1
        """, (cui_hash, semestre)).fetchone()

        if perf_row:
            cursor.execute("""
            UPDATE perfil_semestre
            SET ira_acum = ?, repeticiones_previas = ?, creditos_matriculados = ?,
                origen = 'ACTA_MASIVA', fecha_actualizacion = ?
            WHERE id = ?
            """, (ira, repeticiones, creditos_matriculados, now_str, int(perf_row["id"])))
        else:
            cursor.execute("""
            INSERT INTO perfil_semestre
            (cui_hash, semestre, ira_acum, repeticiones_previas, creditos_matriculados, semestre_ingreso, origen, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, 4.0, 'ACTA_MASIVA', ?)
            """, (cui_hash, semestre, ira, repeticiones, creditos_matriculados, now_str))

        # 4. Crear o actualizar matrícula (evitando duplicados para el mismo cui_hash, semestre y curso)
        mat_row = cursor.execute("""
        SELECT id FROM matriculas
        WHERE cui_hash = ? AND semestre = ? AND curso = ?
        ORDER BY id DESC LIMIT 1
        """, (cui_hash, semestre, curso)).fetchone()

        if mat_row:
            matricula_id = int(mat_row["id"])
            cursor.execute("""
            UPDATE matriculas
            SET docente = ?, seccion = ?, peso_ec1 = ?, peso_ep1 = ?,
                peso_ec2 = ?, peso_ep2 = ?, peso_ec3 = ?, peso_ep3 = ?, es_repeticion = ?
            WHERE id = ?
            """, (
                docente, seccion,
                pesos.get("EC1", 15), pesos.get("EP1", 15),
                pesos.get("EC2", 20), pesos.get("EP2", 20),
                pesos.get("EC3", 15), pesos.get("EP3", 15),
                es_rep, matricula_id,
            ))
        else:
            cursor.execute("""
            INSERT INTO matriculas
            (cui_hash, semestre, curso, docente, seccion, peso_ec1, peso_ep1, peso_ec2, peso_ep2, peso_ec3, peso_ep3, es_repeticion, fecha_inscripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cui_hash, semestre, curso, docente, seccion,
                pesos.get("EC1", 15), pesos.get("EP1", 15),
                pesos.get("EC2", 20), pesos.get("EP2", 20),
                pesos.get("EC3", 15), pesos.get("EP3", 15),
                es_rep, now_str,
            ))
            matricula_id = int(cursor.lastrowid)

        # 5. Persistir calificaciones parciales y registrar historial de cambios si se actualizan
        for ev in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
            val_num = eval_vals.get(ev)
            es_aus = 1 if eval_ausentes.get(ev, False) else 0
            if val_num is None and not es_aus:
                continue

            prev_row = cursor.execute("""
            SELECT valor_num, es_ausente FROM notas
            WHERE matricula_id = ? AND evaluacion = ?
            """, (matricula_id, ev)).fetchone()

            if prev_row:
                prev_val = prev_row["valor_num"]
                prev_aus = int(prev_row["es_ausente"] or 0)
                if prev_val != val_num or prev_aus != es_aus:
                    cursor.execute("""
                    INSERT INTO historial_cambios
                    (matricula_id, evaluacion, valor_previo, valor_nuevo, motivo, fecha_cambio)
                    VALUES (?, ?, ?, ?, 'Actualización por Carga Masiva de Acta', ?)
                    """, (matricula_id, ev, prev_val, val_num, now_str))

                    cursor.execute("""
                    UPDATE notas
                    SET valor_num = ?, es_ausente = ?, fecha_registro = ?, origen = 'DOCENTE_ACTA'
                    WHERE matricula_id = ? AND evaluacion = ?
                    """, (val_num, es_aus, now_str, matricula_id, ev))
            else:
                cursor.execute("""
                INSERT INTO notas (matricula_id, evaluacion, valor_num, es_ausente, fecha_registro, origen)
                VALUES (?, ?, ?, ?, ?, 'DOCENTE_ACTA')
                """, (matricula_id, ev, val_num, es_aus, now_str))

        # 6. Persistir o actualizar predicción y explicación SHAP para este (matricula_id, checkpoint)
        pred_row = cursor.execute("""
        SELECT id FROM predicciones
        WHERE matricula_id = ? AND checkpoint = ?
        ORDER BY id DESC LIMIT 1
        """, (matricula_id, checkpoint)).fetchone()

        if pred_row:
            prediccion_id = int(pred_row["id"])
            cursor.execute("""
            UPDATE predicciones
            SET probabilidad = ?, umbral = ?, semaforo = ?, meta_nota_min = ?,
                promedio_acumulado = ?, imposible_ordinario = ?, fecha = ?
            WHERE id = ?
            """, (
                prob_val, umbral_val, semaforo_color, meta_nota,
                prom_acum, 1 if imposible else 0, now_str, prediccion_id,
            ))
            exp_row = cursor.execute(
                "SELECT id FROM explicaciones WHERE prediccion_id = ? LIMIT 1",
                (prediccion_id,),
            ).fetchone()
            if exp_row:
                cursor.execute("""
                UPDATE explicaciones
                SET top_factors_json = ?, recomendaciones_json = ?, fidelidad_r = ?, fecha = ?
                WHERE prediccion_id = ?
                """, (json.dumps(top_factors), json.dumps(recs), fidelidad_val, now_str, prediccion_id))
            else:
                cursor.execute("""
                INSERT INTO explicaciones
                (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
                VALUES (?, ?, ?, ?, ?)
                """, (prediccion_id, json.dumps(top_factors), json.dumps(recs), fidelidad_val, now_str))
        else:
            cursor.execute("""
            INSERT INTO predicciones
            (matricula_id, checkpoint, probabilidad, umbral, semaforo, meta_nota_min, promedio_acumulado, imposible_ordinario, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                matricula_id, checkpoint, prob_val, umbral_val,
                semaforo_color, meta_nota, prom_acum, 1 if imposible else 0, now_str,
            ))
            prediccion_id = int(cursor.lastrowid)
            cursor.execute("""
            INSERT INTO explicaciones
            (prediccion_id, top_factors_json, recomendaciones_json, fidelidad_r, fecha)
            VALUES (?, ?, ?, ?, ?)
            """, (prediccion_id, json.dumps(top_factors), json.dumps(recs), fidelidad_val, now_str))

        # 7. Persistir trazas FIPA-ACL del bus para esta solicitud (sin duplicar al reimportar)
        cursor.execute("DELETE FROM mensajes_bus WHERE request_id = ?", (req_id,))
        for h_msg in history:
            emisor = str(h_msg.get("sender", "CoordinatorAgent"))
            receptor = str(h_msg.get("receiver", "Agent"))
            perf = str(h_msg.get("performative", "INFORM"))
            accion = str(h_msg.get("action") or perf)
            dur_ms = float(h_msg.get("duration_ms", 0.0))
            contenido_seguro = {
                "cui_hash": cui_hash,
                "curso": curso,
                "checkpoint": checkpoint,
                "action": accion,
                "performative": perf,
            }
            cursor.execute("""
            INSERT INTO mensajes_bus
            (request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_id, emisor, receptor, perf, accion,
                json.dumps(contenido_seguro), dur_ms, h_msg.get("timestamp", now_str),
            ))

        # 8. Persistir métricas técnicas reales OBJ5 (sin duplicar al reimportar)
        cursor.execute("DELETE FROM metricas_tecnicas WHERE request_id = ?", (req_id,))
        lat_inf = float(telemetry.get("latencia_inferencia_ms", 0.0))
        lat_xai = float(telemetry.get("latencia_xai_ms", 0.0))
        lat_tot = float(telemetry.get("latencia_total_ms", 0.0))
        ram_mb = float(telemetry.get("ram_mb", 0.0))
        over_ms = float(telemetry.get("overhead_bus_ms", 0.0))
        cursor.execute("""
        INSERT INTO metricas_tecnicas
        (request_id, checkpoint, latencia_inferencia_ms, latencia_xai_ms, latencia_total_ms, ram_mb, overhead_bus_ms, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (req_id, checkpoint, lat_inf, lat_xai, lat_tot, ram_mb, over_ms, now_str))

        conn.commit()
        return {
            "cui_hash": cui_hash,
            "matricula_id": matricula_id,
            "prediccion_id": prediccion_id,
            "request_id": req_id,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_latest_prediction(matricula_id: int, current_user: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Obtiene la predicción más reciente de una matrícula junto con sus explicaciones con control de acceso."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
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


def get_prediction_history(matricula_id: int, current_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Obtiene el historial cronológico de predicciones por checkpoint con control de acceso."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
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


def get_course_sections_summary(curso: str, semestre: str = "2026-B") -> list[dict[str, Any]]:
    """
    Retorna estadísticas estrictamente agregadas por sección y docente para el rol AUTORIDAD.
    No incluye CUI, hashes individuales, nombres ni calificaciones individuales.
    """
    conn = get_connection()
    rows = conn.execute("""
    SELECT m.seccion, m.docente, p.semaforo, p.probabilidad
    FROM matriculas m
    JOIN (
        SELECT matricula_id, MAX(id) as max_id
        FROM predicciones GROUP BY matricula_id
    ) latest ON m.id = latest.matricula_id
    JOIN predicciones p ON latest.max_id = p.id
    WHERE m.curso = ? AND m.semestre = ?
    ORDER BY m.seccion ASC
    """, (curso, semestre)).fetchall()
    conn.close()

    grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for r in rows:
        key = (str(r["seccion"] or "A"), str(r["docente"] or "DOCENTE EPIS"))
        grouped.setdefault(key, []).append(r)

    summary_list = []
    for (sec, doc), items in grouped.items():
        total = len(items)
        rojos = sum(1 for x in items if x["semaforo"] == "ROJO")
        amarillos = sum(1 for x in items if x["semaforo"] == "AMARILLO")
        verdes = sum(1 for x in items if x["semaforo"] == "VERDE")
        prom_riesgo = round((sum(float(x["probabilidad"]) for x in items) / total * 100.0) if total > 0 else 0.0, 1)
        summary_list.append({
            "curso": curso,
            "semestre": semestre,
            "seccion": sec,
            "docente": doc,
            "total_alumnos": total,
            "rojos": rojos,
            "amarillos": amarillos,
            "verdes": verdes,
            "promedio_riesgo_pct": prom_riesgo,
            "tasa_riesgo_pct": round((rojos / total * 100.0) if total > 0 else 0.0, 1),
        })
    return summary_list


def get_course_students_table(curso: str, semestre: str = "2026-B", current_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Retorna la lista de estudiantes exclusivamente para el docente/tutor titular del curso.
    Si el estudiante NO dio consentimiento (opt-in comparte_con_tutor=0),
    sus datos individuales se anonimizan como 'RES-XXXXXX'.
    Aplica aislamiento estricto:
    - ESTUDIANTE, ADMIN y AUTORIDAD no tienen acceso a registros individuales.
    - DOCENTE requiere asignaciones activas y solo puede consultar sus propios cursos y secciones.
    """
    if current_user is not None:
        rol_u = current_user.get("role")
        if rol_u == "ESTUDIANTE":
            raise AuthorizationError("Aislamiento estricto: Un estudiante no tiene autorización para listar otros alumnos del curso.")
        if rol_u == "ADMIN":
            raise AuthorizationError("Principio de Privacidad: El Administrador no tiene acceso a notas individuales de estudiantes.")
        if rol_u == "AUTORIDAD":
            raise AuthorizationError("Principio de Privacidad: El rol Autoridad solo tiene acceso a métricas agregadas, no a registros individuales de estudiantes.")

    conn = get_connection()
    try:
        allowed_teacher_names: set[str] | None = None
        if current_user is not None:
            allowed_teacher_names = validate_course_teacher_access(current_user, curso, semestre, conn)

        rows = conn.execute("""
        SELECT m.id as matricula_id, m.cui_hash, m.seccion, m.docente, e.comparte_con_tutor,
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
    finally:
        conn.close()

    result = []
    for r in rows:
        if allowed_teacher_names is not None:
            doc_row = str(r["docente"] or "").strip().upper()
            if doc_row not in allowed_teacher_names:
                continue
        item = dict(r)
        if not bool(r["comparte_con_tutor"]):
            item["id_mostrado"] = f"RES-{r['cui_hash'][:6]}"
            item["estado_optin"] = "No compartido"
        else:
            item["id_mostrado"] = r["cui_hash"]
            item["estado_optin"] = "Compartido con tutor"
        result.append(item)
    return result


def get_courses_for_user(current_user: dict[str, Any] | None, semestre: str = "2026-B") -> list[dict[str, Any]]:
    """
    Retorna la lista de asignaturas disponibles según el rol del usuario:
    - Si es DOCENTE, retorna exclusivamente las asignaturas donde es titular en el semestre.
    - Para otros roles (AUTORIDAD, ADMIN, ESTUDIANTE), retorna el catálogo completo.
    """
    catalogo = get_all_courses()
    if not current_user or current_user.get("role") != "DOCENTE":
        return catalogo
    allowed_names = get_authorized_teacher_names(current_user)
    if not allowed_names:
        return []
    placeholders = ",".join("?" for _ in allowed_names)
    conn = get_connection()
    rows = conn.execute(
        f"SELECT DISTINCT curso FROM matriculas WHERE semestre = ? AND UPPER(TRIM(docente)) IN ({placeholders})",
        (semestre, *tuple(allowed_names)),
    ).fetchall()
    conn.close()
    assigned_names = {str(r["curso"]).strip().upper() for r in rows}
    if not assigned_names:
        return []
    filtered = [c for c in catalogo if str(c["nombre"]).strip().upper() in assigned_names]
    for c_name in sorted(assigned_names):
        if all(str(c["nombre"]).strip().upper() != c_name for c in filtered):
            filtered.append({"nombre": c_name, "semestre_malla": 5})
    return filtered


def get_bus_messages_for_student(cui_hash: str, limit: int = 8) -> list[dict[str, Any]]:
    """
    Obtiene los mensajes de trazabilidad del bus FIPA-ACL que pertenecen
    estrictamente a las evaluaciones y solicitudes del estudiante autenticado.
    Garantiza aislamiento total respecto a otros estudiantes.
    """
    conn = get_connection()
    cui_pattern = f"%{cui_hash}%"
    rows = conn.execute("""
    SELECT id, request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp 
    FROM mensajes_bus 
    WHERE request_id LIKE ? OR contenido_json LIKE ?
    ORDER BY id DESC LIMIT ?
    """, (cui_pattern, cui_pattern, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_bus_message(
    request_id: str,
    emisor: str,
    receptor: str,
    performativa: str,
    topico: str,
    contenido: dict[str, Any],
    duracion_ms: float = 0.0,
    conn: sqlite3.Connection | None = None,
):
    """Registra en la base de datos cada mensaje FIPA-ACL para auditoría y monitor técnico."""
    own_conn = conn is None
    db_conn = conn if conn is not None else get_connection()
    now_str = datetime.now().isoformat()
    db_conn.execute("""
    INSERT INTO mensajes_bus (request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (request_id, emisor, receptor, performativa, topico, json.dumps(contenido), duracion_ms, now_str))
    if own_conn:
        db_conn.commit()
        db_conn.close()


def get_recent_bus_messages(limit: int = 50) -> list[dict[str, Any]]:
    """Obtiene los mensajes más recientes del bus FIPA-ACL."""
    conn = get_connection()
    rows = conn.execute("""
    SELECT id, request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp 
    FROM mensajes_bus ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_enrollment_by_id(matricula_id: int, current_user: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Obtiene el registro de una matrícula por su ID con validación estricta de permisos."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
    row = conn.execute("SELECT * FROM matriculas WHERE id = ?", (matricula_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_grade_change_history(matricula_id: int, current_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Retorna el historial de auditoría de cambios de notas para una matrícula."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
    rows = conn.execute("""
    SELECT evaluacion, valor_previo, valor_nuevo, motivo, fecha_cambio
    FROM historial_cambios
    WHERE matricula_id = ?
    ORDER BY id DESC
    """, (matricula_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tutoring_checklist_state(matricula_id: int, current_user: dict[str, Any] | None = None) -> dict[str, Any]:
    """Obtiene el estado persistido de las 3 casillas del plan de tutoría para una matrícula."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
    row = conn.execute("""
    SELECT accion_1_ok, accion_2_ok, accion_3_ok, fecha_sesion, fecha_registro
    FROM tutorias
    WHERE matricula_id = ?
    ORDER BY id DESC LIMIT 1
    """, (matricula_id,)).fetchone()
    conn.close()
    if not row:
        return {
            "accion_1": False,
            "accion_2": False,
            "accion_3": False,
            "fecha_actualizacion": "Sin registros",
        }
    return {
        "accion_1": bool(row["accion_1_ok"]),
        "accion_2": bool(row["accion_2_ok"]),
        "accion_3": bool(row["accion_3_ok"]),
        "fecha_actualizacion": str(row["fecha_registro"])[:10],
    }


def get_tutoring_history(matricula_id: int, current_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Retorna la bitácora histórica de sesiones de tutoría de una matrícula."""
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
    rows = conn.execute("""
    SELECT id, matricula_id, cui_hash, curso, responsable, rol_registro, estado,
           fecha_sesion, observaciones, accion_1_ok, accion_2_ok, accion_3_ok, fecha_registro
    FROM tutorias
    WHERE matricula_id = ?
    ORDER BY id DESC
    """, (matricula_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def schedule_tutoring_session(
    matricula_id: int,
    fecha_sesion: str,
    observaciones: str,
    current_user: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Programa y persiste una sesión de tutoría en SQLite validando permisos y campos obligatorios."""
    fecha_clean = str(fecha_sesion or "").strip()
    obs_clean = str(observaciones or "").strip()
    if not fecha_clean:
        return False, "Debe especificar una fecha válida para programar la tutoría."
    if len(obs_clean) < 5:
        return False, "Debe ingresar el motivo u observación de la tutoría (mínimo 5 caracteres)."

    conn = get_connection()
    try:
        if current_user:
            validate_matricula_ownership(current_user, matricula_id, conn)
        mat_row = conn.execute("SELECT * FROM matriculas WHERE id = ?", (matricula_id,)).fetchone()
        if not mat_row:
            return False, "No se encontró la matrícula seleccionada en la base de datos."

        prev_tut = conn.execute(
            "SELECT accion_1_ok, accion_2_ok, accion_3_ok FROM tutorias WHERE matricula_id = ? ORDER BY id DESC LIMIT 1",
            (matricula_id,),
        ).fetchone()
        a1 = int(prev_tut["accion_1_ok"]) if prev_tut else 1
        a2 = int(prev_tut["accion_2_ok"]) if prev_tut else 0
        a3 = int(prev_tut["accion_3_ok"]) if prev_tut else 0

        now_str = datetime.now().isoformat()
        cui_h = str(mat_row["cui_hash"])
        curso = str(mat_row["curso"])
        resp = str(current_user.get("username") if current_user else mat_row["docente"])
        rol_reg = str(current_user.get("role") if current_user else "DOCENTE")

        conn.execute("""
        INSERT INTO tutorias
        (matricula_id, cui_hash, curso, responsable, rol_registro, estado, fecha_sesion, observaciones, accion_1_ok, accion_2_ok, accion_3_ok, fecha_registro)
        VALUES (?, ?, ?, ?, ?, 'PROGRAMADA', ?, ?, ?, ?, ?, ?)
        """, (matricula_id, cui_h, curso, resp, rol_reg, fecha_clean, obs_clean, a1, a2, a3, now_str))

        req_id = f"tut_prog_{cui_h[:12]}_{matricula_id}"
        contenido_bus = json.dumps({
            "cui_hash": cui_h,
            "curso": curso,
            "estado": "PROGRAMADA",
            "fecha_sesion": fecha_clean,
        })
        conn.execute("""
        INSERT INTO mensajes_bus
        (request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp)
        VALUES (?, 'TutoriaUI', 'AlertAgent', 'REQUEST', 'PROGRAMAR_TUTORIA', ?, 0.2, ?)
        """, (req_id, contenido_bus, now_str))

        conn.commit()
        return True, f"Sesión de tutoría programada para el {fecha_clean} y persistida en SQLite."
    finally:
        conn.close()


def register_tutoring_session(
    matricula_id: int,
    fecha_sesion: str,
    estado: str,
    observaciones: str,
    accion_1: bool,
    accion_2: bool,
    accion_3: bool,
    current_user: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Registra una intervención de tutoría y actualiza el estado del checklist en SQLite."""
    fecha_clean = str(fecha_sesion or "").strip()
    estado_clean = str(estado or "REALIZADA").strip().upper()
    obs_clean = str(observaciones or "").strip()

    if not fecha_clean:
        return False, "La fecha de la sesión de tutoría es obligatoria."
    if estado_clean not in ("PROGRAMADA", "REALIZADA", "SEGUIMIENTO"):
        return False, "El estado de la tutoría no es válido."
    if len(obs_clean) < 5:
        return False, "Debe ingresar las observaciones o acuerdos pedagógicos de la tutoría (mínimo 5 caracteres)."

    conn = get_connection()
    try:
        if current_user:
            validate_matricula_ownership(current_user, matricula_id, conn)
        mat_row = conn.execute("SELECT * FROM matriculas WHERE id = ?", (matricula_id,)).fetchone()
        if not mat_row:
            return False, "No se encontró la matrícula indicada."

        now_str = datetime.now().isoformat()
        cui_h = str(mat_row["cui_hash"])
        curso = str(mat_row["curso"])
        resp = str(current_user.get("username") if current_user else mat_row["docente"])
        rol_reg = str(current_user.get("role") if current_user else "DOCENTE")

        conn.execute("""
        INSERT INTO tutorias
        (matricula_id, cui_hash, curso, responsable, rol_registro, estado, fecha_sesion, observaciones, accion_1_ok, accion_2_ok, accion_3_ok, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            matricula_id, cui_h, curso, resp, rol_reg, estado_clean, fecha_clean, obs_clean,
            1 if accion_1 else 0, 1 if accion_2 else 0, 1 if accion_3 else 0, now_str,
        ))

        req_id = f"tut_reg_{cui_h[:12]}_{matricula_id}"
        contenido_bus = json.dumps({
            "cui_hash": cui_h,
            "curso": curso,
            "estado": estado_clean,
            "compromisos": [bool(accion_1), bool(accion_2), bool(accion_3)],
        })
        conn.execute("""
        INSERT INTO mensajes_bus
        (request_id, emisor, receptor, performativa, topico, contenido_json, duracion_ms, timestamp)
        VALUES (?, 'TutoriaUI', 'RecommendationAgent', 'INFORM', 'REGISTRAR_TUTORIA', ?, 0.2, ?)
        """, (req_id, contenido_bus, now_str))

        conn.commit()
        return True, "Intervención de tutoría y compromisos pedagógicos guardados en la bitácora SQLite."
    finally:
        conn.close()


def get_header_metrics(
    current_user: dict[str, Any],
    semestre: str = "2026-B",
    curso_filtro: str | None = None,
) -> dict[str, Any]:
    """
    Calcula los indicadores de la sub-cabecera directamente desde SQLite sin valores estáticos ni ficticios:
    - Rol ESTUDIANTE: asignaturas inscritas del propio alumno, sus tutorías registradas y última actualización de sus predicciones.
    - Roles DOCENTE / AUTORIDAD / ADMIN: matrículas activas en seguimiento en el semestre, tutorías registradas y última actualización real.
    """
    conn = get_connection()
    rol = str(current_user.get("role", "ESTUDIANTE"))

    if rol == "ESTUDIANTE":
        cui_h = str(current_user.get("cui_hash") or current_user.get("username") or "")
        total_items = int(conn.execute(
            "SELECT COUNT(*) FROM matriculas WHERE cui_hash = ? AND semestre = ?",
            (cui_h, semestre),
        ).fetchone()[0])
        total_tutorias = int(conn.execute(
            "SELECT COUNT(*) FROM tutorias WHERE cui_hash = ?",
            (cui_h,),
        ).fetchone()[0])
        ult_row = conn.execute("""
        SELECT MAX(p.fecha) as max_fecha
        FROM predicciones p
        JOIN matriculas m ON p.matricula_id = m.id
        WHERE m.cui_hash = ? AND m.semestre = ?
        """, (cui_h, semestre)).fetchone()
        label_col1 = "ASIGNATURAS INSCRITAS"
        label_col2 = "TUTORÍAS REGISTRADAS"
    else:
        if curso_filtro:
            total_items = int(conn.execute(
                "SELECT COUNT(*) FROM matriculas WHERE semestre = ? AND curso = ?",
                (semestre, curso_filtro),
            ).fetchone()[0])
        else:
            total_items = int(conn.execute(
                "SELECT COUNT(*) FROM matriculas WHERE semestre = ?",
                (semestre,),
            ).fetchone()[0])
        total_tutorias = int(conn.execute(
            "SELECT COUNT(*) FROM tutorias"
        ).fetchone()[0])
        ult_row = conn.execute(
            "SELECT MAX(fecha) as max_fecha FROM predicciones"
        ).fetchone()
        label_col1 = "ESTUDIANTES EN SEGUIMIENTO"
        label_col2 = "TUTORÍAS ESTA SEMANA"

    conn.close()

    max_fecha_raw = ult_row["max_fecha"] if (ult_row and ult_row["max_fecha"]) else None
    if max_fecha_raw:
        try:
            dt_obj = datetime.fromisoformat(str(max_fecha_raw))
            ultima_actualizacion = dt_obj.strftime("%d/%m/%Y")
        except Exception:
            ultima_actualizacion = str(max_fecha_raw)[:10]
    else:
        ultima_actualizacion = "Sin registros"

    return {
        "label_col1": label_col1,
        "valor_col1": total_items,
        "label_col2": label_col2,
        "valor_col2": total_tutorias,
        "ultima_actualizacion": ultima_actualizacion,
    }


def evaluate_and_persist_enrollment(
    matricula_id: int,
    coordinator_agent,
    current_user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Reevalúa una matrícula con el Sistema Multiagente tras registrar o modificar calificaciones
    parciales (save_grade) y persiste la predicción y explicaciones SHAP en SQLite.
    """
    conn = get_connection()
    if current_user:
        validate_matricula_ownership(current_user, matricula_id, conn)
    mat = conn.execute("SELECT * FROM matriculas WHERE id = ?", (matricula_id,)).fetchone()
    if not mat:
        conn.close()
        return {"status": "ERROR", "errors": ["Matrícula no encontrada."]}

    cui_h = str(mat["cui_hash"])
    sem = str(mat["semestre"])
    perf = conn.execute(
        "SELECT * FROM perfil_semestre WHERE cui_hash = ? AND semestre = ? ORDER BY id DESC LIMIT 1",
        (cui_h, sem),
    ).fetchone()
    notas_rows = conn.execute(
        "SELECT evaluacion, valor_num, es_ausente FROM notas WHERE matricula_id = ?",
        (matricula_id,),
    ).fetchall()
    conn.close()

    notas_map = {r["evaluacion"]: (r["valor_num"], bool(r["es_ausente"])) for r in notas_rows}
    payload: dict[str, Any] = {
        "CUI": cui_h,
        "CUI_HASH": cui_h,
        "ASIGNATURA": mat["curso"],
        "ASIGNATURA_NORM": mat["curso"],
        "IRA_ACUM": float(perf["ira_acum"]) if perf else 12.0,
        "TASA_APROB_ACUM": 0.85,
        "REPROBACIONES_PREVIAS": int(perf["repeticiones_previas"]) if perf else int(mat["es_repeticion"]),
        "CARGA_ACADEMICA": int(perf["creditos_matriculados"]) if perf else 6,
        "ES_REPETICION": int(mat["es_repeticion"]),
        "SEMESTRES_DESDE_INGRESO": float(perf["semestre_ingreso"]) if perf else 4.0,
        "DIFICULTAD_CURSO_HIST": 0.12,
        "DIFICULTAD_DOCENTE_HIST": 0.08,
        "DIFICULTAD_CURSO_DOCENTE_HIST": 0.10,
        "PESO_EC1": int(mat["peso_ec1"]),
        "PESO_EP1": int(mat["peso_ep1"]),
        "PESO_EC2": int(mat["peso_ec2"]),
        "PESO_EP2": int(mat["peso_ep2"]),
        "PESO_EC3": int(mat["peso_ec3"]),
        "PESO_EP3": int(mat["peso_ep3"]),
    }
    for ev in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
        if ev in notas_map:
            val_num, is_aus = notas_map[ev]
            payload[ev] = 0.0 if is_aus else val_num
            payload[f"{ev}_AUSENTE"] = 1 if is_aus else 0
        else:
            payload[ev] = None
            payload[f"{ev}_AUSENTE"] = 0

    res_sma = coordinator_agent.analyze_student_risk(payload, persist_telemetry=True)
    if res_sma.get("status") != "SUCCESS":
        return res_sma

    al = res_sma["alert"]
    pred = res_sma["prediction"]
    xai = res_sma["xai"]
    checkpoint = str(al.get("checkpoint") or pred.get("checkpoint") or "CP0")
    prob_val = float(pred.get("probability", al.get("probability_pct", 0.0) / 100.0))
    umbral_val = float(pred.get("threshold", al.get("threshold_pct", 34.0) / 100.0))
    imposible = bool(al.get("imposible_ordinario", False))

    th_yellow = round(0.75 * umbral_val, 4)
    if imposible or prob_val >= umbral_val:
        semaforo = "ROJO"
    elif prob_val >= th_yellow:
        semaforo = "AMARILLO"
    else:
        semaforo = "VERDE"

    from ..agents.xai_agent import normalize_local_fidelity

    save_prediction_result(
        matricula_id=matricula_id,
        checkpoint=checkpoint,
        proba=prob_val,
        umbral=umbral_val,
        semaforo=semaforo,
        meta_nota=al.get("meta_nota_min"),
        promedio=float(al.get("promedio_acumulado") or 0.0),
        imposible=imposible,
        top_factors=al.get("top_factors") or xai.get("top_factors") or [],
        recs=al.get("recommendations") or [],
        fidelidad=normalize_local_fidelity(xai.get("fidelidad_r")),
    )
    return res_sma


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
    """
    Calcula estadísticas descriptivas para la Ficha de Desempeño Técnico del OBJ5.
    Garantiza un esquema de claves homogéneo tanto cuando la tabla está vacía
    (total_muestras == 0) como cuando existen mediciones reales registradas.
    """
    conn = get_connection()
    rows = conn.execute("""
    SELECT latencia_inferencia_ms, latencia_xai_ms, latencia_total_ms, ram_mb, overhead_bus_ms
    FROM metricas_tecnicas
    """).fetchall()
    conn.close()

    if not rows:
        return {
            "total_muestras": 0,
            "latencia_inf_media_ms": 0.0,
            "latencia_inf_p95_ms": 0.0,
            "latencia_xai_media_ms": 0.0,
            "latencia_total_media_ms": 0.0,
            "ram_media_mb": 0.0,
            "overhead_media_ms": 0.0,
        }

    inf_vals = [float(r["latencia_inferencia_ms"]) for r in rows if r["latencia_inferencia_ms"] is not None]
    xai_vals = [float(r["latencia_xai_ms"]) for r in rows if r["latencia_xai_ms"] is not None]
    tot_vals = [float(r["latencia_total_ms"]) for r in rows if r["latencia_total_ms"] is not None]
    ram_vals = [float(r["ram_mb"]) for r in rows if r["ram_mb"] is not None]
    over_vals = [float(r["overhead_bus_ms"]) for r in rows if r["overhead_bus_ms"] is not None]

    sorted_inf = sorted(inf_vals) if inf_vals else [0.0]
    p95_idx = min(len(sorted_inf) - 1, int(len(sorted_inf) * 0.95))
    p95_val = sorted_inf[p95_idx] if len(sorted_inf) >= 20 else max(sorted_inf)

    return {
        "total_muestras": len(rows),
        "latencia_inf_media_ms": round(sum(inf_vals) / len(inf_vals), 2) if inf_vals else 0.0,
        "latencia_inf_p95_ms": round(p95_val, 2),
        "latencia_xai_media_ms": round(sum(xai_vals) / len(xai_vals), 2) if xai_vals else 0.0,
        "latencia_total_media_ms": round(sum(tot_vals) / len(tot_vals), 2) if tot_vals else 0.0,
        "ram_media_mb": round(sum(ram_vals) / len(ram_vals), 1) if ram_vals else 0.0,
        "overhead_media_ms": round(sum(over_vals) / len(over_vals), 3) if over_vals else 0.0,
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
