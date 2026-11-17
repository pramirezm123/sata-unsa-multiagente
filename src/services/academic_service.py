"""
Servicios de Negocio Académico para SATA-UNSA.
Implementa:
- Simulación normativa del Examen Sustitutorio (UNSA EPIS: reemplaza el parcial más bajo, sin nota mínima de acceso).
- Regla de calibración del Semáforo con Banda Amarilla (75% del umbral).
- Procesamiento y validación fila por fila de cargas masivas de actas.
"""
import io
import math
from typing import Any

import numpy as np
import pandas as pd

from ..database.db import persist_acta_row_transactional
from ..security.access_control import AuthorizationError, get_authorized_teacher_names
from ..security.crypto import ensure_cui_hash

# Regla académica obligatoria UNSA: promedio redondeado >= 10.50 equivale a nota aprobatoria 11
UMBRAL_APROBACION_NORMATIVO: float = 10.50


def calcular_semaforo(probabilidad: float, checkpoint: str, imposible_ordinario: bool = False) -> dict[str, Any]:
    """
    Determina el color y nivel de alerta del semáforo:
    - ROJO: Probabilidad >= Umbral_CP o Imposible en ordinario.
    - AMARILLO: Probabilidad en [0.75 * Umbral_CP, Umbral_CP[.
    - VERDE: Probabilidad < 0.75 * Umbral_CP.
    """
    thresholds = {
        "CP0": 0.285,
        "CP1": 0.340,
        "CP2": 0.495,
        "CP3": 0.765
    }
    th = thresholds.get(checkpoint, 0.340)
    th_yellow = round(0.75 * th, 4)

    if imposible_ordinario or probabilidad >= th:
        color_code = "ROJO"
        badge_text = "ALERTA ROJA - Alto Riesgo Académico"
        bg_hex = "#D32F2F"
        desc = "Se recomienda coordinar intervención tutorial y asesoría académica inmediata."
    elif probabilidad >= th_yellow:
        color_code = "AMARILLO"
        badge_text = "ALERTA AMARILLA - Riesgo Medio / Observación Preventiva"
        bg_hex = "#FBC02D"
        desc = "Estudiante en zona límite de riesgo; requiere refuerzo en las próximas evaluaciones."
    else:
        color_code = "VERDE"
        badge_text = "SITUACIÓN REGULAR - Bajo Riesgo"
        bg_hex = "#388E3C"
        desc = "Trayectoria académica favorable y dentro de los parámetros esperados de aprobación."

    return {
        "color": color_code,
        "badge": badge_text,
        "bg_hex": bg_hex,
        "descripcion": desc,
        "umbral_rojo": th,
        "umbral_amarillo": th_yellow,
        "probabilidad": probabilidad
    }


