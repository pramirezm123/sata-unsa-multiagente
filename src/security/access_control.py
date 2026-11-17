"""
Módulo de Control de Acceso y Aislamiento de Datos por Rol (SATA-UNSA).
Garantiza que ningún estudiante pueda consultar, inferir ni manipular datos
de otros estudiantes en ninguna capa del sistema (UI, Servicios o Persistencia).
"""
import sqlite3
from typing import Any


class AuthorizationError(PermissionError):
    """Excepción lanzada ante intentos de acceso no autorizado o violación de aislamiento."""


# Mapeo canónico de cuentas de demostración de docentes a su nombre titular en actas/matrículas
DOCENTE_ALIASES: dict[str, set[str]] = {
    "DOCENTE_DEMO": {"DOCENTE_DEMO", "DOCENTE PRINCIPAL 1"},
    "DOCENTE_EPIS": {"DOCENTE_EPIS", "DOCENTE TITULAR EPIS"},
}


def get_authorized_teacher_names(current_user: dict[str, Any] | None) -> set[str]:
    """
    Retorna el conjunto normalizado (UPPER) de identificadores de docente asociados
    al usuario autenticado con rol DOCENTE. Aplica denegación por defecto si el rol
    no es DOCENTE o no posee identificador válido.
    """
    if not current_user or current_user.get("role") != "DOCENTE":
        return set()
    raw_uname = str(current_user.get("username") or "").strip().upper()
    if not raw_uname:
        return set()
    names = set(DOCENTE_ALIASES.get(raw_uname, {raw_uname}))
    extra_doc = str(current_user.get("docente") or current_user.get("nombre_docente") or "").strip().upper()
    if extra_doc:
        names.add(extra_doc)
    return names


def validate_course_teacher_access(
    current_user: dict[str, Any] | None,
    curso: str,
    semestre: str,
    conn: sqlite3.Connection,
) -> set[str]:
    """
    Verifica que el docente autenticado tenga asignaciones activas y que no intente
    acceder a una asignatura cuyas matrículas pertenezcan exclusivamente a otro docente.
    Retorna los identificadores normalizados del docente autorizado.
    """
    if current_user is None:
        raise AuthorizationError("Acceso no autorizado: Sesión no autenticada.")

    rol = current_user.get("role")
    if rol != "DOCENTE":
        raise AuthorizationError(
            f"Acceso denegado: El rol '{rol}' no está autorizado para consultar nóminas docentes de curso."
        )

    allowed_names = get_authorized_teacher_names(current_user)
    if not allowed_names:
        raise AuthorizationError("Acceso denegado: Docente sin identificador válido.")

    placeholders = ",".join("?" for _ in allowed_names)
    params_names = tuple(allowed_names)

    # 1. Verificar que el docente tenga al menos una asignación registrada en el sistema
    total_own = conn.execute(
        f"SELECT COUNT(*) FROM matriculas WHERE UPPER(TRIM(docente)) IN ({placeholders})",
        params_names,
    ).fetchone()[0]
    if total_own == 0:
        raise AuthorizationError(
            f"Acceso denegado: El docente '{current_user.get('username')}' no tiene cursos ni matrículas asignadas."
        )

    # 2. Verificar titularidad sobre la asignatura solicitada en el semestre
    curso_clean = str(curso or "").strip()
    sem_clean = str(semestre or "2026-B").strip()
    rows_curso = conn.execute(
        "SELECT docente FROM matriculas WHERE curso = ? AND semestre = ?",
        (curso_clean, sem_clean),
    ).fetchall()

    if rows_curso:
        own_in_course = sum(
            1 for r in rows_curso if str(r["docente"] or "").strip().upper() in allowed_names
        )
        if own_in_course == 0:
            raise AuthorizationError(
                f"Violación de aislamiento docente: El docente '{current_user.get('username')}' "
                f"intentó acceder al curso '{curso_clean}', el cual está asignado a otro docente."
            )

    return allowed_names


