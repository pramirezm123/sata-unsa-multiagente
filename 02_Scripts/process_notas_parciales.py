"""
Extracción, depuración y consolidación de notas parciales (2018-2025).
Sistema de Alerta Temprana Académica - UNSA

Procesa los reportes de notas parciales generados por el Sistema de Administración
Académico de la UNSA (archivos PDF con estructura oficial de evaluaciones),
extrae las calificaciones por componente (EC1, EP1, EC2, EP2, EC3, EP3), sus pesos
porcentuales y estados (REGULAR, AUSENTE, RETIRADO), y consolida un dataset ordenado
a nivel estudiante-curso-período cruzado contra dataset_features_final.csv.

Uso:
    python process_notas_parciales.py <carpeta_notas_parciales> <dataset_features_final.csv> <carpeta_salida>

Ejemplo:
    python process_notas_parciales.py "Información académica_Notas Parciales_2018-2025/Data de las notas de estudiante" "03_Datasets/dataset_features_final.csv" "03_Datasets"
"""
import sys
import os
import re
import time
import hashlib
import pypdf
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Expresiones regulares para encabezados oficiales
RE_PERIODO = re.compile(r"PERIODO\s+LECTIVO\s+(\d{4})\s*-\s*([AB])", re.IGNORECASE)
RE_PESO = re.compile(r"PESO\s*:\s*(\d+)\s*%", re.IGNORECASE)
RE_EVAL = re.compile(r"(EXAMEN|EVAL\S*\s*CONTINUA)\s*(\d+)", re.IGNORECASE)
RE_ASIG = re.compile(r"ASIGNATURA\s*:\s*(?:\[(\d+)\])?\s*(.+)", re.IGNORECASE)
RE_GRUPO = re.compile(r"GRUPO\s*:\s*([A-Za-z0-9]+)", re.IGNORECASE)
RE_ESTUDIANTE = re.compile(r"^\s*(\d{1,3})\s+(\d{8})\s+(.+?)\s+([0-9]{1,2}(?:\.[0-9]+)?|NSP|NP|-)\s+([A-Z\s]+?)(?:\s+(.+))?$", re.MULTILINE)

COMPONENTES_VALIDOS = ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]


def get_file_hash(filepath):
    """Calcula el hash MD5 de un archivo para detectar duplicados exactos."""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def procesar_pdf(filepath):
    """Extrae metadatos y registros de estudiantes de un PDF oficial del sistema académico."""
    try:
        reader = pypdf.PdfReader(filepath)
        all_text = ""
        for page in reader.pages:
            all_text += (page.extract_text() or "") + "\n"

        if "SISTEMA DE ADMINISTRACION ACADEMICO" not in all_text.upper():
            return None, "NO_OFICIAL"

        m_per = RE_PERIODO.search(all_text)
        periodo = f"{m_per.group(1)}-{m_per.group(2).upper()}" if m_per else None

        m_peso = RE_PESO.search(all_text)
        peso = int(m_peso.group(1)) if m_peso else None

        m_eval = RE_EVAL.search(all_text)
        tipo_raw = m_eval.group(1).upper() if m_eval else None
        num_eval = m_eval.group(2) if m_eval else None

        comp = None
        if tipo_raw and num_eval:
            prefix = "EP" if "EXAM" in tipo_raw else "EC"
            comp = f"{prefix}{num_eval}"

        m_asig = RE_ASIG.search(all_text)
        cod_asig = m_asig.group(1) if m_asig else None
        nom_asig = m_asig.group(2).strip() if m_asig else None

        m_grupo = RE_GRUPO.search(all_text)
        grupo = m_grupo.group(1).upper() if m_grupo else None

        if not (periodo and comp):
            return None, "METADATOS_INCOMPLETOS"

        rows = []
        for line in all_text.split("\n"):
            m_s = RE_ESTUDIANTE.match(line.strip())
            if m_s:
                cui = int(m_s.group(2))
                nota_str = m_s.group(4).strip()
                en_letras = m_s.group(5).strip()

                if en_letras == "AUSENTE" or nota_str in ["NSP", "NP", "-"]:
                    tipo_nota = "AUSENTE"
                    nota_num = None
                elif en_letras == "RETIRADO":
                    tipo_nota = "RETIRADO"
                    nota_num = None
                else:
                    tipo_nota = "REGULAR"
                    try:
                        nota_num = float(nota_str)
                    except ValueError:
                        nota_num = None

                rows.append({
                    "CUI": cui,
                    "CODIGO": str(cod_asig).strip().lstrip("0") if cod_asig else None,
                    "ASIGNATURA": nom_asig,
                    "GRUPO": grupo,
                    "PERIODO": periodo,
                    "COMPONENTE": comp,
                    "PESO": peso,
                    "NOTA": nota_num,
                    "TIPO_NOTA": tipo_nota,
                })

        return rows, "OK"
    except Exception as e:
        return None, f"ERROR:{e}"


