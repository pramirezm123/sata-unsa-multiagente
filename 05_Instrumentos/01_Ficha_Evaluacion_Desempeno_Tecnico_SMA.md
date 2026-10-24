# FICHA DE EVALUACIÓN DE DESEMPEÑO TÉCNICO DE LA ARQUITECTURA MULTIAGENTE (SMA)
**Sistema de Alerta Temprana Académica (SATA-UNSA)**  
**Investigador:** Paolo Sebastián Ramírez Melendres  
**Objetivo Específico 5 (OBJ5 - Actividad 1 y 2):** Pruebas técnicas de rendimiento, estabilidad y concurrencia.

---

## 1. Identificación y Propósito
El propósito de este instrumento es medir cuantitativamente la eficiencia computacional, la latencia de mensajería asíncrona, el consumo de memoria y la escalabilidad de la arquitectura multiagente implementada en Python mediante un bus de eventos desacoplado bajo estándares FIPA-ACL.

---

## 2. Dimensiones y Métricas Técnicas

| Dimensión | Métrica | Unidad de Medida | Umbral Aceptable | Herramienta de Medición |
|---|---|---|---|---|
| **Latencia de Inferencia** | Tiempo de predicción por checkpoint ($CP_0, CP_1, CP_2, CP_3$) | Milisegundos (ms) | $< 50\text{ ms}$ por registro | `time.perf_counter()` |
| **Latencia de Explicabilidad** | Generación de atribuciones SHAP (TreeExplainer) | Segundos (s) | $< 1.5\text{ s}$ por instancia | Profiler / `xai_agent.py` |
| **Latencia de Explicabilidad LIME** | Generación de explicación local subrogada LIME | Segundos (s) | $< 3.0\text{ s}$ por instancia | Profiler / `xai_agent.py` |
| **Sobrecarga del Bus (Bus Overhead)** | Tiempo de tránsito de un mensaje FIPA-ACL entre agentes | Microsegundos ($\mu\text{s}$) | $< 500\ \mu\text{s}$ | `EventBus.publish()` logger |
| **Consumo de Memoria RAM** | Huella de memoria del sistema completo con 4 modelos cargados | Megabytes (MB) | $< 400\text{ MB}$ | `psutil.Process().memory_info()` |
| **Carga de CPU** | Porcentaje de uso sostenido durante inferencia continua | Porcentaje (%) | $< 30\%$ (1 core) | `psutil.cpu_percent()` |
| **Rendimiento bajo Concurrencia** | Ingesta masiva y evaluación de cohortes completas | Registros / seg | $> 500\text{ reg/s}$ | Benchmark de estrés |

---

## 3. Protocolo de Pruebas de Estrés y Desempeño

### Escenario 1: Latencia Individual por Componente (Inferencia en Línea)
- **Condición:** Invocación unitaria simulando un docente ingresando calificaciones en tiempo real.
- **Flujo:** `IngestionAgent` $\rightarrow$ `PreprocessingAgent` $\rightarrow$ `PredictorAgent` $\rightarrow$ `RecommendationAgent` $\rightarrow$ `AlertAgent`.
- **Repeticiones:** 100 ejecuciones independientes (se reporta media, desviación estándar, percentil 95 y percentil 99).

### Escenario 2: Generación Asíncrona de Explicabilidad XAI
- **Condición:** Solicitud bajo demanda del reporte explicativo para casos en alerta alta.
- **Verificación:** El agente predictor debe emitir la alerta inmediatamente ($< 50\text{ ms}$) y notificar al bus; el `XAIAgent` debe procesar el cálculo en segundo plano sin congelar la UI de Streamlit ni retardar otras predicciones concurrentes.

### Escenario 3: Carga Masiva por Lotes (Batch Processing)
- **Condición:** Procesamiento del conjunto de prueba completo de la cohorte 2024–2025 ($N = 4,948$ registros estudiante-asignatura).
- **Métricas:** Tiempo total de corrida, tasa de transacciones por segundo (throughput), uso pico de memoria RAM.

---

## 4. Matriz de Registro de Resultados de Laboratorio

```
Fecha de Prueba: ____________________   
Entorno de Hardware: CPU: _____________________ | RAM: ________ GB | SO: Windows 11
Versión de Python: 3.12.x | scikit-learn: 1.5.x | shap: 0.46.x

+-------------------------------------+------------+-----------+------------+------------+
| Componente / Agente                 | Media (ms) | P95 (ms)  | P99 (ms)   | RAM (MB)   |
+-------------------------------------+------------+-----------+------------+------------+
| Bus de Mensajería (Overhead)        |            |           |            |            |
| IngestionAgent (Validación)         |            |           |            |            |
| PreprocessingAgent (Vectorización)  |            |           |            |            |
| PredictorAgent (RF Inferencia CP1)  |            |           |            |            |
| RecommendationAgent (Reglas)        |            |           |            |            |
| AlertAgent (Clasificación/Despacho) |            |           |            |            |
| Pipeline Completo (Sin XAI)         |            |           |            |            |
| XAIAgent (SHAP TreeExplainer CP1)   |            |           |            |            |
| XAIAgent (LIME Subrogado CP1)       |            |           |            |            |
+-------------------------------------+------------+-----------+------------+------------+
```

---

## 5. Criterios de Aceptación Técnica
1. **No-Bloqueo:** Ninguna llamada al motor explicativo XAI debe demorar más de 2 segundos en responder al bus, garantizando la fluidez de la interfaz del usuario.
2. **Determinismo:** El preprocesamiento y la predicción deben arrojar exactamente la misma probabilidad calculada que el entorno analítico de validación offline ($MAE = 0.0000$).
3. **Robustez ante Errores:** Mensajes corruptos o con campos faltantes deben generar una respuesta `ACLMessage.Performative.FAILURE` sin colapsar el bus ni desestabilizar a los agentes suscriptores.