def validate_student_access(current_user: dict[str, Any] | None, target_cui_hash: str) -> None:
    """
    Verifica que si el usuario autenticado tiene rol ESTUDIANTE, solo pueda
    acceder a registros con su propio cui_hash.
    Impide que ADMIN y AUTORIDAD consulten registros individuales de estudiantes.
    """
    if current_user is None:
        raise AuthorizationError("Acceso no autorizado: No existe sesión de usuario activa.")

    rol = current_user.get("role")
    user_hash = current_user.get("cui_hash")

    if rol == "ESTUDIANTE" and (not user_hash or user_hash != target_cui_hash):
        raise AuthorizationError(
            f"Violación de aislamiento de datos: El estudiante '{user_hash}' "
            f"intentó acceder a información del estudiante '{target_cui_hash}'."
        )
    if rol in ("ADMIN", "AUTORIDAD"):
        raise AuthorizationError(
            f"Principio de Privacidad: El rol '{rol}' no tiene acceso a registros individuales de estudiantes."
        )


def validate_matricula_ownership(current_user: dict[str, Any] | None, matricula_id: int, conn: sqlite3.Connection) -> dict[str, Any]:
    """
    Verifica que la matrícula solicitada pertenezca al estudiante autenticado.
    Si el rol es DOCENTE, verifica que el curso/sección esté a su cargo.
    Impide que ADMIN y AUTORIDAD accedan a matrículas o notas individuales.
    Retorna los datos de la matrícula si es válida.
    """
    if current_user is None:
        raise AuthorizationError("Acceso no autorizado: Sesión no autenticada.")

    rol = current_user.get("role")
    if rol in ("ADMIN", "AUTORIDAD"):
        raise AuthorizationError(
            f"Principio de Privacidad: El rol '{rol}' no tiene autorización para consultar matrículas o calificaciones individuales."
        )

    row = conn.execute("SELECT * FROM matriculas WHERE id = ?", (matricula_id,)).fetchone()
    if not row:
        raise KeyError(f"La matrícula con ID {matricula_id} no existe.")

    mat_dict = dict(row)
    user_hash = current_user.get("cui_hash")
    username = current_user.get("username")

    if rol == "ESTUDIANTE":
        if mat_dict["cui_hash"] != user_hash:
            raise AuthorizationError(
                f"Violación de aislamiento: La matrícula {matricula_id} no pertenece al estudiante autenticado."
            )
    elif rol == "DOCENTE":
        allowed_names = get_authorized_teacher_names(current_user)
        docente_mat = str(mat_dict.get("docente") or "").strip().upper()
        if not allowed_names or docente_mat not in allowed_names:
            raise AuthorizationError(
                f"Violación de aislamiento docente: El docente '{username}' no tiene asignada "
                f"la matrícula {matricula_id} (pertenece a '{mat_dict.get('docente')}')."
            )
    else:
        raise AuthorizationError(
            f"Acceso denegado: El rol '{rol}' no tiene autorización para acceder a la matrícula {matricula_id}."
        )

    return mat_dict


ROLE_AUTHORIZED_VIEWS: dict[str, list[str]] = {
    "ESTUDIANTE": [
        "Panel de seguimiento",
        "Detalle con explicabilidad",
        "Trazabilidad multiagente",
        "Seguimiento y plan de tutoría",
        "Inscribir Asignatura",
        "Perfil Basal",
    ],
    "DOCENTE": [
        "Panel de seguimiento",
        "Detalle con explicabilidad",
        "Trazabilidad multiagente",
        "Seguimiento y plan de tutoría",
        "Carga Masiva de Actas",
    ],
    "AUTORIDAD": [
        "Panel de seguimiento",
        "Métricas Institucionales",
        "Trazabilidad multiagente",
    ],
    "ADMIN": [
        "Panel de seguimiento",
        "Monitor Técnico OBJ5",
        "Trazabilidad multiagente",
        "Encuestas SUS / TAM",
    ],
}


def can_access_view(role: str, view_name: str) -> bool:
    """Verifica si un rol está autorizado para acceder a una vista determinada."""
    return view_name in ROLE_AUTHORIZED_VIEWS.get(role, [])


def require_role(current_user: dict[str, Any] | None, allowed_roles: list[str]) -> None:
    """Verifica que el usuario pertenezca a uno de los roles permitidos."""
    if current_user is None:
        raise AuthorizationError("Acceso no autorizado: Sesión requerida.")
    if current_user.get("role") not in allowed_roles:
        raise AuthorizationError(
            f"Acceso denegado: El rol '{current_user.get('role')}' no tiene privilegios para esta acción."
        )
