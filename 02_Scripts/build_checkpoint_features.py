"""
Ingeniería de variables intra-semestrales para modelos en cascada (CP0 a CP3).
Sistema de Alerta Temprana Académica - UNSA

A partir de:
  - notas_parciales_consolidado.csv
  - dataset_features_final.csv

Construye las variables intra-semestrales para cada checkpoint:
  - CP0: 15 variables históricas originales (línea base).
  - CP1: Historial + notas crudas F1 (EC1, EP1) + promedio ponderado F1 + puntos ganados
         + nota mínima requerida en pendiente + indicador de imposibilidad + faltantes
         + probabilidad calibrada fuera de muestra de CP0 (stacking).
  - CP2: Lo anterior + notas crudas F2 (EC2, EP2) + acumulado F1+F2 + tendencia F2 vs F1
         + nota mínima requerida en F3 + indicador de imposibilidad de aprobar.
  - CP3: Lo anterior + notas F3 (EC3, EP3) + acumulado total previo al acta.

Divide cronológicamente en:
  - Train: 2018-A a 2022-B
  - Val:   2023-A a 2023-B
  - Test:  2024-B a 2025-B

Uso:
    python build_checkpoint_features.py <notas_parciales_consolidado.csv> <dataset_features_final.csv> <carpeta_salida>
"""
import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold

sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_WEIGHTS = {
    "PESO_EC1": 15.0, "PESO_EP1": 15.0,
    "PESO_EC2": 20.0, "PESO_EP2": 20.0,
    "PESO_EC3": 15.0, "PESO_EP3": 15.0
}

HIST_COLS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS", "CARGA_ACADEMICA",
    "SEMESTRES_DESDE_INGRESO", "ES_REPETICION", "DIFICULTAD_CURSO_HIST",
    "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST",
    "ORDEN_PERIODO"
]

HIST_NULOS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS",
    "DIFICULTAD_CURSO_HIST", "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"
]