def calcular_simulacion_sustitutorio(
    ec1: float | None, ep1: float | None,
    ec2: float | None, ep2: float | None,
    ec3: float | None, ep3: float | None,
    pesos: dict[str, int]
) -> dict[str, Any]:
    """
    Calcula la viabilidad y nota mínima requerida en el Examen Sustitutorio.
    Regla confirmada UNSA-EPIS:
    1. Puede rendirlo cualquier alumno desaprobado (sin nota mínima previa requerida).
    2. Reemplaza el Examen Parcial más bajo (min(EP1, EP2, EP3)).
    3. Las evaluaciones continuas (EC) NO se reemplazan.
    4. La nota mínima para aprobar es 10.5 -> 11.
    """
    # Si falta algún examen parcial, no se puede simular el sustitutorio final
    eps = [ep1, ep2, ep3]
    if any(e is None for e in eps):
        return {
            "aplica": False,
            "motivo": "El examen sustitutorio solo se calcula en el Checkpoint 3 al haber rendido las 3 fases ordinarias."
        }

    # Reemplazar None en continuas por 0 si no se rindió
    val_ec1 = ec1 if ec1 is not None else 0.0
    val_ec2 = ec2 if ec2 is not None else 0.0
    val_ec3 = ec3 if ec3 is not None else 0.0

    w_ec1 = pesos.get("EC1", 15) / 100.0
    w_ep1 = pesos.get("EP1", 15) / 100.0
    w_ec2 = pesos.get("EC2", 20) / 100.0
    w_ep2 = pesos.get("EP2", 20) / 100.0
    w_ec3 = pesos.get("EC3", 15) / 100.0
    w_ep3 = pesos.get("EP3", 15) / 100.0

    # Promedio ordinario final con redondeo normativo a 2 decimales para evitar imprecisión de punto flotante
    prom_ordinario_raw = (
        val_ec1 * w_ec1 + ep1 * w_ep1 +
        val_ec2 * w_ec2 + ep2 * w_ep2 +
        val_ec3 * w_ec3 + ep3 * w_ep3
    )
    prom_ordinario = round(prom_ordinario_raw, 2)

    if prom_ordinario >= 10.5:
        return {
            "aplica": False,
            "ya_aprobo": True,
            "promedio_ordinario": prom_ordinario,
            "mensaje": f"El estudiante ya se encuentra aprobado con promedio ordinario de {prom_ordinario:.2f}."
        }

    # Identificar el parcial más bajo y su peso
    parciales_info = [
        ("EP1", ep1, w_ep1),
        ("EP2", ep2, w_ep2),
        ("EP3", ep3, w_ep3)
    ]
    # Ordenar por nota menor (en caso de empate, el de mayor peso para favorecer al estudiante)
    parciales_info.sort(key=lambda x: (x[1], -x[2]))
    peor_nombre, peor_nota, peor_peso = parciales_info[0]

    # Despejar nota en examen sustitutorio S tal que:
    # Prom_nuevo = Prom_ordinario - (peor_nota * peor_peso) + (S * peor_peso) >= 10.5
    # S = peor_nota + (10.5 - prom_ordinario) / peor_peso
    delta_necesario = UMBRAL_APROBACION_NORMATIVO - prom_ordinario
    s_min_exacta = round(peor_nota + (delta_necesario / peor_peso), 6)
    s_min_redondeada = math.ceil(s_min_exacta)

    es_posible = (s_min_redondeada <= 20)

    return {
        "aplica": True,
        "ya_aprobo": False,
        "promedio_ordinario": round(prom_ordinario, 2),
        "parcial_a_reemplazar": peor_nombre,
        "nota_reemplazada": peor_nota,
        "peso_parcial": int(peor_peso * 100),
        "nota_minima_requerida": s_min_redondeada if es_posible else None,
        "nota_minima_exacta": round(s_min_exacta, 2),
        "es_viable": es_posible,
        "mensaje": (
            f"El sustitutorio reemplazará su nota en {peor_nombre} ({peor_nota:.1f}). "
            f"Para aprobar con 11, requiere obtener al menos {s_min_redondeada} en el examen sustitutorio."
            if es_posible else
            f"Matemáticamente inalcanzable: aún obteniendo 20 en el sustitutorio en reemplazo de {peor_nombre}, "
            f"su promedio máximo sería de {(prom_ordinario - peor_nota*peor_peso + 20*peor_peso):.2f}."
        )
    }


