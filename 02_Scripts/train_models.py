"""
Entrenamiento, comparación y selección del modelo final - VERSIÓN FINAL.
Sistema de Alerta Temprana Académica - UNSA

Entrena los 4 algoritmos definidos en el plan de tesis (Regresión Logística,
Árbol de Decisión, Random Forest, Gradient Boosting) sobre las 15 variables
finales (incluye docente y familia de curso estable).

Selección de umbral: en lugar de maximizar F1 (que prioriza equilibrio),
se elige -sobre el conjunto de VALIDACIÓN- el umbral que llega al Recall
objetivo fijado (0.80, decisión tomada junto con el investigador dado que
en un sistema de alerta temprana es preferible una falsa alarma a un caso
no detectado), maximizando la Precisión dentro de esa restricción.

Uso:
    python train_models.py <carpeta_train_val_test> <carpeta_salida>
"""
import sys
import os
import json
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    accuracy_score, recall_score, precision_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, average_precision_score,
    confusion_matrix,
)

RANDOM_STATE = 42
RECALL_OBJETIVO = 0.80

FEATURE_COLS = [
    "IRA_ACUM", "TASA_APROB_ACUM", "REPROBACIONES_PREVIAS", "CARGA_ACADEMICA",
    "DIFICULTAD_CURSO_HIST", "SEMESTRES_DESDE_INGRESO",
    "DIFICULTAD_DOCENTE_HIST", "DIFICULTAD_CURSO_DOCENTE_HIST", "ES_REPETICION",
    "IRA_ACUM_SIN_DATO", "TASA_APROB_ACUM_SIN_DATO", "REPROBACIONES_PREVIAS_SIN_DATO",
    "DIFICULTAD_CURSO_HIST_SIN_DATO", "DIFICULTAD_DOCENTE_HIST_SIN_DATO",
    "DIFICULTAD_CURSO_DOCENTE_HIST_SIN_DATO",
]
TARGET_COL = "REPROBADO"


def cargar(carpeta, nombre):
    df = pd.read_csv(os.path.join(carpeta, nombre))
    return df[FEATURE_COLS].copy(), df[TARGET_COL].astype(int)


def construir_modelos():
    return {
        "Regresión Logística": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
        "Árbol de Decisión": DecisionTreeClassifier(max_depth=8, min_samples_leaf=50, class_weight="balanced", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=20,
                                                  class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=RANDOM_STATE),
    }


def umbral_para_recall(y_val, proba_val, objetivo):
    mejor = {"umbral": 0.01, "precision": -1}
    for u in np.linspace(0.01, 0.99, 197):
        pred = (proba_val >= u).astype(int)
        r = recall_score(y_val, pred, pos_label=1, zero_division=0)
        if r >= objetivo:
            p = precision_score(y_val, pred, pos_label=1, zero_division=0)
            if p > mejor["precision"]:
                mejor = {"umbral": u, "precision": p}
    return mejor["umbral"]


def evaluar(y_true, y_pred, y_proba):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "recall_clase_riesgo": recall_score(y_true, y_pred, pos_label=1),
        "precision_clase_riesgo": precision_score(y_true, y_pred, pos_label=1, zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted"),
        "f1_clase_riesgo": f1_score(y_true, y_pred, pos_label=1, zero_division=0),
        "auc_roc": roc_auc_score(y_true, y_proba),
        "average_precision": average_precision_score(y_true, y_proba),
    }


