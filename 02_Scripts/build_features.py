"""
Ingeniería de variables (features) para el sistema de alerta temprana - VERSIÓN FINAL.
UNSA - Escuela de Ingeniería de Sistemas

A partir de dos fuentes:
  - matriculados_consolidado_full.csv (una fila = estudiante-curso-periodo)
  - plan_funcionamiento_consolidado.csv (una fila = curso-grupo-periodo, incluye DOCENTE)

Construye las variables predictoras finales, todas calculadas usando SOLO
información de periodos ANTERIORES al registro actual (sin fuga de datos):

  - IRA_ACUM, TASA_APROB_ACUM, REPROBACIONES_PREVIAS: historial del ESTUDIANTE
  - CARGA_ACADEMICA: cursos matriculados en el periodo actual
  - SEMESTRES_DESDE_INGRESO: antigüedad en la carrera
  - ES_REPETICION: si ya había llevado el curso antes
  - DIFICULTAD_CURSO_HIST: tasa histórica de reprobación del CURSO, usando una
    identidad de curso ESTABLE (nombre normalizado) que preserva continuidad
    a través de reformas curriculares que cambian el CODIGO (ver sección 3
    del informe de mejoras)
  - DIFICULTAD_DOCENTE_HIST: tasa histórica de reprobación del DOCENTE
    (todas sus secciones, cualquier curso)
  - DIFICULTAD_CURSO_DOCENTE_HIST: tasa histórica de reprobación de ESE
    docente específicamente en ESE curso

Nota: se evaluó también una variable de "tendencia institucional reciente"
(tasa de reprobación de toda la escuela en los últimos periodos) pero se
descartó por no aportar mejora neta al combinarse con las demás variables
(resultados documentados en el informe de mejoras).

Uso:
    python build_features.py <matriculados_consolidado.csv> <plan_funcionamiento_consolidado.csv> <salida.csv>
"""
import sys
import re
import unicodedata
import pandas as pd
import numpy as np


def normalizar_asignatura(s):
    """Identidad estable de curso: mayúsculas, sin tildes, espacios colapsados."""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    return " ".join(s.split())


def extraer_docente_principal(s):
    """Cuando hay 2 docentes en un mismo grupo (co-dictado), se toma el primero como principal."""
    if pd.isna(s) or str(s).strip() == "":
        return np.nan
    partes = re.split(r"\s{2,}", str(s).strip())
    return partes[0].strip() if partes else np.nan


def extraer_anio_ingreso(cod_ingreso):
    m = str(cod_ingreso)[2:4]
    try:
        dd = int(m)
    except ValueError:
        return np.nan
    return 1900 + dd if dd >= 90 else 2000 + dd


def periodo_a_orden(anio, semestre):
    return anio * 2 + np.where(semestre == "A", 0, 1)


def tasa_historica_por_grupo(df, columnas_grupo, target_col="REPROBADO"):
    """
    Calcula, para cada combinación de `columnas_grupo` + periodo, la tasa de
    reprobación acumulada usando SOLO periodos estrictamente anteriores
    (ventana expansiva desplazada). Devuelve un DataFrame con la tasa lista
    para hacer merge de vuelta al dataset principal.
    """
    stats = (
        df.dropna(subset=[target_col] + columnas_grupo)
        .groupby(columnas_grupo + ["ORDEN_PERIODO"])[target_col]
        .agg(["sum", "count"]).rename(columns={"sum": "reprobados", "count": "con_resultado"})
        .reset_index()
    )
    stats = stats.sort_values(columnas_grupo + ["ORDEN_PERIODO"])
    stats["reprobados_acum"] = stats.groupby(columnas_grupo)["reprobados"].cumsum()
    stats["con_resultado_acum"] = stats.groupby(columnas_grupo)["con_resultado"].cumsum()
    stats["reprobados_prev"] = stats.groupby(columnas_grupo)["reprobados_acum"].shift(1)
    stats["con_resultado_prev"] = stats.groupby(columnas_grupo)["con_resultado_acum"].shift(1)
    stats["_tasa"] = stats["reprobados_prev"] / stats["con_resultado_prev"]
    return stats[columnas_grupo + ["ORDEN_PERIODO", "_tasa"]]


