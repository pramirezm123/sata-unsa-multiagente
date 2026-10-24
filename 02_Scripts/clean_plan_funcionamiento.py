"""
Limpieza y consolidación de reportes 'reporte_plan_funcionamiento_*'.
Objetivo: extraer el DOCENTE de cada curso-grupo-período para poder
cruzarlo con el dataset de matriculados y construir la variable
DIFICULTAD_DOCENTE_HIST (tasa histórica de reprobación de cada docente).

Uso:
    python clean_plan_funcionamiento.py <carpeta_entrada> <archivo_salida.csv>
"""
import sys
import re
import glob
import os
import pandas as pd
import numpy as np

REQUIRED_COLS = [
    "NRO.", "CODIGO", "ASIGNATURA", "GRUPOS", "MATRICULADOS", "APROBADOS",
    "DESAPROBADOS", "ABANDONOS", "RETIROS", "APROB 11-13", "APROB. 14-16",
    "APROB. 17-20", "PROMEDIO", "DOCENTES",
]
FILENAME_RE = re.compile(r"reporte_plan_funcionamiento_\d+_(\d{4})-([AB])", re.IGNORECASE)


def extraer_periodo(filepath):
    m = FILENAME_RE.search(os.path.basename(filepath))
    if not m:
        raise ValueError(f"No se pudo extraer el periodo de: {filepath}")
    anio, semestre = m.groups()
    return f"{anio}-{semestre.upper()}"


def es_binario_excel(filepath):
    with open(filepath, "rb") as f:
        header = f.read(8)
    return header.startswith(b"\xd0\xcf\x11\xe0") or header.startswith(b"PK")


def fix_mojibake(val):
    """Corrige dos variantes de doble-codificación observadas en los archivos fuente."""
    if not isinstance(val, str) or "Ã" not in val:
        return val
    for enc in ("latin1", "cp1252"):
        try:
            return val.encode(enc).decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return val


def leer_archivo_plan(filepath):
    if es_binario_excel(filepath):
        raw = pd.read_excel(filepath, header=None, dtype=str)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            lineas = [ln.rstrip("\n").split("\t") for ln in f]
        max_cols = max(len(ln) for ln in lineas)
        lineas = [ln + [None] * (max_cols - len(ln)) for ln in lineas]
        raw = pd.DataFrame(lineas)

    header_row_idx = None
    for i in range(min(15, len(raw))):
        primera = str(raw.iloc[i, 0]).strip()
        if primera == "NRO.":
            header_row_idx = i
            break
    if header_row_idx is None:
        raise ValueError(f"No se encontró encabezado 'NRO.' en {filepath}")

    df = raw.iloc[header_row_idx + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[header_row_idx]]

    # limpiar filas basura: nos quedamos solo con filas cuyo NRO sea numérico
    # (descarta líneas separadoras "====", filas vacías al final, etc.)
    df = df[df["NRO."].apply(lambda x: str(x).strip().isdigit())].copy()

    faltantes = set(REQUIRED_COLS) - set(df.columns)
    if faltantes:
        raise ValueError(f"Columnas faltantes {faltantes} en {filepath}")
    df = df[REQUIRED_COLS].copy()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": "", "None": ""})

    for col in ["ASIGNATURA", "DOCENTES"]:
        df[col] = df[col].apply(fix_mojibake)

    return df


def procesar_archivo(filepath):
    periodo = extraer_periodo(filepath)
    df = leer_archivo_plan(filepath)
    df["PERIODO"] = periodo
    df = df.rename(columns={"GRUPOS": "GRUPO", "DOCENTES": "DOCENTE"})
    return df


def main(carpeta, salida):
    patron = os.path.join(carpeta, "reporte_plan_funcionamiento_*")
    archivos = sorted(glob.glob(patron))
    if not archivos:
        print(f"No se encontraron archivos con patrón {patron}")
        sys.exit(1)

    print(f"Encontrados {len(archivos)} archivos de plan_funcionamiento:")
    dfs = []
    for f in archivos:
        try:
            df = procesar_archivo(f)
            dfs.append(df)
            print(f"  OK  {os.path.basename(f):55s}  filas={len(df):4d}  periodo={df['PERIODO'].iloc[0]}")
        except Exception as e:
            print(f"  ERROR {os.path.basename(f):55s}  -> {e}")

    consolidado = pd.concat(dfs, ignore_index=True)

    for col in ["MATRICULADOS", "APROBADOS", "DESAPROBADOS", "ABANDONOS", "RETIROS"]:
        consolidado[col] = pd.to_numeric(consolidado[col], errors="coerce")
    consolidado["PROMEDIO"] = pd.to_numeric(
        consolidado["PROMEDIO"].str.replace(",", ".", regex=False), errors="coerce"
    )

    consolidado.to_csv(salida, index=False, encoding="utf-8-sig")

    print()
    print("=" * 70)
    print(f"CONSOLIDADO: {len(consolidado):,} filas (curso-grupo-período) -> {salida}")
    print("=" * 70)
    print(f"Periodos: {sorted(consolidado['PERIODO'].unique())}")
    print(f"Docentes únicos: {consolidado[consolidado['DOCENTE']!='']['DOCENTE'].nunique():,}")
    print(f"Filas sin docente asignado (grupos especiales/convalidación): "
          f"{(consolidado['DOCENTE']=='').sum():,} de {len(consolidado):,}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python clean_plan_funcionamiento.py <carpeta_entrada> <archivo_salida.csv>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
