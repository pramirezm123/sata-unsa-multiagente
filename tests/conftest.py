"""
Configuración global de fixtures para la suite de pruebas SATA-UNSA.
Garantiza aislamiento de base de datos, inicialización de bus y fixtures reutilizables.
"""
import os
import sys
import tempfile

import pandas as pd
import pytest

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Redirigir SATA_DB_PATH antes de importar src.database.db para que la importación
# inicial jamás escriba sobre la base de datos institucional sata_unsa.db
_BOOT_TEST_DIR = tempfile.mkdtemp(prefix="sata_boot_test_")
os.environ.setdefault("SATA_DB_PATH", os.path.join(_BOOT_TEST_DIR, "sata_boot.db"))

from src.agents.coordinator_agent import CoordinatorAgent
from src.messaging.bus import MessageBus


@pytest.fixture(scope="session", autouse=True)
def isolated_test_database(tmp_path_factory):
    """
    Redirige DB_PATH a una base de datos SQLite temporal aislada durante toda la
    ejecución de pytest para no contaminar la base de datos institucional sata_unsa.db.
    """
    import src.database.db as db_mod

    original_db_path = db_mod.DB_PATH
    temp_dir = tmp_path_factory.mktemp("sata_test_db")
    test_db_path = os.path.join(str(temp_dir), "sata_unsa_test.db")
    db_mod.DB_PATH = test_db_path
    db_mod.init_database()
    db_mod.seed_initial_data()
    yield test_db_path
    db_mod.DB_PATH = original_db_path


@pytest.fixture(scope="session")
def models_dir():
    """Ruta del directorio de modelos serializados."""
    return os.path.join(BASE_DIR, "04_Modelo")


@pytest.fixture(scope="function")
def fresh_bus():
    """Instancia limpia de MessageBus."""
    return MessageBus()


@pytest.fixture(scope="function")
def coordinator(fresh_bus, models_dir):
    """Instancia del Coordinador Multiagente con bus limpio."""
    return CoordinatorAgent("CoordinatorAgent", fresh_bus, models_dir)


@pytest.fixture(scope="session")
def val_dataset():
    """Carga el dataset de validación 2023 (N=2,749, 230 reprobados)."""
    val_path = os.path.join(BASE_DIR, "03_Datasets", "checkpoint_val.csv")
    if os.path.exists(val_path):
        return pd.read_csv(val_path)
    return None


@pytest.fixture(scope="session")
def test_dataset():
    """Carga el dataset de prueba 2024-2025 (N=4,948, 312 reprobados)."""
    test_path = os.path.join(BASE_DIR, "03_Datasets", "checkpoint_test.csv")
    if os.path.exists(test_path):
        return pd.read_csv(test_path)
    return None


@pytest.fixture(scope="function")
def sample_payload_cp0():
    """Payload de estudiante en Checkpoint 0 (solo historial basal)."""
    return {
        "CUI": "20230001",
        "ASIGNATURA": "ESTRUCTURAS DE DATOS Y ALGORITMOS",
        "ASIGNATURA_NORM": "ESTRUCTURAS DE DATOS Y ALGORITMOS",
        "IRA_ACUM": 13.5,
        "TASA_APROB_ACUM": 0.90,
        "REPROBACIONES_PREVIAS": 0,
        "CARGA_ACADEMICA": 6,
        "ES_REPETICION": 0,
        "SEMESTRES_DESDE_INGRESO": 4.0,
        "DIFICULTAD_CURSO_HIST": 0.10,
        "DIFICULTAD_DOCENTE_HIST": 0.08,
        "DIFICULTAD_CURSO_DOCENTE_HIST": 0.09,
        "EC1": None, "EP1": None,
        "EC2": None, "EP2": None,
        "EC3": None, "EP3": None,
        "PESO_EC1": 15.0, "PESO_EP1": 15.0,
        "PESO_EC2": 20.0, "PESO_EP2": 20.0,
        "PESO_EC3": 15.0, "PESO_EP3": 15.0
    }


@pytest.fixture(scope="function")
def sample_payload_cp1(sample_payload_cp0):
    """Payload de estudiante en Checkpoint 1 (Fase 1 completada con bajo rendimiento)."""
    p = sample_payload_cp0.copy()
    p["EC1"] = 8.0
    p["EP1"] = 7.0
    p["IRA_ACUM"] = 10.8
    p["REPROBACIONES_PREVIAS"] = 2
    p["ES_REPETICION"] = 1
    return p


@pytest.fixture(scope="function")
def sample_payload_cp2(sample_payload_cp1):
    """Payload de estudiante en Checkpoint 2 (Fase 1 y 2 completadas)."""
    p = sample_payload_cp1.copy()
    p["EC2"] = 9.0
    p["EP2"] = 8.0
    return p


@pytest.fixture(scope="function")
def sample_payload_cp3(sample_payload_cp2):
    """Payload de estudiante en Checkpoint 3 (Todas las fases completadas)."""
    p = sample_payload_cp2.copy()
    p["EC3"] = 10.0
    p["EP3"] = 9.0
    return p