def main(carpeta_datos, carpeta_salida):
    os.makedirs(carpeta_salida, exist_ok=True)
    X_train, y_train = cargar(carpeta_datos, "train.csv")
    X_val, y_val = cargar(carpeta_datos, "val.csv")
    X_test, y_test = cargar(carpeta_datos, "test.csv")
    print(f"Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")
    print(f"Recall objetivo: {RECALL_OBJETIVO}")
    print()

    scaler = StandardScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_val_s = pd.DataFrame(scaler.transform(X_val), columns=X_val.columns)
    X_test_s = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    sample_weight_train = compute_sample_weight(class_weight="balanced", y=y_train)

    modelos = construir_modelos()
    resultados = []
    umbrales = {}
    matrices_confusion = {}
    modelos_entrenados = {}
    curvas_roc = {}
    curvas_pr = {}

    for nombre, modelo in modelos.items():
        print(f"Entrenando: {nombre} ...")
        usa_escalado = nombre == "Regresión Logística"
        Xtr, Xv, Xte = (X_train_s, X_val_s, X_test_s) if usa_escalado else (X_train, X_val, X_test)

        if nombre == "Gradient Boosting":
            modelo.fit(Xtr, y_train, sample_weight=sample_weight_train)
        else:
            modelo.fit(Xtr, y_train)

        proba_val = modelo.predict_proba(Xv)[:, 1]
        proba_test = modelo.predict_proba(Xte)[:, 1]

        umbral = umbral_para_recall(y_val, proba_val, RECALL_OBJETIVO)
        umbrales[nombre] = float(umbral)
        pred_test = (proba_test >= umbral).astype(int)

        m = evaluar(y_test, pred_test, proba_test)
        m["modelo"] = nombre
        m["umbral"] = umbral
        resultados.append(m)

        matrices_confusion[nombre] = confusion_matrix(y_test, pred_test).tolist()
        modelos_entrenados[nombre] = modelo
        fpr, tpr, _ = roc_curve(y_test, proba_test)
        curvas_roc[nombre] = {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": m["auc_roc"]}
        prec, rec, _ = precision_recall_curve(y_test, proba_test)
        curvas_pr[nombre] = {"precision": prec.tolist(), "recall": rec.tolist(), "ap": m["average_precision"]}

        print(f"  Umbral={umbral:.3f}  Recall={m['recall_clase_riesgo']:.3f}  Precision={m['precision_clase_riesgo']:.3f}  "
              f"F1={m['f1_clase_riesgo']:.3f}  Accuracy={m['accuracy']:.3f}  AUC-ROC={m['auc_roc']:.4f}")

    df_res = pd.DataFrame(resultados).set_index("modelo")
    df_res.to_csv(os.path.join(carpeta_salida, "comparacion_final.csv"))

    with open(os.path.join(carpeta_salida, "matrices_confusion.json"), "w") as f:
        json.dump(matrices_confusion, f, indent=2)
    with open(os.path.join(carpeta_salida, "curvas_roc.json"), "w") as f:
        json.dump(curvas_roc, f)
    with open(os.path.join(carpeta_salida, "curvas_pr.json"), "w") as f:
        json.dump(curvas_pr, f)
    with open(os.path.join(carpeta_salida, "umbrales.json"), "w") as f:
        json.dump(umbrales, f, indent=2)

    print()
    print("=" * 100)
    print(f"COMPARACIÓN FINAL (umbral por Recall objetivo={RECALL_OBJETIVO}, elegido en validación, evaluado en test 2023-2025)")
    print("=" * 100)
    print(df_res.sort_values("auc_roc", ascending=False).to_string())

    mejor = df_res["auc_roc"].idxmax()
    print()
    print(f"Mejor modelo según AUC-ROC: {mejor}")

    mejor_obj = modelos_entrenados[mejor]
    if hasattr(mejor_obj, "feature_importances_"):
        imp = pd.Series(mejor_obj.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
        imp.to_csv(os.path.join(carpeta_salida, "importancia_variables.csv"))
        print()
        print(f"Importancia de variables ({mejor}):")
        print(imp)
    elif hasattr(mejor_obj, "coef_"):
        coefs = pd.Series(mejor_obj.coef_[0], index=FEATURE_COLS).sort_values(key=abs, ascending=False)
        coefs.to_csv(os.path.join(carpeta_salida, "coeficientes_regresion.csv"))

    rf = modelos_entrenados.get("Random Forest")
    if rf is not None:
        imp_rf = pd.Series(rf.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
        imp_rf.to_csv(os.path.join(carpeta_salida, "importancia_variables_random_forest.csv"))

        import joblib
        joblib.dump(rf, os.path.join(carpeta_salida, "random_forest_final.joblib"))
        print()
        print(f"Modelo Random Forest guardado en {carpeta_salida}/random_forest_final.joblib")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python train_models.py <carpeta_train_val_test> <carpeta_salida>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