def main(matriculados_path, plan_path, salida_path):
    df = pd.read_csv(matriculados_path)
    plan = pd.read_csv(plan_path)

    # ---------- Variables de estudiante (igual que versión anterior) ----------
    df["ANIO_INGRESO"] = df["COD.INGRESO"].apply(extraer_anio_ingreso)
    df["ORDEN_PERIODO"] = periodo_a_orden(df["ANIO"], df["SEMESTRE"])
    df["ORDEN_INGRESO"] = periodo_a_orden(df["ANIO_INGRESO"].fillna(df["ANIO"]), pd.Series(["A"] * len(df)))
    df["SEMESTRES_DESDE_INGRESO"] = df["ORDEN_PERIODO"] - df["ORDEN_INGRESO"]
    df["ES_REPETICION"] = (df["MATR."] > 1).astype(int)

    carga = df.groupby(["CUI", "PERIODO"]).size().rename("CARGA_ACADEMICA")
    df = df.merge(carga, on=["CUI", "PERIODO"], how="left")

    df = df.sort_values(["CUI", "ORDEN_PERIODO", "CODIGO"]).reset_index(drop=True)
    df_original = df.copy()

    def historicos_estudiante(g):
        tiene_resultado = g["REPROBADO"].notna()
        g = g.copy()
        g["IRA_ACUM"] = g["NOTA_NUM"].where(tiene_resultado).expanding().mean().shift(1)
        g["TASA_APROB_ACUM"] = g["REPROBADO"].where(tiene_resultado).apply(lambda x: 1 - x).expanding().mean().shift(1)
        g["REPROBACIONES_PREVIAS"] = g["REPROBADO"].where(tiene_resultado).fillna(0).expanding().sum().shift(1)
        return g

    df = df.groupby("CUI", group_keys=False).apply(historicos_estudiante)
    if "CUI" not in df.columns:
        df["CUI"] = df_original.loc[df.index, "CUI"]

    # ---------- Identidad de curso estable (corrige fragmentación por reforma curricular) ----------
    df["ASIGNATURA_NORM"] = df["ASIGNATURA"].apply(normalizar_asignatura)

    tasa_curso = tasa_historica_por_grupo(df, ["ASIGNATURA_NORM"])
    tasa_curso = tasa_curso.rename(columns={"_tasa": "DIFICULTAD_CURSO_HIST"})
    df = df.merge(tasa_curso, on=["ASIGNATURA_NORM", "ORDEN_PERIODO"], how="left")

    # ---------- Cruce con plan_funcionamiento para obtener el DOCENTE ----------
    plan["DOCENTE_PRINCIPAL"] = plan["DOCENTE"].apply(extraer_docente_principal)
    plan_join = plan[["CODIGO", "GRUPO", "PERIODO", "DOCENTE_PRINCIPAL"]].drop_duplicates(
        subset=["CODIGO", "GRUPO", "PERIODO"]
    )
    df = df.merge(plan_join, on=["CODIGO", "GRUPO", "PERIODO"], how="left")

    tasa_docente = tasa_historica_por_grupo(df, ["DOCENTE_PRINCIPAL"])
    tasa_docente = tasa_docente.rename(columns={"_tasa": "DIFICULTAD_DOCENTE_HIST"})
    df = df.merge(tasa_docente, on=["DOCENTE_PRINCIPAL", "ORDEN_PERIODO"], how="left")

    tasa_curso_docente = tasa_historica_por_grupo(df, ["CODIGO", "DOCENTE_PRINCIPAL"])
    tasa_curso_docente = tasa_curso_docente.rename(columns={"_tasa": "DIFICULTAD_CURSO_DOCENTE_HIST"})
    df = df.merge(tasa_curso_docente, on=["CODIGO", "DOCENTE_PRINCIPAL", "ORDEN_PERIODO"], how="left")

    # reordenar: CUI cerca del inicio
    cols = df.columns.tolist()
    cols.remove("CUI")
    cols.insert(cols.index("CODIGO"), "CUI")
    df = df[cols]

    df.to_csv(salida_path, index=False, encoding="utf-8-sig")

    print(f"Features finales construidas -> {salida_path}")
    print(f"Filas: {len(df):,}  Columnas: {len(df.columns)}")
    print()
    nuevas = ["IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS", "CARGA_ACADEMICA",
              "SEMESTRES_DESDE_INGRESO", "ES_REPETICION", "DIFICULTAD_CURSO_HIST",
              "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"]
    print("Cobertura (% no nulo) de cada variable:")
    for c in nuevas:
        print(f"  {c}: {df[c].notna().mean()*100:.1f}%")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python build_features.py <matriculados.csv> <plan_funcionamiento.csv> <salida.csv>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
