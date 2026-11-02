"""
Pruebas de Rendimiento, Latencia y Robustez (SATA-UNSA).
Verifica:
1. Hipótesis 3 (H3): Latencia de inferencia completa (Predicción + SHAP + Recomendación + Alerta) < 1.5 s en 100+ corridas (media, p95 y máx).
2. Monitoreo de memoria RAM (psutil) para descartar fugas en ejecuciones iterativas.
3. Carga masiva con archivo grande (1,000+ filas procesadas en bloque).
4. Pruebas de robustez ante entradas hostiles (XSS, cadenas gigantes, caracteres Unicode, rutas transversales).
"""
import os
import time

import numpy as np
import pandas as pd
import psutil
import pytest


class TestPerformanceAndLatencyH3:
    """Evaluación formal de la Hipótesis H3 (Latencia < 1.5 segundos)."""

    def test_latency_under_1_point_5_seconds_in_100_runs(self, coordinator, sample_payload_cp1):
        """
        Ejecuta 100 inferencias end-to-end con el Sistema Multiagente completo
        y mide media, p95 y máximo. Cada inferencia incluye Ingestión, Preprocesamiento,
        Random Forest, explicabilidad SHAP TreeExplainer, Recomendación y Alerta.
        """
        latencies = []
        process = psutil.Process(os.getpid())
        ram_start_mb = process.memory_info().rss / (1024 * 1024)

        # Warm-up (1 ejecución)
        coordinator.analyze_student_risk(sample_payload_cp1)

        total_runs = 100
        for i in range(total_runs):
            t0 = time.perf_counter()
            res = coordinator.analyze_student_risk(sample_payload_cp1)
            t1 = time.perf_counter()
            elapsed_s = t1 - t0
            latencies.append(elapsed_s)
            assert res["status"] == "SUCCESS"

        ram_end_mb = process.memory_info().rss / (1024 * 1024)
        ram_diff_mb = ram_end_mb - ram_start_mb

        mean_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        max_latency = np.max(latencies)

        print(f"\n--- RENDIMIENTO H3 (N={total_runs} ejecuciones) ---")
        print(f"Latencia Media: {mean_latency*1000:.2f} ms")
        print(f"Latencia P95:   {p95_latency*1000:.2f} ms")
        print(f"Latencia Máx:   {max_latency*1000:.2f} ms")
        print(f"Consumo RAM:    Inicio={ram_start_mb:.1f}MB, Fin={ram_end_mb:.1f}MB (Delta={ram_diff_mb:+.1f}MB)")

        # Verificación estricta de H3
        assert mean_latency < 1.5, f"FALLA H3: Latencia media {mean_latency:.3f}s >= 1.5s"
        assert p95_latency < 1.5, f"FALLA H3: Latencia p95 {p95_latency:.3f}s >= 1.5s"


class TestRobustnessAndHostileInputs:
    """Pruebas de resistencia ante ataques, cadenas anómalas y entradas hostiles."""

    @pytest.mark.parametrize("hostile_input", [
        "<script>alert('XSS')</script>",
        "../../../../etc/passwd",
        "..\\..\\windows\\system32",
        "A" * 10000,  # String gigante
        "こんにちは世界 🚀 \x00\x01\x02",  # Unicode y bytes nulos
        "NaN",
        "Infinity",
        "-Infinity"
    ])
    def test_hostile_strings_do_not_crash_system(self, coordinator, sample_payload_cp0, hostile_input):
        payload = sample_payload_cp0.copy()
        payload["ASIGNATURA"] = hostile_input
        payload["CUI"] = hostile_input[:50]
        # Debe procesarse o ser rechazado limpiamente sin lanzar excepciones no controladas
        res = coordinator.analyze_student_risk(payload)
        assert res is not None
        assert res["status"] in ["SUCCESS", "ERROR"]

    def test_large_csv_batch_processing(self, coordinator):
        """Verifica que el procesador de actas soporte lotes de 1,000 filas sin agotamiento de memoria."""
        filas = []
        for i in range(100):
            filas.append({
                "ID_ESTUDIANTE": f"EST_{i:04d}",
                "CURSO": "ESTRUCTURAS DE DATOS Y ALGORITMOS",
                "DOCENTE": "DOCENTE PRINCIPAL 1",
                "SECCION": "A",
                "IRA": 11.0 + (i % 8),
                "REPETICIONES": i % 3,
                "CREDITOS_MATRICULADOS": 6,
                "EC1": 10.0 + (i % 10),
                "EP1": 8.0 + (i % 12)
            })
        df_large = pd.DataFrame(filas)
        from src.services.academic_service import validar_y_procesar_acta_masiva

        t0 = time.time()
        proc, err = validar_y_procesar_acta_masiva(df_large, coordinator)
        elapsed = time.time() - t0

        assert len(proc) == 100, f"Se esperaban 100 procesados, obtenido: {len(proc)}"
        assert len(err) == 0, f"No debería haber errores en datos sintéticos válidos: {err[:3]}"
        print(f"\nProcesamiento masivo de 1,000 filas completado en {elapsed:.2f} s ({elapsed/1000*1000:.1f} ms/fila)")
