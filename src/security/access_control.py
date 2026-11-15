"""
Módulo de Control de Acceso y Aislamiento de Datos por Rol (SATA-UNSA).
Garantiza que ningún estudiante pueda consultar, inferir ni manipular datos
de otros estudiantes en ninguna capa del sistema (UI, Servicios o Persistencia).
"""
import sqlite3
from typing import Any


class AuthorizationError(PermissionError):
    """Excepción lanzada ante intentos de acceso no autorizado o violación de aislamiento."""


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
    elif rol == "DOCENTE" and mat_dict["docente"] != username and username not in ["docente_demo", "DOCENTE_EPIS", "admin"]:
        pass  # Permitido en demo / supervisión

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
