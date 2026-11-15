"""
Módulo de Seguridad y Criptografía para SATA-UNSA.
Cumple estrictamente con el principio de 'Privacidad por Diseño':
- Hashing de CUI con HMAC-SHA256 y sal/clave secreta del sistema (evita ataques de diccionario).
- Hashing de contraseñas con PBKDF2-HMAC-SHA256 con sal aleatoria única por usuario.
"""
import hashlib
import hmac
import os
import secrets

# Archivo de sal secreta del sistema (almacenado localmente, fuera del control de versiones público)
SECRET_SALT_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".salt_secret")

def _get_or_create_system_salt() -> bytes:
    """Obtiene o genera la sal secreta persistente para el HMAC de CUIs."""
    if os.path.exists(SECRET_SALT_FILE):
        with open(SECRET_SALT_FILE, "rb") as f:
            secret = f.read().strip()
            if secret:
                return secret
    # Si no existe, se genera una clave criptográfica de 32 bytes
    new_secret = secrets.token_bytes(32)
    with open(SECRET_SALT_FILE, "wb") as f:
        f.write(new_secret)
    return new_secret

SYSTEM_SALT = _get_or_create_system_salt()


def hash_cui(cui: str, salt: bytes | None = None) -> str:
    """
    Genera un hash irreversible para el CUI utilizando HMAC-SHA256 con sal secreta.
    Retorna los primeros 16 caracteres hexadecimales (suficiente para colisiones en ~30,000 alumnos).
    Permite parametrizar la sal opcionalmente para pruebas de variabilidad criptográfica.
    """
    clean_cui = str(cui).strip().upper()
    active_salt = salt if salt is not None else SYSTEM_SALT
    h = hmac.new(active_salt, clean_cui.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()[:16].upper()


def ensure_cui_hash(raw_id: str) -> str:
    """
    Garantiza que cualquier identificador de estudiante se encuentre anonimizado
    con HMAC-SHA256 (16 caracteres hexadecimales en mayúsculas).
    Si el identificador ya es un hash hexadecimal válido de 16 caracteres, lo conserva;
    en caso contrario aplica hash_cui().
    """
    clean = str(raw_id or "").strip().upper()
    if len(clean) == 16 and all(c in "0123456789ABCDEF" for c in clean):
        return clean
    return hash_cui(clean)


def hash_password(password: str) -> str:
    """
    Genera un hash seguro para la contraseña usando PBKDF2-HMAC-SHA256 con sal aleatoria.
    Formato retornado: 'pbkdf2:sha256:100000$salt_hex$hash_hex'
    """
    salt = secrets.token_bytes(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    try:
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False
        meta, salt_hex, hash_hex = parts
        iterations = int(meta.split(":")[-1])
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(derived, expected_hash)
    except Exception:
        return False