def main(parciales_path, features_path, carpeta_salida):
    os.makedirs(carpeta_salida, exist_ok=True)
    print("=" * 80)
    print("CONSTRUCCIÓN DE VARIABLES INTRA-SEMESTRALES (CP0 - CP3)")
    print("=" * 80)

    df_parc = pd.read_csv(parciales_path)
    df_feat = pd.read_csv(features_path)

    df_parc["CUI"] = df_parc["CUI"].astype(int)
    df_parc["CODIGO"] = df_parc["CODIGO"].astype(str).str.strip().str.lstrip("0")
    df_parc["PERIODO"] = df_parc["PERIODO"].astype(str).str.strip()

    df_feat["CUI"] = df_feat["CUI"].astype(int)
    df_feat["CODIGO"] = df_feat["CODIGO"].astype(str).str.strip().str.lstrip("0")
    df_feat["PERIODO"] = df_feat["PERIODO"].astype(str).str.strip()

    df = pd.merge(
        df_parc,
        df_feat[["CUI", "CODIGO", "PERIODO"] + HIST_COLS].drop_duplicates(subset=["CUI", "CODIGO", "PERIODO"]),
        on=["CUI", "CODIGO", "PERIODO"],
        how="inner"
    )
    df = df.dropna(subset=["REPROBADO"]).copy()
    df["REPROBADO"] = df["REPROBADO"].astype(int)
    print(f"Registros etiquetados consolidados: {len(df):,}")

    # Normalización robusta de pesos
    for comp in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
        col = f"PESO_{comp}"
        course_med = df.groupby("ASIGNATURA_NORM")[col].transform("median")
        df[col] = df[col].fillna(course_med).fillna(DEFAULT_WEIGHTS[col])

    sum_w = (df["PESO_EC1"] + df["PESO_EP1"] + df["PESO_EC2"] + df["PESO_EP2"] + df["PESO_EC3"] + df["PESO_EP3"]).replace(0, 100.0)
    for comp in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
        df[f"PESO_{comp}"] = (df[f"PESO_{comp}"] / sum_w) * 100.0

    # Valores y banderas de evaluación
    for comp in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
        df[f"{comp}_VAL"] = df[comp].fillna(0.0)
        df[f"{comp}_AUSENTE"] = (df[f"ESTADO_{comp}"] == "AUSENTE").astype(int)
        df[f"{comp}_SIN_DATO"] = df[comp].isna().astype(int)

    # Variables CP1 (Fase 1)
    df["PESO_F1"] = df["PESO_EC1"] + df["PESO_EP1"]
    df["PUNTOS_F1"] = (df["EC1_VAL"] * df["PESO_EC1"] + df["EP1_VAL"] * df["PESO_EP1"]) / 100.0
    df["PROM_F1"] = (df["PUNTOS_F1"] * 100.0) / df["PESO_F1"]
    df["PESO_PEND_F1"] = 100.0 - df["PESO_F1"]
    df["PUNTOS_FALT_F1"] = (11.0 - df["PUNTOS_F1"]).clip(lower=0.0)
    df["NOTA_MIN_PEND_F1"] = (df["PUNTOS_FALT_F1"] * 100.0) / df["PESO_PEND_F1"].replace(0, 1)
    df["IMPOSIBLE_APROBAR_F1"] = (df["NOTA_MIN_PEND_F1"] > 20.0).astype(int)
    df["FALTANTES_F1"] = df["EC1_SIN_DATO"] + df["EP1_SIN_DATO"]

    # Variables CP2 (Fases 1 y 2)
    df["PESO_F2"] = df["PESO_EC2"] + df["PESO_EP2"]
    df["PUNTOS_F2"] = (df["EC2_VAL"] * df["PESO_EC2"] + df["EP2_VAL"] * df["PESO_EP2"]) / 100.0
    df["PROM_F2"] = (df["PUNTOS_F2"] * 100.0) / df["PESO_F2"].replace(0, 1)
    df["PESO_F1_F2"] = df["PESO_F1"] + df["PESO_F2"]
    df["PUNTOS_F1_F2"] = df["PUNTOS_F1"] + df["PUNTOS_F2"]
    df["PROM_F1_F2"] = (df["PUNTOS_F1_F2"] * 100.0) / df["PESO_F1_F2"].replace(0, 1)
    df["PESO_PEND_F2"] = (100.0 - df["PESO_F1_F2"]).clip(lower=1.0)
    df["PUNTOS_FALT_F2"] = (11.0 - df["PUNTOS_F1_F2"]).clip(lower=0.0)
    df["NOTA_MIN_PEND_F2"] = (df["PUNTOS_FALT_F2"] * 100.0) / df["PESO_PEND_F2"]
    df["IMPOSIBLE_APROBAR_F2"] = (df["NOTA_MIN_PEND_F2"] > 20.0).astype(int)
    df["TENDENCIA_F2_VS_F1"] = df["PROM_F2"] - df["PROM_F1"]
    df["FALTANTES_F1_F2"] = df["FALTANTES_F1"] + df["EC2_SIN_DATO"] + df["EP2_SIN_DATO"]

    # Variables CP3 (Fases 1, 2 y 3)
    df["PESO_F3"] = df["PESO_EC3"] + df["PESO_EP3"]
    df["PUNTOS_F3"] = (df["EC3_VAL"] * df["PESO_EC3"] + df["EP3_VAL"] * df["PESO_EP3"]) / 100.0
    df["PUNTOS_TOTAL"] = df["PUNTOS_F1_F2"] + df["PUNTOS_F3"]
    df["PROM_TOTAL"] = df["PUNTOS_TOTAL"]
    df["YA_APROBADO_CP3"] = (df["PUNTOS_TOTAL"] >= 10.5).astype(int)
    df["TENDENCIA_F3_VS_F2"] = ((df["PUNTOS_F3"] * 100.0) / df["PESO_F3"].replace(0, 1)) - df["PROM_F2"]
    df["FALTANTES_TOTAL"] = df["FALTANTES_F1_F2"] + df["EC3_SIN_DATO"] + df["EP3_SIN_DATO"]

    # Partición temporal
    train_mask = df["ANIO"] <= 2022
    val_mask = df["ANIO"] == 2023
    test_mask = df["ANIO"] >= 2024

    train_df = df[train_mask].copy()
    val_df = df[val_mask].copy()
    test_df = df[test_mask].copy()

    print(f"Particiones: Train={len(train_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")

    # Imputación de históricas con medias de entrenamiento
    for c in HIST_NULOS:
        mean_tr = train_df[c].mean()
        for d in (train_df, val_df, test_df):
            d[f"{c}_SIN_DATO"] = d[c].isna().astype(int)
            d[c] = d[c].fillna(mean_tr)

    base_hist_features = [
        "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS", "CARGA_ACADEMICA",
        "SEMESTRES_DESDE_INGRESO", "ES_REPETICION", "DIFICULTAD_CURSO_HIST",
        "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"
    ] + [f"{c}_SIN_DATO" for c in HIST_NULOS]

    # Stacking sin fuga: out-of-fold en train
    print("Generando predicciones fuera de muestra de CP0 (Stacking)...")
    train_df = train_df.sort_values("ORDEN_PERIODO").reset_index(drop=True)
    train_df["PROBA_CP0"] = np.nan
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    for tr_idx, oof_idx in kf.split(train_df):
        rf_fold = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=20, class_weight="balanced", random_state=42, n_jobs=-1)
        rf_fold.fit(train_df.iloc[tr_idx][base_hist_features], train_df.iloc[tr_idx]["REPROBADO"])
        train_df.loc[oof_idx, "PROBA_CP0"] = rf_fold.predict_proba(train_df.iloc[oof_idx][base_hist_features])[:, 1]

    rf_cp0 = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=20, class_weight="balanced", random_state=42, n_jobs=-1)
    rf_cp0.fit(train_df[base_hist_features], train_df["REPROBADO"])
    val_df["PROBA_CP0"] = rf_cp0.predict_proba(val_df[base_hist_features])[:, 1]
    test_df["PROBA_CP0"] = rf_cp0.predict_proba(test_df[base_hist_features])[:, 1]

    # Guardar particiones
    f_tr = os.path.join(carpeta_salida, "checkpoint_train.csv")
    f_va = os.path.join(carpeta_salida, "checkpoint_val.csv")
    f_te = os.path.join(carpeta_salida, "checkpoint_test.csv")

    train_df.to_csv(f_tr, index=False, encoding="utf-8-sig")
    val_df.to_csv(f_va, index=False, encoding="utf-8-sig")
    test_df.to_csv(f_te, index=False, encoding="utf-8-sig")

    print(f"\nParticiones guardadas con éxito en {carpeta_salida}:")
    print(f"  Train: {f_tr} ({len(train_df):,} filas)")
    print(f"  Val:   {f_va} ({len(val_df):,} filas)")
    print(f"  Test:  {f_te} ({len(test_df):,} filas)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python build_checkpoint_features.py <notas_parciales_consolidado.csv> <dataset_features_final.csv> <carpeta_salida>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
