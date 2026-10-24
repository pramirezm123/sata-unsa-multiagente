"""
Entrenamiento y evaluación comparativa de modelos en cascada (CP0, CP1, CP2, CP3).
Sistema de Alerta Temprana Académica - UNSA

Entrena los 5 algoritmos requeridos:
  - Random Forest
  - Gradient Boosting
  - HistGradientBoosting
  - Regresión Logística
  - Árbol de Decisión

Protocolo metodológico estricto:
  - El umbral de decisión se calibra y congela EXCLUSIVAMENTE sobre Validación (2023)
    garantizando Recall >= 0.80 y maximizando la Precisión.
  - La evaluación final sobre Prueba (2024-2025) se ejecuta UNA SOLA VEZ sobre
    las mismas filas para todos los checkpoints.

Uso:
    python train_checkpoint_models.py <carpeta_datos> <carpeta_salida>

Ejemplo:
    python train_checkpoint_models.py "03_Datasets" "04_Modelo"
"""
import sys
import os
import json
import time
import joblib
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    accuracy_score, recall_score, precision_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, average_precision_score, confusion_matrix
)

RANDOM_STATE = 42
RECALL_OBJETIVO = 0.80

HIST_NULOS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS",
    "DIFICULTAD_CURSO_HIST", "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"
]
BASE_HIST_FEATURES = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS", "CARGA_ACADEMICA",
    "SEMESTRES_DESDE_INGRESO", "ES_REPETICION", "DIFICULTAD_CURSO_HIST",
    "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST"
] + [f"{c}_SIN_DATO" for c in HIST_NULOS]

CP0_FEATURES = BASE_HIST_FEATURES
CP1_FEATURES = BASE_HIST_FEATURES + [
    "PROBA_CP0", "EC1_VAL", "EP1_VAL", "EC1_AUSENTE", "EP1_AUSENTE",
    "PROM_F1", "PUNTOS_F1", "NOTA_MIN_PEND_F1", "IMPOSIBLE_APROBAR_F1", "FALTANTES_F1"
]
CP2_FEATURES = CP1_FEATURES + [
    "EC2_VAL", "EP2_VAL", "EC2_AUSENTE", "EP2_AUSENTE",
    "PROM_F2", "PUNTOS_F2", "PROM_F1_F2", "PUNTOS_F1_F2",
    "NOTA_MIN_PEND_F2", "IMPOSIBLE_APROBAR_F2", "TENDENCIA_F2_VS_F1", "FALTANTES_F1_F2"
]
CP3_FEATURES = CP2_FEATURES + [
    "EC3_VAL", "EP3_VAL", "EC3_AUSENTE", "EP3_AUSENTE",
    "PUNTOS_TOTAL", "PROM_TOTAL", "YA_APROBADO_CP3", "TENDENCIA_F3_VS_F2", "FALTANTES_TOTAL"
]

CHECKPOINTS = {
    "CP0": CP0_FEATURES,
    "CP1": CP1_FEATURES,
    "CP2": CP2_FEATURES,
    "CP3": CP3_FEATURES,
}


def construir_modelos():
    return {
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=20, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=RANDOM_STATE),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=200, max_depth=6, class_weight="balanced", random_state=RANDOM_STATE),
        "Regresión Logística": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
        "Árbol de Decisión": DecisionTreeClassifier(max_depth=8, min_samples_leaf=50, class_weight="balanced", random_state=RANDOM_STATE),
    }


def umbral_para_recall(y_val, proba_val, objetivo=RECALL_OBJETIVO):
    mejor = {"umbral": 0.01, "precision": -1}
    for u in np.linspace(0.01, 0.99, 197):
        pred = (proba_val >= u).astype(int)
        r = recall_score(y_val, pred, pos_label=1, zero_division=0)
        if r >= objetivo:
            p = precision_score(y_val, pred, pos_label=1, zero_division=0)
            if p > mejor["precision"]:
                mejor = {"umbral": u, "precision": p}
    return mejor["umbral"]


