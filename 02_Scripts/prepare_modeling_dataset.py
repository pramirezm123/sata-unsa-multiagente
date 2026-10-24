"""
Preparación del dataset de entrenamiento - VERSIÓN FINAL.
Sistema de Alerta Temprana Académica - UNSA

División CRONOLÓGICA en tres partes:
  - Entrenamiento: hasta 2020
  - Validación:    2021-2022  (para elegir el umbral de decisión)
  - Prueba:        2023 en adelante (evaluación final)

Variables predictoras finales (9 numéricas/binarias + 4 indicadoras de imputación):
  IRA_ACUM, TASA_APROB_ACUM, REPROBACIONES_PREVIAS, CARGA_ACADEMICA,
  DIFICULTAD_CURSO_HIST, SEMESTRES_DESDE_INGRESO, ES_REPETICION,
  DIFICULTAD_DOCENTE_HIST, DIFICULTAD_CURSO_DOCENTE_HIST

Uso:
    python prepare_modeling_dataset.py <dataset_features_final.csv> <carpeta_salida>
"""
import sys
import os
import pandas as pd

FEATURES_NUMERICAS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS",
    "CARGA_ACADEMICA", "DIFICULTAD_CURSO_HIST", "SEMESTRES_DESDE_INGRESO",
    "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST",
]
FEATURES_BINARIAS = ["ES_REPETICION"]
COLS_CON_NULOS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS",
    "DIFICULTAD_CURSO_HIST", "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST",
]

ANIO_CORTE_VAL = 2021
ANIO_CORTE_TEST = 2023


def main(entrada, carpeta_salida):
    os.makedirs(carpeta_salida, exist_ok=True)
    df = pd.read_csv(entrada)
    df = df.dropna(subset=["REPROBADO"]).copy()
    print(f"Registros con resultado definitivo: {len(df):,}")

    train_df = df[df["ANIO"] < ANIO_CORTE_VAL].copy()
    val_df = df[(df["ANIO"] >= ANIO_CORTE_VAL) & (df["ANIO"] < ANIO_CORTE_TEST)].copy()
    test_df = df[df["ANIO"] >= ANIO_CORTE_TEST].copy()

    print(f"Entrenamiento (hasta {ANIO_CORTE_VAL - 1}): {len(train_df):,} filas  "
          f"(tasa reprobación {train_df['REPROBADO'].mean()*100:.1f}%)")
    print(f"Validación ({ANIO_CORTE_VAL}-{ANIO_CORTE_TEST - 1}): {len(val_df):,} filas  "
          f"(tasa reprobación {val_df['REPROBADO'].mean()*100:.1f}%)")
    print(f"Prueba ({ANIO_CORTE_TEST} en adelante): {len(test_df):,} filas  "
          f"(tasa reprobación {test_df['REPROBADO'].mean()*100:.1f}%)")

    medias_train = {}
    for col in COLS_CON_NULOS:
        media = train_df[col].mean()
        medias_train[col] = media
        flag_col = f"{col}_SIN_DATO"
        for d in (train_df, val_df, test_df):
            d[flag_col] = d[col].isna().astype(int)
            d[col] = d[col].fillna(media)

    print()
    print("Medias de imputación (solo con datos de entrenamiento):")
    for col, val in medias_train.items():
        print(f"  {col}: {val:.4f}")

    flag_cols = [f"{c}_SIN_DATO" for c in COLS_CON_NULOS]
    feature_cols = FEATURES_NUMERICAS + FEATURES_BINARIAS + flag_cols
    id_cols = ["CUI", "CODIGO", "ASIGNATURA", "DOCENTE_PRINCIPAL", "PERIODO", "ANIO"]
    target_col = "REPROBADO"
    columnas_finales = id_cols + feature_cols + [target_col]

    train_df[columnas_finales].to_csv(os.path.join(carpeta_salida, "train.csv"), index=False, encoding="utf-8-sig")
    val_df[columnas_finales].to_csv(os.path.join(carpeta_salida, "val.csv"), index=False, encoding="utf-8-sig")
    test_df[columnas_finales].to_csv(os.path.join(carpeta_salida, "test.csv"), index=False, encoding="utf-8-sig")

    print()
    print(f"Guardado en {carpeta_salida}/: train.csv, val.csv, test.csv")
    print(f"Variables predictoras ({len(feature_cols)}): {feature_cols}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python prepare_modeling_dataset.py <dataset_features_final.csv> <carpeta_salida>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