def main(carpeta_notas, path_features, carpeta_salida):
    t0 = time.time()
    os.makedirs(carpeta_salida, exist_ok=True)
    print("=" * 80)
    print("SISTEMA DE ALERTA TEMPRANA ACADÉMICA - UNSA")
    print("Extracción y Consolidación de Notas Parciales (Fase 1)")
    print("=" * 80)
    print(f"Carpeta entrada: {carpeta_notas}")
    print(f"Dataset features: {path_features}")
    print(f"Carpeta salida: {carpeta_salida}\n")

    # 1. Escaneo e inventario
    print("Paso 1: Escaneando archivos y filtrando duplicados...")
    archivos_pdf = []
    hashes_vistos = set()
    dup_count = 0

    for root, _, files in os.walk(carpeta_notas):
        for f in files:
            if f.lower().endswith(".pdf"):
                fpath = os.path.join(root, f)
                h = get_file_hash(fpath)
                if h in hashes_vistos:
                    dup_count += 1
                    continue
                hashes_vistos.add(h)
                archivos_pdf.append(fpath)

    print(f"  Archivos PDF encontrados: {len(archivos_pdf) + dup_count:,}")
    print(f"  Duplicados descartados por MD5: {dup_count:,}")
    print(f"  PDFs únicos a procesar: {len(archivos_pdf):,}\n")

    # 2. Extracción
    print("Paso 2: Extrayendo evaluaciones individuales...")
    todas_evals = []
    conteo_estados = {}

    for i, fpath in enumerate(archivos_pdf):
        rows, estado = procesar_pdf(fpath)
        conteo_estados[estado] = conteo_estados.get(estado, 0) + 1
        if rows:
            todas_evals.extend(rows)
        if (i + 1) % 500 == 0 or (i + 1) == len(archivos_pdf):
            print(f"  Procesados {i + 1:,} de {len(archivos_pdf):,} PDFs...")

    print(f"\nExtracción finalizada. Total registros individuales extraídos: {len(todas_evals):,}")
    print(f"Distribución de estados de procesamiento de archivos: {conteo_estados}\n")

    df_evals = pd.DataFrame(todas_evals)
    df_evals = df_evals[df_evals["COMPONENTE"].isin(COMPONENTES_VALIDOS)].copy()

    # 3. Pivotado a nivel estudiante-curso-período
    print("Paso 3: Pivotando por componente (EC1, EP1, EC2, EP2, EC3, EP3)...")
    # Prioridad en caso de duplicados
    df_evals["prio"] = df_evals["TIPO_NOTA"].map({"REGULAR": 3, "AUSENTE": 2, "RETIRADO": 1}).fillna(0)
    df_evals = df_evals.sort_values(["CUI", "CODIGO", "PERIODO", "COMPONENTE", "prio"], ascending=[True, True, True, True, False])
    df_evals = df_evals.drop_duplicates(subset=["CUI", "CODIGO", "PERIODO", "COMPONENTE"]).copy()

    piv_notas = df_evals.pivot(index=["CUI", "CODIGO", "PERIODO"], columns="COMPONENTE", values="NOTA")
    piv_pesos = df_evals.pivot(index=["CUI", "CODIGO", "PERIODO"], columns="COMPONENTE", values="PESO")
    piv_tipo = df_evals.pivot(index=["CUI", "CODIGO", "PERIODO"], columns="COMPONENTE", values="TIPO_NOTA")

    piv_notas.columns = [f"{c}" for c in piv_notas.columns]
    piv_pesos.columns = [f"PESO_{c}" for c in piv_pesos.columns]
    piv_tipo.columns = [f"ESTADO_{c}" for c in piv_tipo.columns]

    pivoted = pd.concat([piv_notas, piv_pesos, piv_tipo], axis=1).reset_index()

    # 4. Cruce con dataset_features_final
    print("Paso 4: Cruzando con dataset_features_final.csv...")
    df_feat = pd.read_csv(path_features)
    df_feat["CUI"] = df_feat["CUI"].astype(int)
    df_feat["CODIGO"] = df_feat["CODIGO"].astype(str).str.strip().str.lstrip("0")
    df_feat["PERIODO"] = df_feat["PERIODO"].astype(str).str.strip()

    id_cols = [
        "CUI", "CODIGO", "ASIGNATURA", "ASIGNATURA_NORM", "GRUPO", "PERIODO", "ANIO", "SEMESTRE",
        "DOCENTE_PRINCIPAL", "NOTA_NUM", "CONDICION", "REPROBADO"
    ]
    df_feat_sub = df_feat[id_cols].drop_duplicates(subset=["CUI", "CODIGO", "PERIODO"])

    consolidado = pd.merge(df_feat_sub, pivoted, on=["CUI", "CODIGO", "PERIODO"], how="inner")

    cols_order = [
        "CUI", "CODIGO", "ASIGNATURA", "ASIGNATURA_NORM", "GRUPO", "PERIODO", "ANIO", "SEMESTRE",
        "DOCENTE_PRINCIPAL",
        "EC1", "EP1", "PESO_EC1", "PESO_EP1", "ESTADO_EC1", "ESTADO_EP1",
        "EC2", "EP2", "PESO_EC2", "PESO_EP2", "ESTADO_EC2", "ESTADO_EP2",
        "EC3", "EP3", "PESO_EC3", "PESO_EP3", "ESTADO_EC3", "ESTADO_EP3",
        "NOTA_NUM", "CONDICION", "REPROBADO"
    ]
    consolidado = consolidado[cols_order].sort_values(["ANIO", "SEMESTRE", "ASIGNATURA", "CUI"]).reset_index(drop=True)

    # 5. Exportaciones
    salida_csv = os.path.join(carpeta_salida, "notas_parciales_consolidado.csv")
    consolidado.to_csv(salida_csv, index=False, encoding="utf-8-sig")

    salida_excel_es = os.path.join(carpeta_salida, "notas_parciales_consolidado_excel_es.csv")
    consolidado_es = consolidado.copy()
    float_cols = ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3", "PESO_EC1", "PESO_EP1", "PESO_EC2", "PESO_EP2", "PESO_EC3", "PESO_EP3", "NOTA_NUM"]
    for fc in float_cols:
        consolidado_es[fc] = consolidado_es[fc].apply(lambda x: "" if pd.isna(x) else str(x).replace(".", ","))
    consolidado_es.to_csv(salida_excel_es, sep=";", index=False, encoding="latin1", errors="replace")

    print("\n" + "=" * 80)
    print("CONSOLIDADO GENERADO CON ÉXITO")
    print("=" * 80)
    print(f"Total registros consolidados: {len(consolidado):,} (estudiante-curso-período)")
    print(f"Periodos cubiertos: {sorted(consolidado['PERIODO'].unique())}")
    print(f"Tasa de reprobación en el subconjunto: {consolidado['REPROBADO'].mean() * 100:.2f}%")
    print(f"Archivo estándar: {salida_csv}")
    print(f"Archivo Excel ES: {salida_excel_es}")
    print(f"Tiempo total: {time.time() - t0:.1f} segundos\n")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python process_notas_parciales.py <carpeta_notas_parciales> <dataset_features_final.csv> <carpeta_salida>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