def evaluar_condicion_academica_normativa(
    ec1: float | None = None,
    ep1: float | None = None,
    ec2: float | None = None,
    ep2: float | None = None,
    ec3: float | None = None,
    ep3: float | None = None,
    pesos: dict[str, int] | None = None,
    probabilidad_riesgo: float = 0.0,
) -> dict[str, Any]:
    """
    Evalúa de forma coherente y unificada la condición académica bajo la normativa UNSA:
    - Umbral único de aprobación por redondeo: promedio >= 10.50 (nota entera 11).
    - Nota redondeada de 10.49 reprueba (nota entera 10).
    - Calcula puntos acumulados, peso evaluado, peso pendiente, puntos faltantes para 10.50,
      nota mínima necesaria en evaluaciones pendientes e imposibilidad matemática ordinaria.
    - En CP3 (cuando se rindieron las 3 fases), integra la simulación del examen sustitutorio
      reemplazando exclusivamente min(EP1, EP2, EP3) y jamás una evaluación continua (EC).
    - Si matemáticamente no es posible aprobar en vía ordinaria, activa la alerta roja.
    """
    pesos_cfg = pesos or {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
    sum_w = float(sum(pesos_cfg.get(k, 0) for k in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"])) or 100.0
    w_norm = {k: (float(pesos_cfg.get(k, 0)) / sum_w) * 100.0 for k in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]}

    evals_map = {"EC1": ec1, "EP1": ep1, "EC2": ec2, "EP2": ep2, "EC3": ec3, "EP3": ep3}
    has_f1 = (ec1 is not None) or (ep1 is not None)
    has_f2 = (ec2 is not None) or (ep2 is not None)
    has_f3 = (ec3 is not None) or (ep3 is not None)

    if has_f3 and has_f2 and has_f1:
        checkpoint = "CP3"
        fases_evaluadas = ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]
    elif has_f2 and has_f1:
        checkpoint = "CP2"
        fases_evaluadas = ["EC1", "EP1", "EC2", "EP2"]
    elif has_f1:
        checkpoint = "CP1"
        fases_evaluadas = ["EC1", "EP1"]
    else:
        checkpoint = "CP0"
        fases_evaluadas = []

    puntos_acum_raw = sum(
        (float(evals_map[k]) if evals_map[k] is not None else 0.0) * (w_norm[k] / 100.0)
        for k in fases_evaluadas
    )
    peso_evaluado = sum(w_norm[k] for k in fases_evaluadas)
    peso_pendiente = max(0.0, round(100.0 - peso_evaluado, 4))

    promedio_redondeado = round(puntos_acum_raw, 2)
    nota_entera_acta = int(math.floor(promedio_redondeado + 0.5))
    aprobado_actual = bool(promedio_redondeado >= UMBRAL_APROBACION_NORMATIVO)
    puntos_faltantes = 0.0 if aprobado_actual else max(0.0, round(UMBRAL_APROBACION_NORMATIVO - promedio_redondeado, 4))

    if peso_pendiente > 0.0:
        nota_min_pend = round((puntos_faltantes * 100.0) / peso_pendiente, 2)
        imposible_ordinario = bool(((puntos_faltantes * 100.0) / peso_pendiente) > 20.0 + 1e-6)
        posible_ordinario = not imposible_ordinario
        sim_susti = calcular_simulacion_sustitutorio(ec1, ep1, ec2, ep2, ec3, ep3, pesos_cfg)
        posible_con_sustitutorio = posible_ordinario
    else:
        nota_min_pend = 0.0 if aprobado_actual else None
        posible_ordinario = aprobado_actual
        imposible_ordinario = not aprobado_actual
        sim_susti = calcular_simulacion_sustitutorio(ec1, ep1, ec2, ep2, ec3, ep3, pesos_cfg)
        posible_con_sustitutorio = True if aprobado_actual else bool(sim_susti.get("es_viable", False))

    semaforo_info = calcular_semaforo(
        probabilidad=probabilidad_riesgo,
        checkpoint=checkpoint,
        imposible_ordinario=imposible_ordinario,
    )

    return {
        "checkpoint": checkpoint,
        "umbral_aprobacion_normativo": UMBRAL_APROBACION_NORMATIVO,
        "puntos_acumulados": promedio_redondeado,
        "nota_entera_acta": nota_entera_acta,
        "aprobado": aprobado_actual,
        "puntos_faltantes": puntos_faltantes,
        "peso_evaluado": round(peso_evaluado, 2),
        "peso_pendiente": round(peso_pendiente, 2),
        "nota_minima_pendiente": nota_min_pend,
        "posible_aprobar_ordinario": posible_ordinario,
        "imposible_aprobar_ordinario": imposible_ordinario,
        "posible_aprobar_con_sustitutorio": posible_con_sustitutorio,
        "sustitutorio": sim_susti,
        "semaforo": semaforo_info["color"],
        "alerta_roja": bool(semaforo_info["color"] == "ROJO"),
    }


def generar_plantilla_carga_masiva_csv() -> str:
    """Genera el contenido CSV de la plantilla oficial de carga masiva de actas."""
    headers = [
        "id_estudiante", "curso", "docente", "seccion",
        "IRA", "repeticiones", "creditos_matriculados",
        "EC1", "EP1", "EC2", "EP2", "EC3", "EP3",
        "pond_EC1", "pond_EP1", "pond_EC2", "pond_EP2", "pond_EC3", "pond_EP3"
    ]
    ejemplos = [
        ["EST_001", "ANALISIS Y DISENO DE ALGORITMOS", "DOCENTE PRINCIPAL 1", "A", "10.5", "2", "6", "0.0", "5.0", "", "", "", "", "15", "15", "20", "20", "15", "15"],
        ["EST_002", "ANALISIS Y DISENO DE ALGORITMOS", "DOCENTE PRINCIPAL 1", "A", "16.3", "0", "6", "19.0", "18.0", "", "", "", "", "15", "15", "20", "20", "15", "15"],
        ["EST_003", "ANALISIS Y DISENO DE ALGORITMOS", "DOCENTE PRINCIPAL 1", "A", "12.4", "1", "6", "15.0", "4.0", "", "", "", "", "15", "15", "20", "20", "15", "15"],
        ["EST_004", "ANALISIS Y DISENO DE ALGORITMOS", "DOCENTE PRINCIPAL 1", "A", "13.0", "0", "6", "AUSENTE", "12.0", "", "", "", "", "15", "15", "20", "20", "15", "15"]
    ]
    output = io.StringIO()
    output.write(",".join(headers) + "\n")
    for row in ejemplos:
        output.write(",".join(row) + "\n")
    return output.getvalue()


def validar_y_procesar_acta_masiva(
    df: pd.DataFrame,
    coordinator_agent,
    semestre: str = "2026-B",
    persist: bool = True,
    current_user: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Valida fila por fila un archivo de carga masiva (.csv / .xlsx).
    - Si se proporciona current_user, valida rol autorizado (DOCENTE titular de la fila o ADMIN).
    - Filas con errores se agregan al reporte de errores sin interrumpir el lote.
    - Aplica anonimización HMAC-SHA256 (cero CUI en texto claro en BD ni en resultados).
    - Filas válidas se envían al bus del Sistema Multiagente para inferencia y semaforización,
      y se persisten de forma transaccional en SQLite (estudiantes, perfil_semestre, matriculas,
      notas, historial_cambios, predicciones, explicaciones, mensajes_bus y metricas_tecnicas).
    """
    allowed_teacher_names: set[str] | None = None
    if current_user is not None:
        rol_u = current_user.get("role")
        if rol_u != "DOCENTE":
            raise AuthorizationError(
                f"Acceso denegado: El rol '{rol_u}' no tiene privilegios para cargar actas de calificaciones."
            )
        allowed_teacher_names = get_authorized_teacher_names(current_user)
        if not allowed_teacher_names:
            raise AuthorizationError("Acceso denegado: Docente sin identificador autorizado para carga de actas.")

    filas_procesadas: list[dict[str, Any]] = []
    reporte_errores: list[dict[str, Any]] = []

    if df is None or df.empty:
        reporte_errores.append({
            "fila": 0,
            "id_estudiante": "ARCHIVO_VACIO",
            "error": "El archivo cargado no contiene filas de datos.",
        })
        return [], reporte_errores

    # Normalizar nombres de columnas a mayúsculas
    col_map = {c: str(c).strip().upper() for c in df.columns}
    df_clean = df.rename(columns=col_map)
    if "ID_ESTUDIANTE" not in df_clean.columns and "CUI" in df_clean.columns:
        df_clean = df_clean.rename(columns={"CUI": "ID_ESTUDIANTE"})

    required_cols = ["ID_ESTUDIANTE", "CURSO", "DOCENTE"]
    missing = [c for c in required_cols if c not in df_clean.columns]
    if missing:
        reporte_errores.append({
            "fila": 0,
            "id_estudiante": "CABECERA",
            "error": f"Columnas obligatorias faltantes en el archivo: {', '.join(missing)}"
        })
        return [], reporte_errores

    for idx, row in df_clean.iterrows():
        n_fila = int(idx) + 2  # Fila en Excel contando encabezado
        raw_id_val = row.get("ID_ESTUDIANTE")
        id_est = "" if pd.isna(raw_id_val) else str(raw_id_val).strip()
        errores_fila = []

        if not id_est or id_est.lower() in ["nan", "none", "null"]:
            errores_fila.append("Falta especificar el identificador del estudiante (ID_ESTUDIANTE / CUI).")

        # 1. Validar curso y docente
        raw_curso = row.get("CURSO", "")
        raw_docente = row.get("DOCENTE", "")
        raw_seccion = row.get("SECCION", "A")
        curso = "" if pd.isna(raw_curso) else str(raw_curso).strip().upper()
        docente = "" if pd.isna(raw_docente) else str(raw_docente).strip().upper()
        seccion = "A" if pd.isna(raw_seccion) or not str(raw_seccion).strip() else str(raw_seccion).strip().upper()

        if not curso:
            errores_fila.append("Falta especificar el nombre de la asignatura.")
        if not docente:
            errores_fila.append("Falta especificar el docente responsable.")
        elif allowed_teacher_names is not None and docente not in allowed_teacher_names:
            raise AuthorizationError(
                f"Violación de aislamiento docente en fila {n_fila}: El usuario '{current_user.get('username')}' "
                f"no tiene autorización para cargar actas del docente '{docente}'."
            )

        # Detección de inyección de fórmulas CSV (=, +, @, |)
        tiene_formula = False
        for campo, val_str in [("ID_ESTUDIANTE", id_est), ("CURSO", curso), ("DOCENTE", docente), ("SECCION", seccion)]:
            if val_str and val_str[0] in ["=", "+", "@", "|"]:
                tiene_formula = True
                errores_fila.append(f"Contenido sospechoso de fórmula CSV no permitido en {campo}: {val_str}")

        # 2. Validar ponderaciones
        pesos = {}
        for p_key in ["POND_EC1", "POND_EP1", "POND_EC2", "POND_EP2", "POND_EC3", "POND_EP3"]:
            val = row.get(p_key, np.nan)
            if pd.isna(val) or str(val).strip() == "":
                # Fallback estándar institucional 15-15-20-20-15-15
                default_p = 20 if "2" in p_key else 15
                pesos[p_key.replace("POND_", "")] = default_p
            else:
                try:
                    pesos[p_key.replace("POND_", "")] = int(float(val))
                except Exception:
                    errores_fila.append(f"Ponderación inválida en {p_key}: {val}")

        suma_pesos = sum(pesos.values())
        if suma_pesos != 100:
            errores_fila.append(f"La suma de ponderaciones no es 100% (obtenido: {suma_pesos}%).")

        # 3. Validar variables basales
        raw_ira = row.get("IRA")
        if pd.isna(raw_ira) or str(raw_ira).strip() == "":
            ira = 12.0
        else:
            try:
                ira = float(raw_ira)
                if ira < 0 or ira > 20:
                    errores_fila.append(f"IRA fuera de rango (0-20): {ira}")
            except Exception:
                ira = 12.0
                errores_fila.append(f"Formato numérico de IRA inválido: {raw_ira}")

        raw_rep = row.get("REPETICIONES")
        if pd.isna(raw_rep) or str(raw_rep).strip() == "":
            rep = 0
        else:
            try:
                rep = int(float(raw_rep))
                if rep < 0:
                    errores_fila.append(f"Repeticiones no puede ser negativo: {rep}")
            except Exception:
                rep = 0
                errores_fila.append(f"Formato numérico de REPETICIONES inválido: {raw_rep}")

        raw_carga = row.get("CREDITOS_MATRICULADOS")
        if pd.isna(raw_carga) or str(raw_carga).strip() == "":
            carga = 6
        else:
            try:
                carga = int(float(raw_carga))
                if carga <= 0:
                    errores_fila.append(f"Créditos matriculados debe ser mayor a 0: {carga}")
            except Exception:
                carga = 6
                errores_fila.append(f"Formato numérico de CREDITOS_MATRICULADOS inválido: {raw_carga}")

        # 4. Validar y parsear calificaciones
        eval_vals: dict[str, float | None] = {}
        eval_ausentes: dict[str, bool] = {}
        for ev in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
            raw_v = row.get(ev, np.nan)
            if pd.isna(raw_v) or str(raw_v).strip() == "":
                eval_vals[ev] = None
                eval_ausentes[ev] = False
            else:
                str_v = str(raw_v).strip().upper()
                if str_v in ["AUSENTE", "NSP", "NP"]:
                    eval_vals[ev] = 0.0  # El SMA registra ausente = True
                    eval_ausentes[ev] = True
                else:
                    eval_ausentes[ev] = False
                    try:
                        num_v = float(str_v)
                        if num_v < 0 or num_v > 20:
                            errores_fila.append(f"Calificación en {ev} fuera de rango (0-20): {num_v}")
                        else:
                            eval_vals[ev] = num_v
                    except Exception:
                        errores_fila.append(f"Valor no numérico en {ev}: {str_v}")

        # 5. Aplicar anonimización HMAC-SHA256 antes de reportar o procesar
        id_anon = f"FILA_{n_fila}_RECHAZADA" if (not id_est or tiene_formula) else ensure_cui_hash(id_est)

        if errores_fila:
            reporte_errores.append({
                "fila": n_fila,
                "id_estudiante": id_anon,
                "error": " | ".join(errores_fila)
            })
            continue

        # 6. Si la fila es válida, procesar con el Coordinador Multiagente usando el hash anonimizado
        payload = {
            "CUI": id_anon,
            "CUI_HASH": id_anon,
            "ASIGNATURA": curso,
            "ASIGNATURA_NORM": curso,
            "IRA_ACUM": ira,
            "TASA_APROB_ACUM": 0.85,
            "REPROBACIONES_PREVIAS": rep,
            "CARGA_ACADEMICA": carga,
            "ES_REPETICION": 1 if rep > 0 else 0,
            "SEMESTRES_DESDE_INGRESO": 4.0,
            "DIFICULTAD_CURSO_HIST": 0.12,
            "DIFICULTAD_DOCENTE_HIST": 0.08,
            "DIFICULTAD_CURSO_DOCENTE_HIST": 0.10,
            "EC1": eval_vals["EC1"], "EP1": eval_vals["EP1"],
            "EC2": eval_vals["EC2"], "EP2": eval_vals["EP2"],
            "EC3": eval_vals["EC3"], "EP3": eval_vals["EP3"],
            "EC1_AUSENTE": 1 if eval_ausentes["EC1"] else 0,
            "EP1_AUSENTE": 1 if eval_ausentes["EP1"] else 0,
            "EC2_AUSENTE": 1 if eval_ausentes["EC2"] else 0,
            "EP2_AUSENTE": 1 if eval_ausentes["EP2"] else 0,
            "EC3_AUSENTE": 1 if eval_ausentes["EC3"] else 0,
            "EP3_AUSENTE": 1 if eval_ausentes["EP3"] else 0,
            "PESO_EC1": pesos["EC1"], "PESO_EP1": pesos["EP1"],
            "PESO_EC2": pesos["EC2"], "PESO_EP2": pesos["EP2"],
            "PESO_EC3": pesos["EC3"], "PESO_EP3": pesos["EP3"]
        }

        try:
            res_sma = coordinator_agent.analyze_student_risk(payload, persist_telemetry=False)
            if res_sma["status"] == "SUCCESS":
                al = res_sma["alert"]
                # Determinar semáforo de 3 colores con banda amarilla
                prob_val = al.get("probability", al.get("probability_pct", 0.0) / 100.0)
                semaf = calcular_semaforo(
                    prob_val, 
                    al["checkpoint"], 
                    al.get("imposible_ordinario", False)
                )

                if persist:
                    persist_acta_row_transactional(
                        raw_student_id=id_anon,
                        semestre=semestre,
                        curso=curso,
                        docente=docente,
                        seccion=seccion,
                        pesos=pesos,
                        ira=ira,
                        repeticiones=rep,
                        creditos_matriculados=carga,
                        eval_vals=eval_vals,
                        eval_ausentes=eval_ausentes,
                        sma_result=res_sma,
                        semaforo_color=semaf["color"],
                    )

                filas_procesadas.append({
                    "id_estudiante": id_anon,
                    "curso": curso,
                    "seccion": seccion,
                    "checkpoint": al["checkpoint"],
                    "probabilidad_pct": al["probability_pct"],
                    "semaforo": semaf["color"],
                    "badge": semaf["badge"],
                    "meta_nota_min": al["meta_nota_min"],
                    "promedio_acumulado": al["promedio_acumulado"],
                    "top_factor": al["top_factors"][0]["label"] if al.get("top_factors") else "Historial basal",
                    "accion_sugerida": al["recommendations"][0] if al.get("recommendations") else "Monitoreo regular"
                })
            else:
                reporte_errores.append({
                    "fila": n_fila,
                    "id_estudiante": id_anon,
                    "error": f"Falla en el pipeline SMA: {', '.join(res_sma.get('errors', []))}"
                })
        except Exception as e:
            reporte_errores.append({
                "fila": n_fila,
                "id_estudiante": id_anon,
                "error": f"Excepción durante el procesamiento/persistencia: {e!s}"
            })

    return filas_procesadas, reporte_errores
