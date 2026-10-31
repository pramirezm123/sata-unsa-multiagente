"""
Servicios de Negocio Académico para SATA-UNSA.
Implementa:
- Simulación normativa del Examen Sustitutorio (UNSA EPIS: reemplaza el parcial más bajo, sin nota mínima de acceso).
- Regla de calibración del Semáforo con Banda Amarilla (75% del umbral).
- Procesamiento y validación fila por fila de cargas masivas de actas.
"""
import io
import math
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from ..database.db import get_all_courses, get_all_teachers


def calcular_semaforo(probabilidad: float, checkpoint: str, imposible_ordinario: bool = False) -> Dict[str, Any]:
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
        badge_text = "🔴 ALERTA ROJA - Alto Riesgo Académico"
        bg_hex = "#D32F2F"
        desc = "Se recomienda coordinar intervención tutorial y asesoría académica inmediata."
    elif probabilidad >= th_yellow:
        color_code = "AMARILLO"
        badge_text = "🟡 ALERTA AMARILLA - Riesgo Medio / Observación Preventiva"
        bg_hex = "#FBC02D"
        desc = "Estudiante en zona límite de riesgo; requiere refuerzo en las próximas evaluaciones."
    else:
        color_code = "VERDE"
        badge_text = "🟢 SITUACIÓN REGULAR - Bajo Riesgo"
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
    ec1: Optional[float], ep1: Optional[float],
    ec2: Optional[float], ep2: Optional[float],
    ec3: Optional[float], ep3: Optional[float],
    pesos: Dict[str, int]
) -> Dict[str, Any]:
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

    # Promedio ordinario final
    prom_ordinario = (
        val_ec1 * w_ec1 + ep1 * w_ep1 +
        val_ec2 * w_ec2 + ep2 * w_ep2 +
        val_ec3 * w_ec3 + ep3 * w_ep3
    )

    if prom_ordinario >= 10.5:
        return {
            "aplica": False,
            "ya_aprobo": True,
            "promedio_ordinario": round(prom_ordinario, 2),
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
    delta_necesario = 10.5 - prom_ordinario
    s_min_exacta = peor_nota + (delta_necesario / peor_peso)
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


def validar_y_procesar_acta_masiva(df: pd.DataFrame, coordinator_agent) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Valida fila por fila un archivo de carga masiva.
    - Filas con errores se agregan al reporte de errores sin interrumpir el lote.
    - Filas válidas se envían al bus del Sistema Multiagente para inferencia y semaforización.
    """
    filas_procesadas = []
    reporte_errores = []

    # Normalizar nombres de columnas a mayúsculas
    col_map = {c: c.strip().upper() for c in df.columns}
    df_clean = df.rename(columns=col_map)

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
        n_fila = idx + 2  # Fila en Excel contando encabezado
        id_est = str(row.get("ID_ESTUDIANTE", f"FILA_{n_fila}")).strip()
        errores_fila = []

        # 1. Validar curso y docente
        curso = str(row.get("CURSO", "")).strip().upper()
        docente = str(row.get("DOCENTE", "")).strip().upper()
        seccion = str(row.get("SECCION", "A")).strip().upper()
        if not curso:
            errores_fila.append("Falta especificar el nombre de la asignatura.")

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
        try:
            ira = float(row.get("IRA", 12.0))
            if ira < 0 or ira > 20:
                errores_fila.append(f"IRA fuera de rango (0-20): {ira}")
        except Exception:
            ira = 12.0
            errores_fila.append(f"Formato numérico de IRA inválido: {row.get('IRA')}")

        try:
            rep = int(float(row.get("REPETICIONES", 0)))
        except Exception:
            rep = 0

        try:
            carga = int(float(row.get("CREDITOS_MATRICULADOS", 6)))
        except Exception:
            carga = 6

        # 4. Validar y parsear calificaciones
        eval_vals = {}
        for ev in ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"]:
            raw_v = row.get(ev, np.nan)
            if pd.isna(raw_v) or str(raw_v).strip() == "":
                eval_vals[ev] = None
            else:
                str_v = str(raw_v).strip().upper()
                if str_v in ["AUSENTE", "NSP", "NP"]:
                    eval_vals[ev] = 0.0  # El SMA registra ausente = True
                else:
                    try:
                        num_v = float(str_v)
                        if num_v < 0 or num_v > 20:
                            errores_fila.append(f"Calificación en {ev} fuera de rango (0-20): {num_v}")
                        else:
                            eval_vals[ev] = num_v
                    except Exception:
                        errores_fila.append(f"Valor no numérico en {ev}: {str_v}")

        if errores_fila:
            reporte_errores.append({
                "fila": n_fila,
                "id_estudiante": id_est,
                "error": " | ".join(errores_fila)
            })
            continue

        # 5. Si la fila es válida, procesar con el Coordinador Multiagente
        payload = {
            "CUI": id_est,
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
            "PESO_EC1": pesos["EC1"], "PESO_EP1": pesos["EP1"],
            "PESO_EC2": pesos["EC2"], "PESO_EP2": pesos["EP2"],
            "PESO_EC3": pesos["EC3"], "PESO_EP3": pesos["EP3"]
        }

        try:
            res_sma = coordinator_agent.analyze_student_risk(payload)
            if res_sma["status"] == "SUCCESS":
                al = res_sma["alert"]
                # Determinar semáforo de 3 colores con banda amarilla
                semaf = calcular_semaforo(
                    al["probability"], 
                    al["checkpoint"], 
                    al.get("imposible_ordinario", False)
                )

                filas_procesadas.append({
                    "id_estudiante": id_est,
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
                    "id_estudiante": id_est,
                    "error": f"Falla en el pipeline SMA: {', '.join(res_sma.get('errors', []))}"
                })
        except Exception as e:
            reporte_errores.append({
                "fila": n_fila,
                "id_estudiante": id_est,
                "error": f"Excepción durante el análisis: {str(e)}"
            })

    return filas_procesadas, reporte_errores