def main(carpeta_datos, carpeta_salida):
    t0 = time.time()
    os.makedirs(carpeta_salida, exist_ok=True)
    print("=" * 80)
    print("ENTRENAMIENTO Y EVALUACIÓN COMPARATIVA EN CASCADA")
    print("=" * 80)

    train_df = pd.read_csv(os.path.join(carpeta_datos, "checkpoint_train.csv"))
    val_df = pd.read_csv(os.path.join(carpeta_datos, "checkpoint_val.csv"))
    test_df = pd.read_csv(os.path.join(carpeta_datos, "checkpoint_test.csv"))

    y_train = train_df["REPROBADO"].astype(int)
    y_val = val_df["REPROBADO"].astype(int)
    y_test = test_df["REPROBADO"].astype(int)

    sample_weight_train = compute_sample_weight("balanced", y_train)

    print(f"Muestras: Train={len(train_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")
    print(f"Casos reales reprobados en Test: {(y_test == 1).sum():,} ({y_test.mean()*100:.2f}%)\n")

    all_results = []
    trained_models = {}
    curvas_roc = {}
    curvas_pr = {}
    matrices_confusion = {}

    for cp_name, feat_cols in CHECKPOINTS.items():
        print(f"Procesando {cp_name} ({len(feat_cols)} variables)...")
        scaler = StandardScaler()
        Xtr_s = pd.DataFrame(scaler.fit_transform(train_df[feat_cols]), columns=feat_cols)
        Xv_s = pd.DataFrame(scaler.transform(val_df[feat_cols]), columns=feat_cols)
        Xte_s = pd.DataFrame(scaler.transform(test_df[feat_cols]), columns=feat_cols)

        models = construir_modelos()
        for m_name, model in models.items():
            usa_escalado = m_name == "Regresión Logística"
            Xtr = Xtr_s if usa_escalado else train_df[feat_cols]
            Xv = Xv_s if usa_escalado else val_df[feat_cols]
            Xte = Xte_s if usa_escalado else test_df[feat_cols]

            if m_name == "Gradient Boosting":
                model.fit(Xtr, y_train, sample_weight=sample_weight_train)
            else:
                model.fit(Xtr, y_train)

            proba_val = model.predict_proba(Xv)[:, 1]
            proba_test = model.predict_proba(Xte)[:, 1]

            # Umbral fijado en validación
            u = umbral_para_recall(y_val, proba_val, objetivo=RECALL_OBJETIVO)
            pred_test = (proba_test >= u).astype(int)

            cm = confusion_matrix(y_test, pred_test)
            tn, fp, fn, tp = cm.ravel()

            rec = recall_score(y_test, pred_test, pos_label=1)
            prec = precision_score(y_test, pred_test, pos_label=1, zero_division=0)
            acc = accuracy_score(y_test, pred_test)
            f1 = f1_score(y_test, pred_test, pos_label=1, zero_division=0)
            auc = roc_auc_score(y_test, proba_test)
            ap = average_precision_score(y_test, proba_test)

            fp_per_tp = fp / tp if tp > 0 else 0
            total_alerts = tp + fp

            key = f"{cp_name}_{m_name.replace(' ', '_')}"
            trained_models[key] = model
            matrices_confusion[key] = cm.tolist()

            fpr, tpr, _ = roc_curve(y_test, proba_test)
            curvas_roc[key] = {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": auc}

            pr_p, pr_r, _ = precision_recall_curve(y_test, proba_test)
            curvas_pr[key] = {"precision": pr_p.tolist(), "recall": pr_r.tolist(), "ap": ap}

            all_results.append({
                "Checkpoint": cp_name,
                "Modelo": m_name,
                "Umbral_Val": round(u, 3),
                "TP": tp,
                "FN": fn,
                "FP": fp,
                "TN": tn,
                "Recall": round(rec, 4),
                "Precision": round(prec, 4),
                "Accuracy": round(acc, 4),
                "F1": round(f1, 4),
                "AUC_ROC": round(auc, 4),
                "AP": round(ap, 4),
                "Alertas": total_alerts,
                "FP_por_Caso": round(fp_per_tp, 2)
            })

    df_all = pd.DataFrame(all_results)
    fp_base = df_all.loc[(df_all["Checkpoint"] == "CP0") & (df_all["Modelo"] == "Random Forest"), "FP"].values[0]
    df_all["Reduccion_FP_pct"] = ((fp_base - df_all["FP"]) / fp_base * 100).round(2)

    # Exportar resultados
    csv_salida = os.path.join(carpeta_salida, "benchmark_modelos_checkpoints.csv")
    df_all.to_csv(csv_salida, index=False, encoding="utf-8-sig")

    with open(os.path.join(carpeta_salida, "curvas_roc_checkpoints.json"), "w") as f:
        json.dump(curvas_roc, f)
    with open(os.path.join(carpeta_salida, "curvas_pr_checkpoints.json"), "w") as f:
        json.dump(curvas_pr, f)
    with open(os.path.join(carpeta_salida, "matrices_confusion_checkpoints.json"), "w") as f:
        json.dump(matrices_confusion, f, indent=2)

    # Guardar los 4 Random Forest finales
    for cp_name in ["CP0", "CP1", "CP2", "CP3"]:
        rf_obj = trained_models[f"{cp_name}_Random_Forest"]
        rf_path = os.path.join(carpeta_salida, f"random_forest_{cp_name.lower()}.joblib")
        joblib.dump(rf_obj, rf_path)
        print(f"Modelo guardado: {rf_path}")

    print("\n" + "=" * 120)
    print("RESUMEN DE DESEMPEÑO DEL MODELO ELEGIDO (RANDOM FOREST) EN CADA CHECKPOINT:")
    print("=" * 120)
    rf_summary = df_all[df_all["Modelo"] == "Random Forest"]
    print(rf_summary[["Checkpoint", "Umbral_Val", "Recall", "Precision", "Accuracy", "F1", "AUC_ROC", "AP", "Alertas", "FP_por_Caso", "Reduccion_FP_pct"]].to_string(index=False))
    print(f"\nProceso finalizado en {time.time() - t0:.1f} segundos.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python train_checkpoint_models.py <carpeta_datos> <carpeta_salida>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
