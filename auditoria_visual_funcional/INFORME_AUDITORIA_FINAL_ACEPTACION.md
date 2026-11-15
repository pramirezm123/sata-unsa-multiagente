# INFORME DE AUDITORÍA FINAL INTEGRAL DE ACEPTACIÓN — SISTEMA SATA-UNSA (FASE 5)

**Proyecto:** Sistema de Alerta Temprana Académica (SATA-UNSA)  
**Tesis:** *«Diseño e implementación de una Arquitectura de Software basada en Sistemas Multiagentes para un Sistema de Alerta Temprana con Machine Learning e IA Explicable (XAI) para la reducción de la reprobación académica»*  
**Unidad Académica:** Escuela Profesional de Ingeniería de Sistemas — Universidad Nacional de San Agustín de Arequipa (EPIS-UNSA)  
**Rama Auditada:** `fix-ui-acceso` (Commit base `b3ba045`)  
**Entorno de Ejecución:** `http://localhost:8501` (Streamlit + SQLite WAL + 7 Agentes FIPA-ACL + Modelos Random Forest CP0–CP3 + SHAP)  
**Modalidad de Auditoría:** **ESTRICTAMENTE SOLO LECTURA** (Cero modificaciones a código fuente, modelos, pruebas o base de datos institucional)  
**Fecha de Emisión:** 14 de noviembre de 2026  

---

## 1. RESUMEN EJECUTIVO

El equipo multidisciplinario de auditoría senior (Arquitectura Multiagente, Machine Learning, IA Explicable SHAP/LIME, Ciberseguridad y Privacidad, Aseguramiento de Calidad QA, UX/UI Responsive y Persistencia de Bases de Datos) ha ejecutado la **Auditoría Final Integral de Aceptación (Fase 5)** del sistema **SATA-UNSA**.

Tras el ciclo iterativo de auditoría y remediación ejecutado en las fases previas —**Fase 1** (Auditoría Exhaustiva Inicial), **Fase 2** (Corrección de 5 Defectos Críticos), **Fase 3** (Corrección de 6 Bloques de Prioridad Alta) y **Fase 4** (Corrección Visual, UX y Responsive)—, se constata que **el sistema SATA-UNSA cumple satisfactoriamente con los objetivos arquitectónicos, predictivos, explicativos, de seguridad, normativos y visuales definidos en el plan de tesis**, habiendo eliminado la totalidad de defectos de severidad `CRITICAL` (0 pendientes) y `HIGH` (0 pendientes).

### Indicadores Globales de Aceptación
- **Estado de Defectos de Bloqueo:** `0 CRITICAL` | `0 HIGH` | `5 MEDIUM` (Observaciones técnicas no bloqueantes) | `4 LOW` (Observaciones menores de mantenimiento/documentación).
- **Suite de Pruebas Automatizadas:** **117 pruebas ejecutadas (`117 passed, 0 failed`)** en `134.19 s`, ejecutadas sobre una base de datos SQLite temporal aislada (`isolated_test_database` en `tests/conftest.py:21-36`).
- **Cobertura de Código (`pytest --cov=src --cov=app`):** **86% de cobertura global** (`2,291` sentencias analizadas, `1,976` cubiertas, `315` no cubiertas), superando ampliamente el umbral mínimo de ingeniería (70%).
- **Análisis Estático de Seguridad (`bandit -r src app.py`):** **0 vulnerabilidades de severidad Alta (`High: 0`) y 0 de severidad Media (`Medium: 0`)** sobre `5,417` líneas escaneadas.
- **Arquitectura Multiagente:** Los **7 agentes inteligentes** heredan de `BaseAgent`, se comunican a través de `MessageBus` mediante objetos `AgentMessage`, registran las 4 performativas FIPA-ACL (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`) en la tabla `mensajes_bus` y operan sin exponer PII.
- **Modelos Predictivos en Cascada (CP0–CP3):** Los 4 modelos serializados `random_forest_cp{0,1,2,3}.joblib` se encuentran íntegros, calibrados sobre validación temporal 2023 para priorizar sensibilidad (`Recall >= 0.80`) y verificados sobre el conjunto de prueba 2024–2025 (`N = 4,948` matrículas, `312` reprobados reales), alcanzando un `Recall` de **85.90% (CP0)**, **87.50% (CP1)**, **84.62% (CP2)** y **88.46% (CP3)**, con una reducción progresiva de falsos positivos de hasta **-95.23% en CP3** (`ROC-AUC = 0.9950`).
- **Dictamen Final de Aceptación:** **`GO CON OBSERVACIONES`** (Apto para sustentación de tesis y despliegue piloto controlado en la EPIS-UNSA, sujeto a la toma de conocimiento de las 5 observaciones de severidad media y 4 de severidad baja documentadas en la Sección 14).

---

## 2. ALCANCE Y METODOLOGÍA

### 2.1. Alcance de la Auditoría
La auditoría abarcó la totalidad de las capas del sistema SATA-UNSA:
1. **Capa de Presentación y Experiencia de Usuario (`app.py`, `src/reports/pdf_generator.py`):** 7 vistas funcionales, control de navegación por rol (`ESTUDIANTE`, `DOCENTE`, `AUTORIDAD`, `ADMIN`), diseño institucional EPIS-UNSA, accesibilidad cromática WCAG AA y comportamiento responsive en 4 resoluciones (`1440×900`, `1366×768`, `768×1024`, `390×844`).
2. **Capa de Arquitectura Multiagente y Mensajería (`src/agents/`, `src/messaging/`):** 7 agentes especializados, bus de mensajes FIPA-ACL y trazabilidad de performativas.
3. **Capa de Machine Learning e IA Explicable (`04_Modelo/`, `02_Scripts/`, `predictor_agent.py`, `xai_agent.py`):** Modelos Random Forest en cascada `CP0`–`CP3`, umbrales calibrados, apilamiento de probabilidades (`PROBA_CP0`), explicaciones locales SHAP (`TreeExplainer`) y validación experimental SHAP vs. LIME.
4. **Capa de Normativa Académica y Servicios (`src/services/academic_service.py`, `preprocessing_agent.py`):** Regla de redondeo aprobatorio (`10.50 -> 11`), simulador de Examen Sustitutorio (`min(EP1, EP2, EP3)`), detección de imposibilidad matemática ordinaria y procesamiento transaccional de actas masivas.
5. **Capa de Seguridad, Privacidad y Persistencia (`src/security/`, `src/database/db.py`, `src/database/sata_unsa.db`):** Anonimización irreversible `HMAC-SHA256`, hashing de contraseñas `PBKDF2-HMAC-SHA256`, aislamiento RBAC por rol y transaccionalidad SQLite en modo WAL.

### 2.2. Metodología Aplicada (Modo Estrictamente Solo Lectura)
1. **Revisión Documental Cruzada:** Lectura íntegra y contraste de los 4 informes precedentes (`INFORME_AUDITORIA_EXHAUSTIVA.md`, `INFORME_CORRECCION_CRITICOS.md`, `INFORME_CORRECCION_PRIORIDAD_ALTA.md`, `INFORME_CORRECCION_VISUAL.md`), el documento normativo `Propuesta_Ajuste_Plan_Tesis_Asesora.md` y `README.md`.
2. **Inspección Estática de Código y Artefactos:** Revisión línea por línea de los módulos en `src/`, `app.py`, `02_Scripts/`, `04_Modelo/` y `tests/`.
3. **Auditoría Forense de Base de Datos en Modo Solo Lectura (`mode=ro`):** Conexión mediante URI `file:d:/TESIS FINAL/src/database/sata_unsa.db?mode=ro` para verificar esquema, conteo de registros, hashes criptográficos y ausencia de datos personales en claro sin alterar un solo byte del archivo institucional.
4. **Verificación de Cobertura y Análisis Estático:** Inspección del reporte de cobertura por línea (`python -m coverage report -m`), análisis de seguridad con `bandit -r src app.py` y linting con `ruff check src app.py tests`.
5. **Verificación Funcional y Visual Multi-Resolución:** Contraste contra las evidencias reales capturadas en navegador sobre `http://localhost:8501` para los 4 roles y las 4 resoluciones exigidas (`auditoria_visual_funcional/evidencias/`).

---

## 3. ESTADO DEL REPOSITORIO

### 3.1. Estado de Git (`git status -s -b` y `git log -n 5 --oneline`)
- **Rama activa:** `fix-ui-acceso`
- **Historial reciente de commits:**
  - `b3ba045` — *Rediseño UI login y dashboard con identidad UNSA y fix de acceso*
  - `129457e` — *feat: actualización de agentes, interfaz y modelos SATA-UNSA*
  - `d628c14` — *chore: configure gitignore and untrack confidential datasets and temp files*
  - `7cf86b4` — *Sistema SATA-UNSA completo v1.0 - Tesis EPIS UNSA*

### 3.2. Archivos Modificados y No Rastreados (`git diff --stat`)
Respecto al commit base `b3ba045`, el árbol de trabajo registra **11 archivos rastreados modificados** (`+2,291 inserciones / -409 eliminaciones`) y **5 rutas no rastreadas**:

| Ruta del Archivo | Estado Git | Líneas (`+ / -`) | Fase de Origen | Propósito del Cambio |
| :--- | :---: | :---: | :---: | :--- |
| `app.py` | `M` | `+1567 / -358` | Fases 2, 3, 4 | RBAC por rol, selectores reales Docente, bus FIPA-ACL, bitácora de tutorías, TAM completo, métricas dinámicas y mejoras UX/UI responsive. |
| `src/agents/coordinator_agent.py` | `M` | `+30 / -3` | Fase 3 | Persistencia de trazas FIPA-ACL (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`) en `mensajes_bus` durante `analyze_student_risk`. |
| `src/agents/recommendation_agent.py` | `M` | `+2 / -2` | Fase 3 | Emisión de performativa `PROPOSE` (`PROPOSE_TUTORIA_CP*`) en lugar de `INFORM`. |
| `src/agents/xai_agent.py` | `M` | `+89 / -1` | Fase 2 | Helper `format_shap_factor_for_ui` para separar `impact` (valor SHAP) de `value` (nota observada). |
| `src/database/db.py` | `M` | `+559 / -16` | Fases 2, 3 | Tabla `tutorias`, `persist_acta_row_transactional`, `get_course_sections_summary`, `evaluate_and_persist_enrollment`, `get_header_metrics`, `get_technical_metrics_summary`. |
| `src/messaging/bus.py` | `M` | `+29 / -5` | Fase 3 | Integración opcional con `log_bus_message()` y sanitización automática de PII (`nombre`, `dni`, `email`). |
| `src/security/access_control.py` | `M` | `+11 / -6` | Fase 2 | Restricción de `AUTORIDAD` frente a registros individuales (`AuthorizationError`). |
| `src/security/crypto.py` | `M` | `+15 / -0` | Fase 2 | Función idempotente `ensure_cui_hash()` (evita doble hash sobre cadenas hex de 16 caracteres). |
| `src/services/academic_service.py` | `M` | `+87 / -18` | Fase 2 | Anonimización HMAC-SHA256 e invocación de `persist_acta_row_transactional` en carga masiva de actas. |
| `tests/conftest.py` | `M` | `+18 / -0` | Fase 2 | Fixture `isolated_test_database` (`autouse=True`) para redirigir `DB_PATH` a un archivo temporal durante `pytest`. |
| `tests/test_services.py` | `M` | `+2 / -2` | Fase 2 | Ajuste de aserción `proc[0]["id_estudiante"] == hash_cui("EST_OK")` tras anonimizar actas masivas. |
| `tests/test_critical_fixes.py` | `??` | Nuevo (322 lín.) | Fase 2 | 12 pruebas de integración para los 5 defectos críticos. |
| `tests/test_high_priority_fixes.py` | `??` | Nuevo (351 lín.) | Fase 3 | 12 pruebas de integración para los 6 defectos de prioridad alta. |
| `auditoria_visual_funcional/` | `??` | Nuevo (Dir.) | Fases 1–5 | Informes de auditoría y evidencias visuales en navegador. |
| `src/database/sata_unsa.db-shm` / `-wal` | `??` | Archivos WAL | Runtime | Archivos de memoria compartida y Write-Ahead Log de SQLite (`.db` está en `.gitignore`, pero `.db-shm` y `.db-wal` no están en `.gitignore`). |

### 3.3. Consistencia entre Informes Previos y Estado Real del Repositorio
- Se verificó que todas las modificaciones descritas en `INFORME_CORRECCION_CRITICOS.md`, `INFORME_CORRECCION_PRIORIDAD_ALTA.md` e `INFORME_CORRECCION_VISUAL.md` existen realmente en el código actual.
- **Observación de trazabilidad documental (`LOW`):** El archivo `tests/test_services.py` presenta una modificación de 2 líneas (`hash_cui("EST_OK")`) realizada durante la Fase 2 para mantener compatibilidad con la anonimización de `validar_y_procesar_acta_masiva`, la cual no fue listada en la tabla resumen de archivos modificados de `INFORME_CORRECCION_CRITICOS.md`. Asimismo, los archivos temporales de SQLite `*.db-shm` y `*.db-wal` aparecen como untracked porque `.gitignore` ignora `*.db` (línea 33) pero no `*.db-shm` ni `*.db-wal`.

---

## 4. MATRIZ DE CUMPLIMIENTO GENERAL

Cada componente, requisito y subsistema ha sido clasificado rigurosamente bajo la escala oficial:
- `VERIFIED`: Cumple íntegramente en código, base de datos, pruebas y navegador.
- `PARTIALLY VERIFIED`: Implementado y funcional en el flujo principal, pero presenta alguna limitación de alcance o discrepancia menor documentada en la Sección 14.
- `NOT VERIFIED`: No pudo comprobarse por falta de artefacto en tiempo de ejecución.
- `FAILED`: Incumple el requisito especificado.

| Código | Dominio Auditado | Requisito / Especificación | Estado | Evidencia Verificada (Archivo / Línea / Prueba) |
| :---: | :--- | :--- | :---: | :--- |
| **ARQ-01** | Arquitectura Multiagente | Existencia e implementación real de los 7 agentes del SMA | `VERIFIED` | `src/agents/*_agent.py` (7 clases que heredan de `BaseAgent` en `base_agent.py:10`). |
| **ARQ-02** | Mensajería FIPA-ACL | Registro real de performativas `REQUEST`, `INFORM`, `PROPOSE`, `FAILURE` en `mensajes_bus` | `VERIFIED` | `coordinator_agent.py:72-229`, `recommendation_agent.py:27`, `db.py:1154-1175`, `test_high_priority_fixes.py:116-175`. |
| **ARQ-03** | Desacoplamiento SMA | Comunicación mediante colas y objetos `AgentMessage` sin llamadas directas entre agentes especialistas | `PARTIALLY VERIFIED` | `bus.py:17-73` usa `queue.Queue` por agente, aunque `CoordinatorAgent.analyze_student_risk` ejecuta el ciclo en un único hilo síncrono (`HALL-F5-06`). |
| **ML-01** | Modelos en Cascada | Existencia e integridad de los 4 modelos `random_forest_cp{0,1,2,3}.joblib` | `VERIFIED` | `04_Modelo/random_forest_cp0..3.joblib` cargados en `predictor_agent.py:47-55`. |
| **ML-02** | Umbrales Calibrados | Umbrales exactos `CP0=0.285`, `CP1=0.340`, `CP2=0.495`, `CP3=0.765` y banda preventiva amarilla `0.75 * umbral` | `VERIFIED` | `predictor_agent.py:18-23, 94-101`, `04_Modelo/umbrales_calibrados.json`, `test_agents.py`. |
| **ML-03** | Variables por Checkpoint | `CP0` (15 vars), `CP1` (25 vars incl. `PROBA_CP0`), `CP2` (37 vars), `CP3` (46 vars) | `VERIFIED` | `predictor_agent.py:25-45`, `preprocessing_agent.py:73-143`, `coordinator_agent.py:114-121`. |
| **ML-04** | Prioridad de Sensibilidad (`Recall`) | Modelos calibrados para `Recall >= 0.80` en validación 2023 y verificados en test 2024–2025 | `VERIFIED` | `04_Modelo/benchmark_modelos_checkpoints.csv` (`Recall` RF: `0.8590`, `0.8750`, `0.8462`, `0.8846`). |
| **ML-05** | Alimentación de Features Históricos en Runtime | Alimentación de las 9 variables basales desde la BD o el formulario | `PARTIALLY VERIFIED` | 5 provienen del perfil del alumno (`IRA_ACUM`, `REPROBACIONES_PREVIAS`, `CARGA_ACADEMICA`, `ES_REPETICION`, `SEMESTRES_DESDE_INGRESO`); 4 usan priors institucionales fijos en runtime (`db.py:1489-1496`, `HALL-F5-03`). |
| **XAI-01** | Explicabilidad Local SHAP | Cálculo dinámico en tiempo real con `shap.TreeExplainer` por estudiante y checkpoint | `VERIFIED` | `src/agents/xai_agent.py:55-114`, `test_xai_audit.py`. |
| **XAI-02** | Coherencia Visual SHAP (`impact` vs `value`) | Signo, color y longitud de barra determinados por `impact` (valor SHAP), mostrando `value` como dato observado | `VERIFIED` | `src/agents/xai_agent.py:117-201`, `app.py:1483-1495, 1692-1703`, `test_critical_fixes.py:146-210`. |
| **XAI-03** | Fidelidad SHAP vs LIME | Validación experimental de fidelidad entre explicaciones SHAP y LIME | `PARTIALLY VERIFIED` | Validado offline en `04_Modelo/fidelidad_shap_lime_cp1.json` (`r = 0.7778`, `N=100`); LIME no se ejecuta en tiempo real en `xai_agent.py` y `db.py:902, 1544` guarda `fidelidad_r=0.96` constante (`HALL-F5-04`). |
| **SEG-01** | Anonimización CUI (`HMAC-SHA256`) | Cero CUI en texto plano en `sata_unsa.db`, logs, mensajes del bus y reportes PDF | `VERIFIED` | `crypto.py:29-53`, `academic_service.py:145`, `db.py:737`, `test_critical_fixes.py:216-272`. |
| **SEG-02** | Hashing de Contraseñas | `PBKDF2-HMAC-SHA256` con 100,000 iteraciones, sal de 16 bytes y `hmac.compare_digest` | `VERIFIED` | `src/security/crypto.py:56-81`, verificado en tabla `usuarios` de `sata_unsa.db`. |
| **SEG-03** | Control de Acceso RBAC por Rol | Aislamiento estricto para `ESTUDIANTE`, `AUTORIDAD` (solo agregados) y `ADMIN` (solo técnico/catálogo) | `PARTIALLY VERIFIED` | `ESTUDIANTE`, `AUTORIDAD` y `ADMIN` bloqueados con `AuthorizationError` (`db.py:1097-1105`); en `DOCENTE`, `access_control.py:66-67` tiene `pass` para cursos de otros docentes (`HALL-F5-02`). |
| **DB-01** | Transaccionalidad y Modo WAL | SQLite con `PRAGMA journal_mode=WAL`, `foreign_keys=ON` y `BEGIN IMMEDIATE / ROLLBACK` en carga masiva | `VERIFIED` | `src/database/db.py:24-31, 711-973`, `test_critical_fixes.py:274-322`. |
| **DB-02** | Idempotencia de Sembrado Inicial | `seed_initial_data()` no debe duplicar registros al reimportar `src.database.db` | `PARTIALLY VERIFIED` | Idempotente en `usuarios`, `matriculas`, `predicciones`, `mensajes_bus` y `tutorias`, pero inserta filas repetidas en `perfil_semestre` y `explicaciones` al no tener clave única (`HALL-F5-05`). |
| **ACA-01** | Simulador de Examen Sustitutorio | Reemplazo normativo exclusivo de `min(EP1, EP2, EP3)`, jamás `EC1`, `EC2` ni `EC3` | `VERIFIED` | `src/services/academic_service.py:57-127`, `app.py:2082-2152`, `test_high_priority_fixes.py:303-331`. |
| **ACA-02** | Redondeo Normativo e Imposibilidad Matemática | Nota mínima aprobatoria ordinaria `10.50` (redondea a `11`) y alerta cuando se requiere `> 20.0` | `PARTIALLY VERIFIED` | `academic_service.py:104, 125` y `preprocessing_agent.py:141` usan `10.5`, pero `preprocessing_agent.py:117, 130` usa `11.0 - PUNTOS_F1/F2` para `NOTA_MIN_PEND` (`HALL-F5-01`). |
| **FUN-01** | Flujos Interactivos por Rol y Exportación PDF | Selectores dinámicos, registro de notas con recálculo SMA, bitácora de tutorías, PDF y encuestas SUS/TAM | `VERIFIED` | `app.py:1070-2410`, `pdf_generator.py:29-227`, `test_high_priority_fixes.py:43-351`. |
| **VIS-01** | Identidad Visual, UX y Diseño Responsive | Paleta institucional (`--granate`, `--dorado`), contraste WCAG AA, cero CSS crudo y soporte `1440×900` a `390×844` | `VERIFIED` | `app.py:89-990`, verificado en 16 capturas multi-rol y multi-resolución en `evidencias/07_post_correccion_visual/`. |

---

## 5. AUDITORÍA DE ARQUITECTURA MULTIAGENTE

### 5.1. Matriz de Verificación de los 7 Agentes del Sistema
Se verificó en el código fuente (`src/agents/`) que los **7 agentes inteligentes** están implementados como clases independientes que heredan de `BaseAgent` (`src/agents/base_agent.py:10-27`), se registran en el `MessageBus` durante la inicialización de `CoordinatorAgent` (`src/agents/coordinator_agent.py:27-35`) y se comunican mediante instancias de `AgentMessage` (`src/messaging/message.py:10-37`):

| # | Agente | Archivo y Línea | Clase (`BaseAgent`) | Registro en `MessageBus` | Performativas Emitidas / Recibidas | Tópicos (`action`) Verificados | Persistencia en `mensajes_bus` | Estado |
| :-: | :--- | :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| 1 | **Agente de Ingestión** | `src/agents/ingestion_agent.py:13` | `IngestionAgent(BaseAgent)` | Sí (`coordinator_agent.py:29`) | Recibe: `REQUEST`<br>Emite: `INFORM`, `FAILURE` | `INGEST`, `INGEST_OK`, `VALIDATION_FAILURE` | Sí (`coordinator_agent.py:85-92`) | `VERIFIED` |
| 2 | **Agente de Preprocesamiento** | `src/agents/preprocessing_agent.py:13` | `PreprocessingAgent(BaseAgent)` | Sí (`coordinator_agent.py:30`) | Recibe: `REQUEST`<br>Emite: `INFORM`, `FAILURE` | `PREPROCESS`, `FEATURES_CP0..CP3` | Sí (`coordinator_agent.py:107-112`) | `VERIFIED` |
| 3 | **Agente Predictor ML** | `src/agents/predictor_agent.py:15` | `PredictorAgent(BaseAgent)` | Sí (`coordinator_agent.py:31`) | Recibe: `REQUEST`<br>Emite: `INFORM`, `FAILURE` | `PREDICT`, `PREDICT_CP0..CP3` | Sí (`coordinator_agent.py:140-145`) | `VERIFIED` |
| 4 | **Agente Explicativo XAI** | `src/agents/xai_agent.py:42` | `XaiAgent(BaseAgent)` | Sí (`coordinator_agent.py:32`) | Recibe: `REQUEST`<br>Emite: `INFORM`, `FAILURE` | `EXPLAIN`, `SHAP_CP0..CP3` | Sí (`coordinator_agent.py:157-162`) | `VERIFIED` |
| 5 | **Agente de Recomendación** | `src/agents/recommendation_agent.py:12` | `RecommendationAgent(BaseAgent)` | Sí (`coordinator_agent.py:33`) | Recibe: `REQUEST`<br>Emite: `PROPOSE`, `FAILURE` | `RECOMMEND`, `PROPOSE_TUTORIA_CP0..CP3` | Sí (`coordinator_agent.py:175-180`) | `VERIFIED` |
| 6 | **Agente de Alertas** | `src/agents/alert_agent.py:12` | `AlertAgent(BaseAgent)` | Sí (`coordinator_agent.py:34`) | Recibe: `REQUEST`<br>Emite: `INFORM`, `FAILURE` | `GENERATE_ALERT`, `ALERT_ALTO`, `ALERT_MEDIO`, `ALERT_BAJO` | Sí (`coordinator_agent.py:194-199`) | `VERIFIED` |
| 7 | **Agente Coordinador** | `src/agents/coordinator_agent.py:22` | `CoordinatorAgent(BaseAgent)` | Sí (`coordinator_agent.py:24`) | Emite: `REQUEST`<br>Recibe: `INFORM`, `PROPOSE`, `FAILURE` | Orquestación de los 6 pasos del protocolo SMA | Sí (`coordinator_agent.py:217-229`) | `VERIFIED` |

### 5.2. Auditoría del Bus de Mensajes FIPA-ACL (`src/messaging/bus.py` y `message.py`)
- **Colas Desacopladas:** `MessageBus` (`src/messaging/bus.py:17-21`) mantiene un diccionario `_queues: dict[str, queue.Queue]` donde cada agente tiene su propia cola FIFO thread-safe.
- **Trazabilidad de las 4 Performativas FIPA-ACL:**
  - `REQUEST`: Enviada por `CoordinatorAgent` hacia cada uno de los 6 agentes especialistas, y por `TutoriaUI` hacia `AlertAgent` al programar una tutoría (`db.py:1308`).
  - `INFORM`: Enviada por `IngestionAgent`, `PreprocessingAgent`, `PredictorAgent`, `XaiAgent` y `AlertAgent` al completar satisfactoriamente su tarea, y por `TutoriaUI` hacia `RecommendationAgent` al registrar una tutoría realizada (`db.py:1372`).
  - `PROPOSE`: Enviada por `RecommendationAgent` (`src/agents/recommendation_agent.py:27-35`) al proponer acciones pedagógicas contextualizadas según los factores SHAP de riesgo.
  - `FAILURE`: Enviada por `IngestionAgent` (`src/agents/ingestion_agent.py:33-38`) cuando un registro presenta datos fuera de rango (p. ej. `EC1 > 20.0`, `IRA_ACUM > 20.0` o ausencia de identificadores), deteniendo el flujo en `CoordinatorAgent` y persistiendo la traza de fallo en `mensajes_bus` (`coordinator_agent.py:85-97`).
- **Sanitización Automática de PII:** Tanto `MessageBus.publish()` (`src/messaging/bus.py:55-61`) como `CoordinatorAgent` (`src/agents/coordinator_agent.py:219-225`) eliminan cualquier campo sensible (`nombre`, `apellidos`, `dni`, `correo`, `email`, `telefono`) y conservan únicamente `cui_hash`, `curso`, `checkpoint`, `action` y `performative`.
- **Observación Arquitectónica (`HALL-F5-06`, Severidad `LOW`):** Si bien el paso de mensajes se realiza estrictamente a través de `MessageBus.publish()` y `queue.Queue`, el método `CoordinatorAgent.analyze_student_risk()` (`src/agents/coordinator_agent.py:66-205`) invoca secuencialmente `self.send(...) -> agent.receive() -> agent.handle_message() -> self.receive()` dentro del mismo hilo de ejecución de Python. Para el volumen actual de una escuela profesional (EPIS-UNSA) este diseño híbrido (colas FIPA-ACL con despacho síncrono) garantiza determinismo y una sobrecarga de bus mínima (`overhead_bus_ms < 0.5 ms`), aunque no explota concurrencia asíncrona multi-hilo entre agentes.

---

## 6. AUDITORÍA DE MACHINE LEARNING

### 6.1. Verificación de Modelos Serializados, Variables y Umbrales Calibrados (CP0–CP3)
Se inspeccionaron directamente los artefactos en `04_Modelo/`, el script de entrenamiento `02_Scripts/train_checkpoint_models.py` y el agente `PredictorAgent` (`src/agents/predictor_agent.py:15-110`):

| Checkpoint | Momento Académico | Archivo Serializado `.joblib` | N.° de Variables (`Features`) | Composición del Vector de Entrada | Umbral Calibrado (`ROJO`) | Banda Preventiva (`AMARILLO`: `0.75 × Th`) | Apilamiento (`Stacking`) |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| **CP0** | Matrícula (Semana 1) | `04_Modelo/random_forest_cp0.joblib` | **15** | 9 variables históricas (`IRA_ACUM`, `TASA_APROB_ACUM`, `REPROBACIONES_PREVIAS`, `CARGA_ACADEMICA`, `ES_REPETICION`, `SEMESTRES_DESDE_INGRESO`, `DIFICULTAD_CURSO_HIST`, `DIFICULTAD_DOCENTE_HIST`, `DIFICULTAD_CURSO_DOCENTE_HIST`) + 6 banderas `*_SIN_DATO`. | **`0.285`** (28.5%) | `[0.2138, 0.2850[` | Base del apilamiento (`PROBA_CP0`). |
| **CP1** | Cierre Fase 1 (`EC1`, `EP1`) | `04_Modelo/random_forest_cp1.joblib` | **25** | 15 vars `CP0` + `PROBA_CP0` + 9 vars Fase 1 (`EC1`, `EP1`, `EC1_AUSENTE`, `EP1_AUSENTE`, `PUNTOS_F1`, `PROM_F1`, `PUNTOS_FALT_F1`, `NOTA_MIN_PEND_F1`, `IMPOSIBLE_APROBAR_F1`). | **`0.340`** (34.0%) | `[0.2550, 0.3400[` | Consume `PROBA_CP0` calculada en tiempo real por `random_forest_cp0` (`coordinator_agent.py:114-121`). |
| **CP2** | Cierre Fase 2 (`EC2`, `EP2`) | `04_Modelo/random_forest_cp2.joblib` | **37** | 25 vars `CP1` + 12 vars Fase 2 (`EC2`, `EP2`, `EC2_AUSENTE`, `EP2_AUSENTE`, `PUNTOS_F2`, `PROM_F2`, `TENDENCIA_F1_F2`, `CAIDA_ABRUPTA_F2`, `PUNTOS_FALT_F2`, `NOTA_MIN_PEND_F2`, `IMPOSIBLE_APROBAR_F2`, `TOTAL_AUSENCIAS_F2`). | **`0.495`** (49.5%) | `[0.3712, 0.4950[` | Incluye `PROBA_CP0` + trayectoria dinámica `F1 -> F2`. |
| **CP3** | Pre-Sustitutorio (`EC3`, `EP3`) | `04_Modelo/random_forest_cp3.joblib` | **46** | 37 vars `CP2` + 9 vars Fase 3 (`EC3`, `EP3`, `EC3_AUSENTE`, `EP3_AUSENTE`, `PUNTOS_F3`, `PROM_FINAL_EST`, `MIN_EP_SUSTI`, `REQUIERE_SUSTI`, `YA_APROBADO_CP3`). | **`0.765`** (76.5%) | `[0.5738, 0.7650[` | Evalúa estado pre-sustitutorio antes del cierre de acta. |

### 6.2. Contraste de Métricas del Benchmark (`04_Modelo/benchmark_modelos_checkpoints.csv`)
El protocolo experimental implementado en `02_Scripts/train_checkpoint_models.py` aplica una **partición estrictamente temporal** libre de fuga de datos (*data leakage*):
- **Entrenamiento (`Train`):** Semestres `<= 2022` (con validación cruzada `TimeSeriesSplit(n_splits=5)`).
- **Validación (`Val`):** Semestre `2023` (`N = 2,749`, `230` reprobados), utilizado exclusivamente para calibrar los umbrales de decisión sujetos a la restricción pedagógica `Recall >= 0.80`.
- **Prueba Independiente (`Test`):** Semestres `2024–2025` (`N = 4,948` matrículas, `312` reprobados reales, tasa base de reprobación `6.31%`).

A continuación se presenta la tabla íntegra de resultados verificados en `04_Modelo/benchmark_modelos_checkpoints.csv` y `04_Modelo/matrices_confusion_checkpoints.json`:

| Checkpoint | Algoritmo Evaluado | Umbral Calibrado | Accuracy | Precision | Recall (Sensibilidad) | F1-Score | ROC-AUC | PR-AUC | Especificidad | Matriz de Confusión Test (`TP / FP / TN / FN`) | Reducción FP vs CP0 |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CP0** | **Random Forest (Seleccionado)** | **0.285** | **0.7399** | **0.1757** | **0.8590** | **0.2918** | **0.8702** | **0.3519** | **0.7319** | `268 / 1257 / 3409 / 44` | `0.00%` |
| CP0 | Logistic Regression | 0.280 | 0.7447 | 0.1768 | 0.8462 | 0.2946 | 0.8552 | 0.2683 | 0.7379 | — | `-1.19%` |
| CP0 | HistGradientBoosting | 0.190 | 0.6880 | 0.1566 | 0.9071 | 0.2672 | 0.8599 | 0.3054 | 0.6732 | — | `+20.53%` |
| CP0 | Decision Tree | 0.185 | 0.7199 | 0.1595 | 0.8045 | 0.2662 | 0.7921 | 0.2339 | 0.7142 | — | `+5.25%` |
| CP0 | Gradient Boosting | 0.140 | 0.6481 | 0.1422 | 0.9135 | 0.2457 | 0.8479 | 0.2738 | 0.6302 | — | `+36.44%` |
| **CP1** | **Random Forest (Seleccionado)** | **0.340** | **0.8482** | **0.2772** | **0.8750** | **0.4210** | **0.9309** | **0.5177** | **0.8464** | `273 / 712 / 3924 / 39` | **`-43.36%`** |
| CP1 | HistGradientBoosting | 0.235 | 0.8535 | 0.2848 | 0.8718 | 0.4294 | 0.9317 | 0.5477 | 0.8522 | — | `-45.51%` |
| CP1 | Gradient Boosting | 0.180 | 0.8466 | 0.2762 | 0.8846 | 0.4209 | 0.9288 | 0.5194 | 0.8440 | — | `-42.48%` |
| CP1 | Logistic Regression | 0.370 | 0.8385 | 0.2634 | 0.8718 | 0.4045 | 0.9218 | 0.5067 | 0.8363 | — | `-38.98%` |
| CP1 | Decision Tree | 0.165 | 0.8102 | 0.2286 | 0.8558 | 0.3608 | 0.8891 | 0.3372 | 0.8072 | — | `-28.32%` |
| **CP2** | **Random Forest (Seleccionado)** | **0.495** | **0.9173** | **0.4224** | **0.8462** | **0.5635** | **0.9544** | **0.7131** | **0.9221** | `264 / 361 / 4275 / 48` | **`-71.28%`** |
| CP2 | HistGradientBoosting | 0.315 | 0.9089 | 0.3982 | 0.8654 | 0.5454 | 0.9539 | 0.7229 | 0.9118 | — | `-67.46%` |
| CP2 | Gradient Boosting | 0.285 | 0.9056 | 0.3887 | 0.8622 | 0.5359 | 0.9522 | 0.6929 | 0.9085 | — | `-66.27%` |
| CP2 | Logistic Regression | 0.500 | 0.9181 | 0.4241 | 0.8333 | 0.5622 | 0.9524 | 0.7082 | 0.9239 | — | `-71.92%` |
| CP2 | Decision Tree | 0.145 | 0.8717 | 0.3052 | 0.8365 | 0.4472 | 0.9036 | 0.4892 | 0.8740 | — | `-52.74%` |
| **CP3** | **Random Forest (Seleccionado)** | **0.765** | **0.9806** | **0.8214** | **0.8846** | **0.8519** | **0.9950** | **0.9389** | **0.9871** | `276 / 60 / 4576 / 36` | **`-95.23%`** |
| CP3 | HistGradientBoosting | 0.805 | 0.9808 | 0.8293 | 0.8782 | 0.8530 | 0.9943 | 0.9369 | 0.9877 | — | `-95.54%` |
| CP3 | Gradient Boosting | 0.870 | 0.9794 | 0.8081 | 0.8846 | 0.8446 | 0.9943 | 0.9317 | 0.9858 | — | `-94.75%` |
| CP3 | Logistic Regression | 0.675 | 0.9675 | 0.6962 | 0.8846 | 0.7792 | 0.9899 | 0.8726 | 0.9730 | — | `-90.45%` |
| CP3 | Decision Tree | 0.595 | 0.9741 | 0.7527 | 0.8878 | 0.8147 | 0.9669 | 0.7855 | 0.9799 | — | `-92.76%` |

#### Nota de Trazabilidad Metodológica sobre Métricas CP0
- Los valores preliminares de referencia pre-calibración (`Random Forest F1=0.341, Recall=0.517`, `Logistic Regression F1=0.330`, `Gradient Boosting F1=0.331`, `Decision Tree F1=0.296`) corresponden al script base inicial `02_Scripts/train_models.py` (entrenado únicamente con variables históricas sin calibración de umbral orientada a sensibilidad, donde el umbral por defecto `0.50` producía un `Recall` de solo `51.7%`, dejando sin detectar a casi la mitad de los alumnos que reprobarían).
- Conforme a la justificación metodológica documentada en `Propuesta_Ajuste_Plan_Tesis_Asesora.md` y ejecutada en `02_Scripts/train_checkpoint_models.py`, en un **Sistema de Alerta Temprana Académica** el costo pedagógico e institucional de un **Falso Negativo (`FN`)** —un estudiante en riesgo real de reprobación que no recibe alerta ni tutoría— es drásticamente superior al costo de un **Falso Positivo (`FP`)** —una tutoría preventiva adicional—. Por ello, los umbrales fueron calibrados en el conjunto de validación 2023 para garantizar `Recall >= 0.80`, logrando en `CP0` detectar al **85.90%** de los reprobados (`268` de `312`) desde el primer día de clases (`ROC-AUC = 0.8702`), y reduciendo los falsos positivos en **-43.36% (CP1)**, **-71.28% (CP2)** y **-95.23% (CP3)** conforme ingresan las calificaciones parciales.

### 6.3. Observación sobre Variables Históricas en Tiempo de Ejecución (`HALL-F5-03`)
- Al inspeccionar `evaluate_and_persist_enrollment` (`src/database/db.py:1488-1496`) y `validar_y_procesar_acta_masiva` (`src/services/academic_service.py:167-175`), se observó que de las 9 variables históricas de `CP0`, **5 se alimentan dinámicamente** de los datos del estudiante (`IRA_ACUM`, `REPROBACIONES_PREVIAS`, `CARGA_ACADEMICA`, `ES_REPETICION`, `SEMESTRES_DESDE_INGRESO`), mientras que **4 variables contextuales** que no se solicitan en el formulario de UI (`TASA_APROB_ACUM = 0.85`, `DIFICULTAD_CURSO_HIST = 0.12`, `DIFICULTAD_DOCENTE_HIST = 0.08`, `DIFICULTAD_CURSO_DOCENTE_HIST = 0.10`) se inyectan como constantes por defecto (priors institucionales). Esta observación se documenta como `HALL-F5-03` (`MEDIUM`).

---

## 7. AUDITORÍA DE INTELIGENCIA ARTIFICIAL EXPLICABLE (XAI: SHAP Y LIME)

### 7.1. Auditoría de SHAP en Tiempo de Ejecución (`src/agents/xai_agent.py`)
- **Motor de Explicabilidad:** `XaiAgent._generate_shap_explanations` (`src/agents/xai_agent.py:55-114`) instancia `shap.TreeExplainer(model)` para cada uno de los 4 modelos `RandomForestClassifier` (`CP0`–`CP3`) en el arranque del agente y calcula en tiempo real `explainer.shap_values(df_input)` para cada estudiante evaluado.
- **Extracción de la Clase Positiva (Reprobación = 1):** Maneja correctamente tanto la salida en lista `[shap_clase_0, shap_clase_1]` como tensores tridimensionales `(n_samples, n_features, 2)` de versiones recientes de `shap` (`xai_agent.py:67-75`).
- **Exclusión de Banderas Técnicas:** Filtra las variables instrumentales `*_SIN_DATO` (`xai_agent.py:81-82`) para presentar al docente y al estudiante únicamente factores pedagógicamente accionables, ordenados de mayor a menor según `abs(impact)` (`xai_agent.py:100`).
- **Coherencia Matemática y Visual (`format_shap_factor_for_ui` en `xai_agent.py:117-201`):**
  - El signo (`+` / `-`), la dirección (`Incrementa riesgo` / `Factor protector`), el color (`var(--granate)` / `var(--azul-factor)`) y el ancho relativo de la barra horizontal (`width_pct`) dependen **exclusivamente de `impact` (valor SHAP)**.
  - El valor bruto de la variable (`value`, p. ej. una nota `14.0` o un IRA `11.5`) se formatea únicamente como texto descriptivo `(Valor observado: 14.0)`, evitando que una nota numérica positiva sea confundida con un incremento de riesgo cuando su valor SHAP es negativo (protector).

### 7.2. Auditoría de LIME y Fidelidad Explicativa (`04_Modelo/fidelidad_shap_lime_cp1.json`)
- **Estado Real en el Sistema (`PARTIALLY VERIFIED`):**
  - **En la fase offline de investigación (`04_Modelo/fidelidad_shap_lime_cp1.json`):** Se verificó la existencia del artefacto experimental de validación cruzada entre SHAP y LIME en el Checkpoint 1 sobre `n_estudiantes = 100` y `n_variables = 25` (`2,500` pares analizados), obteniendo una correlación de Pearson de **`r = 0.7778`** (`Interpretación: Alta consistencia entre SHAP y LIME (r >= 0.75)`) y una coincidencia en la dirección del impacto de **`77.78%`**.
  - **En la aplicación en tiempo de ejecución (`src/agents/xai_agent.py` y `requirements.txt`):** La librería `lime` **no está instalada ni se invoca dinámicamente en tiempo real** al evaluar a un estudiante; la aplicación utiliza exclusivamente `shap.TreeExplainer` (lo cual es técnicamente óptimo para árboles de decisión por su exactitud teórica y baja latencia `~38 ms`).
  - **Observación de Persistencia (`HALL-F5-04`, Severidad `MEDIUM`):** En `src/database/db.py` (líneas `350`, `902`, `907`, `922` y `1544`), al persistir registros en la tabla `explicaciones`, la columna `fidelidad_r` se guarda con el literal constante `0.96` en lugar de referenciar la correlación empírica `0.7778` de `04_Modelo/fidelidad_shap_lime_cp1.json` o calcular una métrica de completitud aditiva local de SHAP.

---

## 8. AUDITORÍA DE SEGURIDAD Y PRIVACIDAD

### 8.1. Anonimización Irreversible de Identidad (`HMAC-SHA256`)
- **Implementación (`src/security/crypto.py:13-53`):**
  - Utiliza una llave secreta institucional de 32 bytes (`os.urandom(32)`) almacenada en `src/security/.salt_secret` (excluida de Git mediante `.gitignore:34`).
  - `hash_cui(cui_raw)` normaliza el CUI (`strip().upper()`) y calcula `hmac.new(secret_key, cui_clean.encode("utf-8"), hashlib.sha256).hexdigest()[:16].upper()`, generando un identificador pseudónimo irreversible de 16 caracteres hexadecimales (p. ej. `20220638` -> `E7BB88B1B2BDD47F`).
  - `ensure_cui_hash(value)` (`crypto.py:39-53`) previene el doble hashing verificando si el valor ya es un digest hexadecimal de 16 caracteres.
- **Verificación Forense sobre `sata_unsa.db`:**
  - En la consulta en modo solo lectura sobre `src/database/sata_unsa.db`, se comprobó que las tablas `usuarios`, `estudiantes`, `perfil_semestre`, `matriculas`, `mensajes_bus` y `tutorias` almacenan únicamente los hashes `E7BB88B1B2BDD47F` y `2EE41C30116CFC4B`, con **cero CUI en texto plano**.

### 8.2. Autenticación y Almacenamiento de Contraseñas (`PBKDF2-HMAC-SHA256`)
- **Implementación (`src/security/crypto.py:56-81`):**
  - `hash_password(password)` genera una sal criptográfica aleatoria de 16 bytes (`os.urandom(16).hex()`) y aplica `hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()` con **100,000 iteraciones**, almacenando el formato `pbkdf2:sha256:100000$<salt>$<hash>`.
  - `verify_password(password_attempt, stored_hash)` utiliza comparación en tiempo constante `hmac.compare_digest(computed_hash, expected_hash)` (`crypto.py:79`) para mitigar ataques de temporización (*timing attacks*).

### 8.3. Control de Acceso Basado en Roles (RBAC) y Privacidad Opt-In
- **Matriz de Permisos Verificada (`src/security/access_control.py` y `src/database/db.py`):**
  - **`ESTUDIANTE`:** Solo puede acceder a su propio `cui_hash` (`validate_student_access` en `access_control.py:42-46`) y a sus propias matrículas (`validate_matricula_ownership` en `access_control.py:61-63`). Si intenta consultar `get_course_students_table()`, recibe `AuthorizationError` (`db.py:1099-1100`). En la terminal FIPA-ACL solo visualiza mensajes que contienen su propio `cui_hash` (`get_bus_messages_for_student` en `db.py:1136-1151`).
  - **`AUTORIDAD`:** Acceso estrictamente agregado por asignatura y sección (`get_course_risk_summary` y `get_course_sections_summary` en `db.py:1012-1087`). Si intenta invocar `get_course_students_table()` o `validate_matricula_ownership()`, se lanza `AuthorizationError` (`db.py:1103-1104`, `access_control.py:57-59`).
  - **`ADMIN`:** Acceso estrictamente técnico (métricas de latencia OBJ5, catálogo de asignaturas y terminal global FIPA-ACL). Bloqueado con `AuthorizationError` frente a perfiles individuales y tablas nominales de estudiantes (`access_control.py:39-40, 54-55`, `db.py:1101-1102`).
  - **Privacidad Opt-In (`comparte_con_tutor`):** Cuando un estudiante desactiva la casilla de compartir datos con el tutor (`comparte_con_tutor = 0`), `get_course_students_table()` (`db.py:1126-1128`) enmascara su identificador como `RES-XXXXXX` y marca su estado como `"No compartido"`.
- **Observación de Seguridad en Alcance Docente (`HALL-F5-02`, Severidad `MEDIUM`):**
  - En `src/security/access_control.py:66-67`, dentro de `validate_matricula_ownership()`, la rama para el rol `DOCENTE` contiene:
    ```python
    elif rol == "DOCENTE" and mat_dict["docente"] != username and username not in ["docente_demo", "DOCENTE_EPIS", "admin"]:
        pass  # Permitido en demo / supervisión
    ```
  - Asimismo, `validar_y_procesar_acta_masiva()` (`src/services/academic_service.py:129`) no recibe `current_user` para validar permisos en la capa de servicio (aunque la pestaña en `app.py` solo es accesible tras autenticarse). Para un despliegue en producción real con múltiples docentes titulares, esa cláusula `pass` debe reemplazarse por `raise AuthorizationError(...)` para que cada docente acceda exclusivamente a las secciones bajo su cargo.

### 8.4. Escaneo Estático de Seguridad (`bandit -r src app.py`)
- **Líneas de código auditadas:** `5,417`
- **Vulnerabilidades Severidad Alta (`High`):** `0`
- **Vulnerabilidades Severidad Media (`Medium`):** `0`
- **Observaciones Severidad Baja (`Low`):** `2` ocurrencias de `B110:try_except_pass` en `src/agents/coordinator_agent.py` (líneas `95` y `232`), correspondientes a bloques de cierre seguro de conexión SQLite en el registro opcional de telemetría.

---

## 9. AUDITORÍA DE PERSISTENCIA Y BASE DE DATOS (SQLITE)

### 9.1. Esquema Relacional y Configuración de Concurrencia
En `src/database/db.py:24-248`, la base de datos `src/database/sata_unsa.db` define **13 tablas relacionales** con soporte de concurrencia mediante:
- `PRAGMA journal_mode=WAL;` (`db.py:27`)
- `PRAGMA synchronous=NORMAL;` (`db.py:28`)
- `PRAGMA foreign_keys=ON;` (`db.py:29`)
- `timeout=20.0` segundos (`db.py:26`)

| # | Tabla SQLite | Clave Primaria | Claves Foráneas / Restricciones | Filas en `sata_unsa.db` (Modo Lectura) | Estado |
| :-: | :--- | :--- | :--- | :---: | :---: |
| 1 | `usuarios` | `id` (AUTOINCREMENT) | `UNIQUE(username)` | 5 | `VERIFIED` |
| 2 | `estudiantes` | `cui_hash` (TEXT) | — | 2 | `VERIFIED` |
| 3 | `perfil_semestre` | `id` (AUTOINCREMENT) | `FK(cui_hash) -> estudiantes(cui_hash)` | 56 *(ver `HALL-F5-05`)* | `PARTIALLY VERIFIED` |
| 4 | `catalogo_cursos` | `id` (AUTOINCREMENT) | `UNIQUE(nombre)` | 9 | `VERIFIED` |
| 5 | `catalogo_docentes` | `id` (AUTOINCREMENT) | `UNIQUE(nombre)` | 5 | `VERIFIED` |
| 6 | `matriculas` | `id` (AUTOINCREMENT) | `FK(cui_hash) -> estudiantes(cui_hash)` | 1 | `VERIFIED` |
| 7 | `notas` | `id` (AUTOINCREMENT) | `UNIQUE(matricula_id, evaluacion)`, `FK(matricula_id)` | 2 | `VERIFIED` |
| 8 | `historial_cambios` | `id` (AUTOINCREMENT) | `FK(matricula_id) -> matriculas(id)` | 0 | `VERIFIED` |
| 9 | `predicciones` | `id` (AUTOINCREMENT) | `FK(matricula_id) -> matriculas(id)` | 1 | `VERIFIED` |
| 10 | `explicaciones` | `id` (AUTOINCREMENT) | `FK(prediccion_id) -> predicciones(id)` | 56 *(ver `HALL-F5-05`)* | `PARTIALLY VERIFIED` |
| 11 | `mensajes_bus` | `id` (AUTOINCREMENT) | — | 12 | `VERIFIED` |
| 12 | `metricas_tecnicas` | `id` (AUTOINCREMENT) | — | 0 | `VERIFIED` |
| 13 | `encuestas` | `id` (AUTOINCREMENT) | — | 0 | `VERIFIED` |
| 14 | `tutorias` | `id` (AUTOINCREMENT) | `FK(matricula_id) -> matriculas(id)` | 1 | `VERIFIED` |

### 9.2. Auditoría de las Funciones Críticas de Persistencia
Se verificaron individualmente las funciones clave exigidas en la especificación:

1. **`schedule_tutoring_session` (`src/database/db.py:1256-1315`):** Valida permisos (`validate_matricula_ownership`), comprueba obligatoriedad de fecha y observación (`>= 5` caracteres), conserva el estado previo del checklist (`accion_1_ok..accion_3_ok`), inserta en `tutorias` con estado `'PROGRAMADA'` y registra un mensaje FIPA-ACL `REQUEST` (`PROGRAMAR_TUTORIA`) en `mensajes_bus`. **Estado: `VERIFIED`.**
2. **`register_tutoring_session` (`src/database/db.py:1317-1378`):** Valida permisos, fecha, estado (`PROGRAMADA`, `REALIZADA`, `SEGUIMIENTO`) y observaciones (`>= 5` caracteres), persiste la sesión y el estado de las 3 casillas (`accion_1..3`) en `tutorias`, y registra un mensaje FIPA-ACL `INFORM` (`REGISTRAR_TUTORIA`) en `mensajes_bus`. **Estado: `VERIFIED`.**
3. **`get_tutoring_history` (`src/database/db.py:1240-1253`):** Valida propiedad de la matrícula y retorna la bitácora histórica ordenada cronológicamente (`ORDER BY id DESC`). **Estado: `VERIFIED`.**
4. **`get_tutoring_checklist_state` (`src/database/db.py:1213-1237`):** Recupera el estado booleano persistido de las 3 casillas pedagógicas (`accion_1`, `accion_2`, `accion_3`) y su fecha de actualización desde el último registro en `tutorias`. **Estado: `VERIFIED`.**
5. **`update_student_consent` (`src/database/db.py:474-485`):** Actualiza en SQLite las columnas `consentimiento_aceptado`, `comparte_con_tutor` y `fecha_consentimiento` para el `cui_hash` autenticado. Conectada a la vista `Configuración e Inscripción` (`app.py:2165-2195`). **Estado: `VERIFIED`.**
6. **`save_grade` (`src/database/db.py:596-635`):** Verifica propiedad (`validate_matricula_ownership`), comprueba si la nota o condición de ausencia cambió respecto al valor previo y, solo en caso de modificación real, inserta automáticamente el registro de auditoría en `historial_cambios` antes de actualizar `notas`. **Estado: `VERIFIED`.**
7. **`evaluate_and_persist_enrollment` (`src/database/db.py:1453-1546`):** Reconstruye el payload académico de la matrícula tras un cambio de nota, ejecuta el ciclo completo de los 7 agentes (`coordinator_agent.analyze_student_risk(payload, persist_telemetry=True)`) y actualiza sin duplicar la predicción y explicaciones SHAP en `predicciones` y `explicaciones`. **Estado: `VERIFIED`.**
8. **`get_grade_change_history` (`src/database/db.py:1198-1210`):** Valida permisos y retorna el historial de rectificaciones de nota (`evaluacion`, `valor_previo`, `valor_nuevo`, `motivo`, `fecha_cambio`). **Estado: `VERIFIED`.**
9. **`persist_acta_row_transactional` (`src/database/db.py:711-973`):** Ejecuta `BEGIN IMMEDIATE;` (`db.py:762`) para persistir atómicamente catálogos, estudiante anonimizado, perfil semestral, matrícula, notas parciales, historial de cambios, predicción, explicación SHAP, mensajes FIPA-ACL y métricas técnicas OBJ5, con `conn.rollback()` automático (`db.py:970`) ante cualquier excepción. **Estado: `VERIFIED`.**

### 9.3. Hallazgo en Sembrado Inicial (`HALL-F5-05`, Severidad `MEDIUM`)
- Al inspeccionar `src/database/sata_unsa.db` en modo lectura, se detectó que `perfil_semestre` y `explicaciones` tienen **56 filas** cada una, mientras que `matriculas` y `predicciones` tienen **1 fila**.
- **Causa raíz exacta:** En `src/database/db.py:1635-1636`, `init_database()` y `seed_initial_data()` se invocan automáticamente al importar el módulo `src.database.db`. Dentro de `seed_initial_data()`, las sentencias `INSERT OR IGNORE INTO perfil_semestre` (`db.py:313-316`) e `INSERT OR IGNORE INTO explicaciones` (`db.py:349-351`) no especifican la clave primaria `id = 1`, y dichas tablas carecen de restricción `UNIQUE(cui_hash, semestre)` y `UNIQUE(prediccion_id)`. Por ello, cada vez que se importa `db.py` (en arranques del servidor o ejecuciones previas), SQLite inserta una nueva fila con `id` autoincremental. Aunque las consultas `ORDER BY id DESC LIMIT 1` en `get_student_profile` (`db.py:495`) y `get_latest_prediction` (`db.py:986`) devuelven siempre el registro correcto sin afectar la funcionalidad visible, debe añadirse verificación de existencia previa en `seed_initial_data()`.

---

## 10. AUDITORÍA DE NORMATIVA ACADÉMICA EPIS-UNSA

### 10.1. Regla del Examen Sustitutorio (`calcular_simulacion_sustitutorio`)
- **Ubicación:** `src/services/academic_service.py:57-127`, integrada en `app.py:2082-2152`.
- **Verificación Normativa (`VERIFIED`):**
  - Identifica exclusivamente los tres Exámenes Parciales `{"EP1": ep1, "EP2": ep2, "EP3": ep3}` (`academic_service.py:88`).
  - Selecciona el menor valor mediante `min(eps, key=eps.get)` (`academic_service.py:89`). **Jamás evalúa ni reemplaza Evaluaciones Continuas (`EC1`, `EC2`, `EC3`)**, cumpliendo estrictamente el reglamento de evaluación de la UNSA.
  - Calcula la nota mínima requerida en el Examen Sustitutorio para alcanzar `10.50` puntos ponderados (`academic_service.py:104-110`):
    $$\text{Nota Necesaria Susti} = \max\left(0.0,\; \frac{10.5 - \text{Puntos Sin EP Menor}}{\text{Peso}_{\text{EP Menor}} / 100}\right)$$
  - Si el estudiante simula una nota específica (`nota_susti_simulada`), solo reemplaza el examen parcial más bajo si `nota_susti_simulada > valor_ep_min` (`academic_service.py:114`).

### 10.2. Regla de Redondeo Aprobatorio (`10.50 -> 11`) e Imposibilidad Matemática Ordinaria
- **Discrepancia Interna Detectada entre `11.0` y `10.5` (`HALL-F5-01`, Severidad `MEDIUM`):**
  - En la normativa de la UNSA, el promedio final aprobatorio de `11` se alcanza desde **`10.50`** por redondeo al entero superior en el acta final.
  - En `src/services/academic_service.py:104, 125` y en `src/agents/preprocessing_agent.py:141` (`YA_APROBADO_CP3 = 1 if PROM_FINAL_EST >= 10.5 else 0`), el sistema utiliza correctamente **`10.5`**.
  - Sin embargo, en `src/agents/preprocessing_agent.py:117-119` (Fase 1) y `130-132` (Fase 2), heredado de `02_Scripts/build_checkpoint_features.py:102, 115`, el cálculo de puntos faltantes e imposibilidad matemática se realiza respecto a **`11.0`** en lugar de **`10.5`**:
    ```python
    f["PUNTOS_FALT_F1"] = max(0.0, 11.0 - f["PUNTOS_F1"])
    f["NOTA_MIN_PEND_F1"] = f["PUNTOS_FALT_F1"] / (peso_pend_f1 / 100.0)
    f["IMPOSIBLE_APROBAR_F1"] = 1 if f["NOTA_MIN_PEND_F1"] > 20.0 else 0
    ```
  - **Impacto Académico:** Si al cierre de la Fase 2 (`peso_pend_f2 = 30%`) un estudiante acumula `PUNTOS_F2 = 4.90`, para llegar a `10.50` necesita `5.60 / 0.30 = 18.67` (matemáticamente **posible** en vía ordinaria), pero la fórmula con `11.0` calcula `(11.0 - 4.90) / 0.30 = 20.33 > 20.0`, activando prematuramente la bandera `IMPOSIBLE_APROBAR_F2 = 1` en la franja fronteriza `PUNTOS_F2 ∈ [4.50, 5.00[`. Dado que los modelos `.joblib` fueron entrenados con la definición `11.0 - PUNTOS_F1/F2`, la variable de entrada al modelo debe conservarse para no alterar la distribución de árboles, pero la bandera normativa de negocio (`imposible_ordinario` y `meta_nota_min` mostradas al usuario en `AlertAgent`) debería calcularse sobre `10.50`.

---

## 11. AUDITORÍA FUNCIONAL POR PANTALLA Y ROL

Se verificó la funcionalidad de las **7 vistas del sistema** y sus controles interactivos en `app.py`:

| # | Vista / Pantalla | Roles con Acceso | Componentes y Flujos Auditados | Estado |
| :-: | :--- | :--- | :--- | :---: |
| 0 | **Portal de Login y Registro** (`app.py:1110-1230`) | Público (No autenticado) | Selector rápido de perfiles demo (4 botones), formulario de autenticación `authenticate_user`, modal/sección de registro de estudiante con hash inmediato `register_student_user`. | `VERIFIED` |
| 1 | **Panel de Seguimiento** (`app.py:1245-1565`) | `ESTUDIANTE`, `DOCENTE`, `AUTORIDAD` | **Estudiante:** Tarjetas KPI propias, evolución por checkpoint, factores SHAP y plan de acción.<br>**Docente:** Selectores reales de asignatura y alumno (`get_course_students_table`), KPIs de sección, tabla nominal con estado Opt-In (`Compartido con tutor` / `RES-XXXXXX`), formulario de programación rápida de tutoría (`schedule_tutoring_session`) y descarga de reporte PDF (`generate_intervention_pdf`).<br>**Autoridad:** Mapa de calor agregado por sección y docente (`get_course_sections_summary`) sin acceso a datos individuales. | `VERIFIED` |
| 2 | **Explicabilidad XAI (SHAP)** (`app.py:1566-1745`) | `ESTUDIANTE`, `DOCENTE` | Selector de asignatura y estudiante para el docente (`app.py:1574-1601`), velocímetro circular SVG de probabilidad vs. umbral del checkpoint, gráfico de barras horizontales SHAP (`format_shap_factor_for_ui`) y desglose cuantitativo. | `VERIFIED` |
| 3 | **Tutoría y Plan de Acción** (`app.py:1746-1848`) | `ESTUDIANTE`, `DOCENTE` | Tarjetas de recomendaciones generadas por `RecommendationAgent`, checklist de 3 compromisos pedagógicos hidratado desde SQLite (`get_tutoring_checklist_state`), formulario de registro de sesión (`register_tutoring_session`), bitácora histórica (`get_tutoring_history`) y exportación PDF. | `VERIFIED` |
| 4 | **Arquitectura y Bus FIPA-ACL** (`app.py:1849-1988`) | Todos (`ESTUDIANTE` aislado a su propio hash) | Diagrama de los 7 agentes, terminal FIPA-ACL conectada a `mensajes_bus` con badges diferenciados para `REQUEST`, `INFORM`, `PROPOSE` y `FAILURE`, y ficha técnica de latencia/RAM (`get_technical_metrics_summary`). | `VERIFIED` |
| 5 | **Benchmarking ML (CP0–CP3)** (`app.py:1989-2018`) | `DOCENTE`, `AUTORIDAD`, `ADMIN` | Comparativa de los 5 modelos en los 4 checkpoints (`04_Modelo/benchmark_modelos_checkpoints.csv`), curvas de reducción de falsos positivos y matrices de confusión. | `VERIFIED` |
| 6 | **Configuración e Inscripción** (`app.py:2019-2315`) | Todos (pestañas adaptadas por rol) | **Estudiante/Docente:** Registro/rectificación de notas parciales (`save_grade` + `evaluate_and_persist_enrollment` + `get_grade_change_history`) y Simulador de Examen Sustitutorio (`calcular_simulacion_sustitutorio`).<br>**Estudiante:** Consentimiento informado Opt-In (`update_student_consent`), perfil basal (`save_student_profile`) e inscripción de cursos (`enroll_course`).<br>**Docente/Admin:** Carga masiva transaccional de actas CSV (`validar_y_procesar_acta_masiva`) y catálogo curricular EPIS-UNSA. | `PARTIALLY VERIFIED` *(ver `HALL-F5-07`)* |
| 7 | **Evaluación SUS y TAM** (`app.py:2316-2405`) | Todos | Cuestionario SUS completo (10 ítems Likert 1–5 con cálculo estándar de Brooke 0–100) y cuestionario TAM completo (6 ítems: 3 de Utilidad Percibida `PU` + 3 de Facilidad de Uso Percibida `PEOU`, escala 0–100%), ambos persistidos en la tabla `encuestas`. | `VERIFIED` |

- **Observación Funcional Menor (`HALL-F5-07`, Severidad `LOW`):** Cuando un estudiante inscribe una nueva asignatura mediante `enroll_course()` (`app.py:2202-2210`), se crea el registro en la tabla `matriculas` pero no se invoca inmediatamente `evaluate_and_persist_enrollment()` para generar la predicción basal `CP0`. En consecuencia, la nueva asignatura recién aparece en las vistas basadas en `predicciones` (`get_latest_prediction` / `get_course_students_table`) cuando se registra la primera calificación o cuando se procesa un acta.

---

## 12. AUDITORÍA VISUAL, UX Y RESPONSIVE

### 12.1. Sistema de Diseño e Identidad Institucional EPIS-UNSA
Se verificó en `app.py:89-990` y en las capturas del navegador real (`auditoria_visual_funcional/evidencias/07_post_correccion_visual/`) el cumplimiento de los estándares visuales:
- **Paleta Institucional:** Uso consistente de `--granate: #651D32`, `--granate-dark: #4A1525`, `--dorado: #C59B27`, `--superficie: #F4F5F7` y semáforos académicos accesibles (`--rojo-alerta: #D92D20`, `--ambar-alerta: #D97706`, `--verde-alerta: #15803D`).
- **Tipografía:** `Outfit` para encabezados institucionales, `Plus Jakarta Sans` para cuerpo y formularios, y `JetBrains Mono` para hashes `HMAC-SHA256`, trazas FIPA-ACL y métricas numéricas.
- **Limpieza de Chrome Nativo de Streamlit:** Ocultamiento de `#MainMenu`, `footer` y `[data-testid="stToolbar"]` (`app.py:130-154`), conservando accesible el botón de apertura/cierre del panel lateral (`stExpandSidebarButton`) en resoluciones móviles y tablets.
- **Ausencia de Fugas de Código o Texto Truncado:** Cero bloques de CSS/HTML crudo visibles en pantalla y cero títulos truncados con `...` en botones y selectores (`white-space: normal`, `height: auto`).

### 12.2. Matriz de Verificación Multi-Rol y Multi-Resolución
Se auditó el comportamiento visual y de maquetación en las **4 resoluciones estándar** y los **4 roles del sistema**:

| Resolución | Categoría de Dispositivo | Roles Verificados | Comportamiento de Layout, Tablas y Gráficos | Desbordamiento Horizontal (`scrollWidth > innerWidth`) | Estado | Evidencia Gráfica en Repositorio |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| **`1440×900`** | Escritorio Estándar | `ESTUDIANTE`, `DOCENTE`, `AUTORIDAD`, `ADMIN` | Sub-header institucional en 1 fila, 4 tarjetas KPI alineadas con altura uniforme (`min-height: 156px`), paneles SHAP y tablas completas sin recortes. | **No (`0 px`)** | `VERIFIED` | `evidencias/07_post_correccion_visual/01_login_1440x900.png` a `08_admin_1440x900.png` |
| **`1366×768`** | Laptop Estándar | `DOCENTE`, `ESTUDIANTE` | Botones de acción (`Programar Tutoría`, `Exportar Reporte (PDF)`) envuelven texto limpiamente en 2 líneas sin truncamiento. | **No (`0 px`)** | `VERIFIED` | `evidencias/07_post_correccion_visual/09_docente_1366x768.png` |
| **`768×1024`** | Tablet Vertical | `DOCENTE`, `ESTUDIANTE` | Sidebar colapsable, rejilla KPI refluye a `2×2` (`flex: 1 1 calc(50% - 12px)`), tablas con scroll interno contenido. | **No (`0 px`)** | `VERIFIED` | `evidencias/07_post_correccion_visual/10_docente_768x1024.png` |
| **`390×844`** | Móvil (iPhone 13/14) | `LOGIN`, `DOCENTE`, `ESTUDIANTE` | Columnas de Streamlit apiladas al 100% (`min-width: 100%`), tarjetas KPI apiladas verticalmente (`1×4`), velocímetro SVG y barras SHAP escalables al ancho móvil. | **No (`0 px`)** | `VERIFIED` | `evidencias/07_post_correccion_visual/11_login_390x844.png` a `13_estudiante_390x844.png` |

---

## 13. PRUEBAS AUTOMATIZADAS Y COBERTURA DE CÓDIGO

### 13.1. Resumen de Ejecución de la Suite de Pruebas
- **Comando verificado:** `pytest --cov=src --cov=app -q`
- **Resultado:** **`117 passed, 0 failed`** en `134.19 s` (8 archivos de prueba en `tests/`).
- **Aislamiento de Base de Datos:** Todas las pruebas se ejecutan bajo el fixture `isolated_test_database` (`tests/conftest.py:21-36`), que redirige `src.database.db.DB_PATH` a un directorio temporal de `pytest` (`tmp_path_factory.mktemp("sata_test_db")`).

### 13.2. Desglose Exacto de Cobertura por Módulo (`python -m coverage report -m`)

| Módulo / Archivo | Sentencias (`Stmts`) | No Cubiertas (`Miss`) | Cobertura (`Cover`) | Líneas Faltantes Exactas (`Missing`) |
| :--- | :---: | :---: | :---: | :--- |
| `src/__init__.py` | 0 | 0 | **100%** | — |
| `src/agents/__init__.py` | 9 | 0 | **100%** | — |
| `src/agents/alert_agent.py` | 35 | 0 | **100%** | — |
| `src/agents/base_agent.py` | 16 | 0 | **100%** | — |
| `src/agents/predictor_agent.py` | 50 | 2 | **96%** | `62, 91` |
| `src/agents/preprocessing_agent.py` | 83 | 3 | **96%** | `61-62, 104` |
| `src/agents/coordinator_agent.py` | 128 | 6 | **95%** | `38, 62, 95-96, 232-233` |
| `src/agents/recommendation_agent.py` | 45 | 5 | **89%** | `52, 57, 68, 78, 85` |
| `src/agents/xai_agent.py` | 91 | 16 | **82%** | `82, 88, 92, 145-147, 157-158, 164-166, 173-174, 180, 184, 188` |
| `src/agents/ingestion_agent.py` | 84 | 20 | **76%** | `69, 72-76, 82, 84-88, 94, 96-100, 106, 108-112` |
| `src/database/db.py` | 567 | 57 | **90%** | `416-423, 428-463, 506-515, 550-551, 670-688, 858-864, 904, 990, 1226, 1266, 1268, 1276, 1333, 1335, 1345, 1414, 1439-1442, 1467-1468, 1515, 1529` |
| `src/messaging/bus.py` | 52 | 7 | **87%** | `34, 39, 42-43, 60, 64, 72` |
| `src/messaging/message.py` | 14 | 2 | **86%** | `27, 37` |
| `src/reports/pdf_generator.py` | 150 | 4 | **97%** | `19, 191-192, 209` |
| `src/security/access_control.py` | 38 | 6 | **84%** | `21, 45, 55, 63, 67, 110` |
| `src/security/crypto.py` | 44 | 6 | **86%** | `23-26, 80-81` |
| `src/services/academic_service.py` | 176 | 30 | **83%** | `41-44, 190-195, 201, 220, 231, 233, 253-254, 269-271, 280-283, 292-295, 308-309, 318-319, 404-410` |
| `app.py` | 697 | 151 | **78%** | Ramas interactivas de callbacks `st.form_submit_button` y `st.rerun()` |
| **TOTAL GLOBAL** | **2,291** | **315** | **86%** | **Supera en +16 puntos el estándar objetivo del 70%** |

### 13.3. Análisis de Rutas Críticas No Cubiertas por Pruebas Unitarias
1. **`src/database/db.py:426-463` (`register_student_user`) y `501-515` (`save_student_profile`):** Estas dos funciones están conectadas en `app.py` y se probaron funcionalmente en el navegador, pero no cuentan con un test unitario directo en `tests/test_database.py`.
2. **`src/agents/ingestion_agent.py:69-112`:** Corresponde a ramas de validación de rangos específicos para pesos sílabo negativos o suma de pesos distinta de 100 cuando se proveen los 6 pesos explícitamente.
3. **`src/services/academic_service.py:253-319` (`extraer_pesos_silabo_archivo`):** Funciones de extracción de pesos desde documentos `.pdf` y `.docx` cuando no se suministra un archivo binario real de sílabo en las pruebas unitarias.

---

## 14. HALLAZGOS DETALLADOS DE LA AUDITORÍA FINAL

Tras verificar todas las correcciones de las Fases 2, 3 y 4, **no existen hallazgos de severidad `CRITICAL` (0) ni `HIGH` (0)**. Se documentan a continuación las **5 observaciones de severidad `MEDIUM`** y **4 observaciones de severidad `LOW`** identificadas en la inspección profunda de Fase 5:

---

### `HALL-F5-01` — Discrepancia entre `11.0` y `10.5` en el cálculo de puntos faltantes de Fase 1 y Fase 2
- **ID:** `HALL-F5-01`
- **Área:** Normativa Académica / Preprocesamiento ML
- **Requisito afectado:** `ACA-02` — Redondeo normativo UNSA (`10.50 -> 11`) y detección de imposibilidad matemática ordinaria.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `MEDIUM`
- **Archivo:** `src/agents/preprocessing_agent.py` (y `02_Scripts/build_checkpoint_features.py`)
- **Función o componente:** `PreprocessingAgent._extract_features()`
- **Línea aproximada:** `src/agents/preprocessing_agent.py:117-119, 130-132` (vs. línea `141` y `src/services/academic_service.py:104, 125`)
- **Evidencia:**
  En `preprocessing_agent.py:117` y `130`:
  ```python
  f["PUNTOS_FALT_F1"] = max(0.0, 11.0 - f["PUNTOS_F1"])
  f["NOTA_MIN_PEND_F1"] = f["PUNTOS_FALT_F1"] / (peso_pend_f1 / 100.0)
  f["IMPOSIBLE_APROBAR_F1"] = 1 if f["NOTA_MIN_PEND_F1"] > 20.0 else 0
  ```
  Mientras que en `preprocessing_agent.py:141` (`YA_APROBADO_CP3`) y en `academic_service.py:104, 125` se utiliza el umbral normativo real `10.5`.
- **Impacto funcional o académico:** En el intervalo fronterizo donde un estudiante requiere entre `10.5` y `11.0` puntos ponderados acumulados (por ejemplo, en `CP2` con `30%` de peso pendiente y `PUNTOS_F2` entre `4.50` y `4.99`), `NOTA_MIN_PEND_F2` supera `20.0` respecto a `11.0` aunque respecto a `10.5` requiere entre `18.37` y `20.00` (aún aprobable en vía ordinaria).
- **Riesgo asociado:** Activación prematura del indicador `imposible_ordinario` y sobreestimación en `~0.5 / peso_pendiente` puntos de la nota mínima requerida mostrada al estudiante en `CP1` y `CP2`.
- **Recomendación técnica:** Mantener `11.0 - PUNTOS_F1/F2` únicamente dentro del vector interno de entrada al modelo `.joblib` (para preservar compatibilidad exacta con el entrenamiento), pero calcular las variables de negocio reportadas al usuario (`meta_nota_min` e `imposible_ordinario` en `AlertAgent`) tomando como meta `10.5 - PUNTOS_ACUM`.

---

### `HALL-F5-02` — Permisividad entre docentes distintos en `validate_matricula_ownership` y selectores de curso
- **ID:** `HALL-F5-02`
- **Área:** Ciberseguridad y Control de Acceso (RBAC)
- **Requisito afectado:** `SEG-03` — Restricción de acceso del rol `DOCENTE` a sus asignaturas asignadas.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `MEDIUM`
- **Archivo:** `src/security/access_control.py` y `src/services/academic_service.py`
- **Función o componente:** `validate_matricula_ownership()` y `validar_y_procesar_acta_masiva()`
- **Línea aproximada:** `src/security/access_control.py:66-67` y `src/services/academic_service.py:129`
- **Evidencia:**
  En `src/security/access_control.py:66-67`:
  ```python
  elif rol == "DOCENTE" and mat_dict["docente"] != username and username not in ["docente_demo", "DOCENTE_EPIS", "admin"]:
      pass  # Permitido en demo / supervisión
  ```
  Adicionalmente, `validar_y_procesar_acta_masiva()` no recibe `current_user` para validar en backend que quien ejecuta la carga masiva posea rol `DOCENTE` o `ADMIN`.
- **Impacto funcional o académico:** En el entorno de demostración de tesis permite que `docente_demo` supervise cualquiera de las 9 asignaturas del catálogo sin bloqueos, pero en un entorno multi-docente real un docente autenticado podría consultar matrículas de asignaturas dictadas por otro docente.
- **Riesgo asociado:** Exposición horizontal de datos académicos entre docentes de distintas asignaturas dentro de la misma escuela profesional.
- **Recomendación técnica:** Añadir una tabla puente `docente_asignaturas (username, curso, semestre)` y reemplazar `pass` en `access_control.py:67` por `raise AuthorizationError(...)` cuando el docente no sea titular ni tutor asignado del curso, además de exigir `current_user` en `validar_y_procesar_acta_masiva()`.

---

### `HALL-F5-03` — Uso de priors constantes para 4 variables históricas contextuales en inferencia de runtime
- **ID:** `HALL-F5-03`
- **Área:** Machine Learning / Integración de Datos
- **Requisito afectado:** `ML-05` — Alimentación de características históricas del Checkpoint 0.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `MEDIUM`
- **Archivo:** `src/database/db.py` y `src/services/academic_service.py`
- **Función o componente:** `evaluate_and_persist_enrollment()` y `validar_y_procesar_acta_masiva()`
- **Línea aproximada:** `src/database/db.py:1489, 1494-1496` y `src/services/academic_service.py:168, 173-175`
- **Evidencia:**
  ```python
  "TASA_APROB_ACUM": 0.85,
  "DIFICULTAD_CURSO_HIST": 0.12,
  "DIFICULTAD_DOCENTE_HIST": 0.08,
  "DIFICULTAD_CURSO_DOCENTE_HIST": 0.10,
  ```
- **Impacto funcional o académico:** Mientras que `IRA_ACUM`, `REPROBACIONES_PREVIAS`, `CARGA_ACADEMICA`, `ES_REPETICION` y `SEMESTRES_DESDE_INGRESO` varían dinámicamente por alumno, las tasas históricas de dificultad de curso y docente se fijan en valores promedio institucionales (`0.12`, `0.08`, `0.10`), reduciendo la variabilidad explicativa de esas 4 características en tiempo de ejecución.
- **Riesgo asociado:** Subutilización de la capacidad discriminativa de `DIFICULTAD_CURSO_HIST` y `DIFICULTAD_DOCENTE_HIST` en `CP0` frente a asignaturas con tasas históricas de reprobación atípicas.
- **Recomendación técnica:** Almacenar las tasas históricas reales de reprobación en `catalogo_cursos` y `catalogo_docentes` y consultarlas dinámicamente al construir el payload en `evaluate_and_persist_enrollment()` y `validar_y_procesar_acta_masiva()`.

---

### `HALL-F5-04` — LIME validado únicamente en experimentación offline y `fidelidad_r = 0.96` constante en BD
- **ID:** `HALL-F5-04`
- **Área:** Inteligencia Artificial Explicable (XAI)
- **Requisito afectado:** `XAI-03` — Trazabilidad de fidelidad explicativa SHAP y LIME.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `MEDIUM`
- **Archivo:** `src/agents/xai_agent.py`, `src/database/db.py` y `04_Modelo/fidelidad_shap_lime_cp1.json`
- **Función o componente:** `XaiAgent`, `persist_acta_row_transactional()`, `evaluate_and_persist_enrollment()`
- **Línea aproximada:** `src/database/db.py:350, 902, 907, 922, 1544`
- **Evidencia:**
  En `04_Modelo/fidelidad_shap_lime_cp1.json`, la correlación empírica SHAP vs. LIME es `correlacion_pearson: 0.7778` (`77.78%` de coincidencia direccional). Sin embargo, en `src/database/db.py:902, 1544` se almacena el literal fijo `fidelidad = 0.96` en la tabla `explicaciones`, y LIME no se ejecuta en tiempo real en `xai_agent.py`.
- **Impacto funcional o académico:** La explicabilidad en tiempo real opera íntegramente con `shap.TreeExplainer` (exacta para Random Forest), pero el valor `fidelidad_r = 0.96` persistido en la tabla `explicaciones` es una constante estática y no el valor empírico del estudio SHAP-LIME (`0.7778`).
- **Riesgo asociado:** Posible cuestionamiento metodológico del jurado de tesis si se confunde el campo `fidelidad_r` de la base de datos (`0.96`) con la correlación Pearson SHAP-LIME reportada en `04_Modelo/fidelidad_shap_lime_cp1.json` (`0.7778`).
- **Recomendación técnica:** Parametrizar `fidelidad_r` leyendo el valor real desde `04_Modelo/fidelidad_shap_lime_cp1.json` (`0.7778`) o documentar explícitamente en el informe de tesis que LIME se empleó como contraste experimental offline de validación de consistencia y `shap.TreeExplainer` como motor productivo en tiempo real.

---

### `HALL-F5-05` — Inserción repetida de fila demo en `perfil_semestre` y `explicaciones` durante `seed_initial_data()`
- **ID:** `HALL-F5-05`
- **Área:** Persistencia y Base de Datos (SQLite)
- **Requisito afectado:** `DB-02` — Idempotencia en inicialización y sembrado de base de datos.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `MEDIUM`
- **Archivo:** `src/database/db.py`
- **Función o componente:** `seed_initial_data()` e invocación a nivel de módulo
- **Línea aproximada:** `src/database/db.py:313-316, 349-351, 1635-1636`
- **Evidencia:**
  La inspección en modo solo lectura de `src/database/sata_unsa.db` reveló `56` filas en `perfil_semestre` y `56` filas en `explicaciones` (frente a `1` fila en `matriculas` y `1` en `predicciones`), debido a que `INSERT OR IGNORE INTO perfil_semestre` y `explicaciones` no especifican `id = 1` ni cuentan con restricción `UNIQUE`. Además, `db.py:1635-1636` ejecuta `init_database()` y `seed_initial_data()` en el momento de importar `src.database.db` (incluso antes de que `tests/conftest.py` redirija `DB_PATH`).
- **Impacto funcional o académico:** Las consultas de lectura usan `ORDER BY id DESC LIMIT 1`, por lo que la interfaz muestra siempre el dato correcto sin errores funcionales, pero cada reinicio o importación añade un registro redundante en esas dos tablas.
- **Riesgo asociado:** Crecimiento innecesario de las tablas `perfil_semestre` y `explicaciones` y acoplamiento de efectos secundarios de escritura en tiempo de importación (`import src.database.db`).
- **Recomendación técnica:** Incluir el campo `id` explícito (`VALUES (1, ...)`) en los `INSERT OR IGNORE` de `perfil_semestre` (`db.py:313`) y `explicaciones` (`db.py:349`), o verificar `SELECT COUNT(*)` antes de insertar (tal como ya se hace para `mensajes_bus` y `tutorias` en `db.py:355-396`).

---

### `HALL-F5-06` — Ejecución síncrona monohilo del ciclo de mensajes en `CoordinatorAgent`
- **ID:** `HALL-F5-06`
- **Área:** Arquitectura Multiagente
- **Requisito afectado:** `ARQ-03` — Paso de mensajes en el Sistema Multiagente.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `LOW`
- **Archivo:** `src/agents/coordinator_agent.py`
- **Función o componente:** `CoordinatorAgent.analyze_student_risk()`
- **Línea aproximada:** `src/agents/coordinator_agent.py:66-205`
- **Evidencia:**
  `CoordinatorAgent` publica cada mensaje en la cola `queue.Queue` del agente receptor mediante `self.send(...)` e inmediatamente invoca `msg = self.ingestion_agent.receive(); self.ingestion_agent.handle_message(msg)` en el mismo hilo de ejecución.
- **Impacto funcional o académico:** Ningún impacto negativo en el flujo funcional ni en el protocolo FIPA-ACL; por el contrario, evita condiciones de carrera en Streamlit y mantiene una latencia total media inferior a `150 ms` por estudiante.
- **Riesgo asociado:** En cargas masivas superiores a miles de estudiantes simultáneos, el procesamiento es secuencial fila por fila.
- **Recomendación técnica:** Documentar en el capítulo de arquitectura de la tesis que el SMA implementa un modelo de **colas de mensajes FIPA-ACL desacopladas con planificador determinista cooperativo (turn-driven)** para garantizar reproducibilidad en entornos web reactivos (Streamlit).

---

### `HALL-F5-07` — `enroll_course()` no dispara evaluación inicial `CP0` hasta el primer registro de nota
- **ID:** `HALL-F5-07`
- **Área:** Funcionalidad / Flujo de Matrícula
- **Requisito afectado:** `FUN-01` — Visualización inmediata de asignaturas recién inscritas.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `LOW`
- **Archivo:** `app.py` y `src/database/db.py`
- **Función o componente:** Formulario `form_inscripcion_curso` / `enroll_course()`
- **Línea aproximada:** `app.py:2197-2211` y `src/database/db.py:534-579`
- **Evidencia:**
  Al pulsar `Inscribir Asignatura` en `app.py:2202`, se llama a `enroll_course(...)`, que inserta la fila en `matriculas`, pero no invoca a `evaluate_and_persist_enrollment(mat_id, coordinator, current_user=usuario)`.
- **Impacto funcional o académico:** Una asignatura recién inscrita aparece inmediatamente en el selector de cursos de `Configuración e Inscripción`, pero no tiene fila en `predicciones` (`CP0`) hasta que se guarda una calificación parcial o se importa un acta.
- **Riesgo asociado:** Confusión menor del usuario si inscribe un curso nuevo y espera ver de inmediato su predicción basal `CP0` antes de registrar notas.
- **Recomendación técnica:** Invocar `evaluate_and_persist_enrollment(mat_id, get_sma_system(), current_user=usuario)` inmediatamente después de `mat_id = enroll_course(...)` en `app.py:2203`.

---

### `HALL-F5-08` — Desfase documental de credenciales de demostración en `README.md`
- **ID:** `HALL-F5-08`
- **Área:** Documentación Técnica
- **Requisito afectado:** Consistencia documental del repositorio.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `LOW`
- **Archivo:** `README.md`
- **Función o componente:** Sección `3.5 Credenciales de Demostración Pre-sembradas`
- **Línea aproximada:** `README.md:104-111`
- **Evidencia:**
  `README.md` lista los usuarios antiguos `docente_epis / demo123`, `director_epis / demo123` y `admin_epis / demo123`, mientras que `src/database/db.py:290-297` y los botones de acceso rápido del Login (`app.py:1138-1163`) utilizan las credenciales seguras `20220638 / Alumno123*`, `docente_demo / Docente123*`, `tutor_epis / Tutor123*` y `admin / Admin123*`.
- **Impacto funcional o académico:** No afecta a la aplicación (cuyos botones de acceso rápido en la pantalla de Login funcionan directamente), pero puede confundir a un evaluador que intente copiar y pegar las contraseñas desde `README.md`.
- **Riesgo asociado:** Error de inicio de sesión manual si un revisor externo usa las credenciales antiguas del `README.md`.
- **Recomendación técnica:** Actualizar la tabla de la sección 3.5 de `README.md` con los cuatro usuarios reales sembrados en `seed_initial_data()`.

---

### `HALL-F5-09` — Archivos auxiliares SQLite WAL (`.db-shm`, `.db-wal`) y alertas menores de estilo (`ruff`)
- **ID:** `HALL-F5-09`
- **Área:** Higiene de Repositorio y Calidad de Código
- **Requisito afectado:** Limpieza de árbol Git y análisis estático de estilo.
- **Estado:** `PARTIALLY VERIFIED`
- **Severidad:** `LOW`
- **Archivo:** `.gitignore`, `app.py` y `tests/test_high_priority_fixes.py`
- **Función o componente:** Reglas de exclusión Git y formato PEP8/Ruff
- **Línea aproximada:** `.gitignore:33`, `app.py:10, 1165`
- **Evidencia:**
  - `.gitignore` incluye `*.db` en la línea 33, pero no incluye `*.db-shm` ni `*.db-wal`, por lo que `git status` muestra `src/database/sata_unsa.db-shm` y `src/database/sata_unsa.db-wal` como archivos no rastreados cuando el servidor está activo.
  - `python -m ruff check src app.py tests` reporta 31 avisos menores de estilo (`SIM117` bloques `with` anidados de Streamlit, `I001` orden de imports y 1 import no usado en `tests/test_high_priority_fixes.py:24`), sin ningún error sintáctico ni de ejecución.
- **Impacto funcional o académico:** Nulo en tiempo de ejecución.
- **Riesgo asociado:** Posible inclusión accidental de archivos temporales `-shm`/`-wal` si se ejecuta `git add .` antes de hacer commit.
- **Recomendación técnica:** Añadir `*.db-shm` y `*.db-wal` en `.gitignore` y ejecutar `ruff check --fix` antes del commit final de cierre de rama.

---

## 15. COMPARACIÓN EVOLUTIVA ENTRE FASES (FASES 1 A 5)

La siguiente matriz sintetiza la evolución verificada del sistema desde la auditoría inicial hasta la presente auditoría final de aceptación:

| Defecto / Requisito Identificado en Fase 1 | Estado en Fase 1 (Auditoría Inicial) | Fase en que se Abordó | Verificación en Fase 5 (Estado Actual) | ¿Existe Regresión? |
| :--- | :---: | :---: | :---: | :---: |
| **CRIT-01:** `AuthorizationError` al autenticar rol `ADMIN` en `app.py` | `FAILED` (Crash en pantalla principal) | **Fase 2** | `VERIFIED` — `ADMIN` aterriza en `Arquitectura y Bus FIPA-ACL`, aislado de registros individuales (`test_critical_fixes.py:39-84`). | **No** |
| **CRIT-02:** Restricción de `AUTORIDAD` a métricas estrictamente agregadas | `FAILED` (Veía tabla nominal de alumnos) | **Fase 2** | `VERIFIED` — `AUTORIDAD` visualiza mapa de calor por sección (`get_course_sections_summary`) y lanza `AuthorizationError` ante consultas nominales (`test_critical_fixes.py:86-144`). | **No** |
| **CRIT-03:** Inversión visual SHAP (`impact` vs `value`) en `app.py` | `FAILED` (Notas altas se pintaban como riesgo) | **Fase 2** | `VERIFIED` — `format_shap_factor_for_ui` en `xai_agent.py:117-201` usa estrictamente `impact` para signo, color y longitud de barra (`test_critical_fixes.py:146-210`). | **No** |
| **CRIT-04:** Persistencia y anonimización `HMAC-SHA256` en Carga Masiva de Actas | `FAILED` (Solo memoria y CUI en claro) | **Fase 2** | `VERIFIED` — `persist_acta_row_transactional` en `db.py:711-973` anonimiza con `ensure_cui_hash` y persiste con `BEGIN IMMEDIATE / ROLLBACK` (`test_critical_fixes.py:216-322`). | **No** |
| **CRIT-05:** `KeyError: 'latencia_inf_p95_ms'` cuando `metricas_tecnicas` está vacía | `FAILED` (Excepción potencial) | **Fase 2** | `VERIFIED` — `get_technical_metrics_summary()` en `db.py:1564-1606` retorna las 7 claves homogéneas en ambos estados (`test_critical_fixes.py:67-84`). | **No** |
| **ALTA-01:** Selectores reales de asignatura y estudiante para `DOCENTE` (sin `mat_id=1` fijo) | `FAILED` (Hardcodeado a `mat_id=1`) | **Fase 3** | `VERIFIED` — Selectores dinámicos en Seguimiento, Explicabilidad XAI y Tutoría sincronizados con `session_state` (`test_high_priority_fixes.py:43-114`). | **No** |
| **ALTA-02:** Integración real del bus FIPA-ACL y sus 4 performativas en `mensajes_bus` | `PARTIALLY VERIFIED` (Faltaban `PROPOSE` y `FAILURE` en BD) | **Fase 3** | `VERIFIED` — `CoordinatorAgent` y `MessageBus` persisten `REQUEST`, `INFORM`, `PROPOSE` y `FAILURE` reales sin PII (`test_high_priority_fixes.py:116-175`). | **No** |
| **ALTA-03:** Persistencia SQLite del flujo de tutoría, checklist y exportación PDF real | `FAILED` (`st.toast` simulado sin BD) | **Fase 3** | `VERIFIED` — Tabla `tutorias`, `schedule_tutoring_session`, `register_tutoring_session`, `get_tutoring_history` y `generate_intervention_pdf` (`test_high_priority_fixes.py:224-273`). | **No** |
| **ALTA-04:** Eliminación de métricas estáticas (`142`, `5`, `15/10/2026`, `0.0003s`) | `FAILED` (Hardcodeadas en HTML) | **Fase 3** | `VERIFIED` — Sub-header conectado a `get_header_metrics()` y telemetría conectada a `get_technical_metrics_summary()` (`test_high_priority_fixes.py:275-301`). | **No** |
| **ALTA-05:** Cuestionario TAM completo (PU + PEOU) y conexión de `save_grade`, `calcular_simulacion_sustitutorio` y `update_student_consent` | `PARTIALLY VERIFIED` (TAM con 2 sliders; funciones desconectadas de UI) | **Fase 3** | `VERIFIED` — TAM con 6 ítems Likert (3 PU + 3 PEOU) y las 3 funciones de negocio integradas en `Configuración e Inscripción` (`test_high_priority_fixes.py:303-351`). | **No** |
| **VIS-01..08:** Contraste de badges, alturas de KPIs, truncamiento de botones, CSS responsive `768×1024` y `390×844` | `PARTIALLY VERIFIED` (8 defectos UX/UI en Fase 1) | **Fase 4** | `VERIFIED` — Corregidos en `app.py:89-990` y verificados con `0 px` de desbordamiento horizontal en las 4 resoluciones (`INFORME_CORRECCION_VISUAL.md`). | **No** |

---

## 16. RIESGOS PENDIENTES Y LIMITACIONES IDENTIFICADAS

De cara a la sustentación de la tesis y a una eventual puesta en producción piloto en la EPIS-UNSA, se documentan de manera transparente los siguientes riesgos residuales:

1. **Riesgo Académico-Normativo (Bajo-Medio):** La diferencia de `0.5` puntos entre `11.0` y `10.5` en `PreprocessingAgent` (`HALL-F5-01`) puede adelantar la bandera de imposibilidad matemática ordinaria para alumnos cuyos puntos acumulados se ubiquen exactamente en la banda fronteriza de redondeo (`[10.50, 10.99]`).
2. **Riesgo de Privacidad Horizontal entre Docentes (Medio en Producción, Bajo en Piloto):** Mientras se mantenga la cláusula `pass` en `access_control.py:67` (`HALL-F5-02`), cualquier cuenta con rol `DOCENTE` puede visualizar las asignaturas del catálogo general. Para el piloto con cuentas controladas por la coordinación académica esto es aceptable, pero requiere filtrado por carga lectiva antes de abrir el registro a toda la plana docente.
3. **Riesgo Operativo de Concurrencia en SQLite (Bajo):** SQLite en modo `WAL` soporta adecuadamente lecturas concurrentes y escrituras moderadas para una escuela profesional (`~500–1,200` estudiantes activos), pero no está diseñado para cargas transaccionales masivas concurrentes a escala de toda la universidad sin migrar el motor de persistencia a PostgreSQL.
4. **Limitación Experimental de LIME en Tiempo Real (Bajo):** El contraste entre SHAP y LIME (`r = 0.7778`) se realizó en fase experimental offline (`CP1`), mientras que en producción se ejecuta exclusivamente `shap.TreeExplainer`. Esto debe exponerse con claridad en la defensa de tesis como una decisión deliberada de ingeniería por exactitud matemática en ensambles de árboles (`TreeSHAP`) y eficiencia computacional.

---

## 17. DICTAMEN FINAL DE ACEPTACIÓN

Con base en la evidencia empírica recolectada en modo de solo lectura sobre el código fuente, la base de datos SQLite, los modelos predictivos serializados, las pruebas automatizadas y la verificación multi-rol y multi-resolución en navegador real, el equipo auditor emite el siguiente dictamen formal:

> ### **DICTAMEN FINAL: `GO CON OBSERVACIONES`**

### Justificación Basada en Evidencias
1. **Cero Defectos Críticos o de Prioridad Alta Pendientes:** Los 5 defectos críticos y los 6 bloques de defectos de prioridad alta detectados en la auditoría inicial fueron resueltos íntegramente y verificados sin regresiones (`0 CRITICAL`, `0 HIGH`).
2. **Cumplimiento Riguroso de los 5 Objetivos de la Tesis:**
   - **Arquitectura Multiagente:** 7 agentes operativos comunicados mediante `MessageBus` y `AgentMessage` con trazabilidad real de las 4 performativas FIPA-ACL (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`) en SQLite.
   - **Modelos Predictivos en Cascada (CP0–CP3):** 4 modelos Random Forest calibrados temporalmente con `Recall` entre `84.62%` y `88.46%` y reducción progresiva de falsos positivos de hasta `-95.23%` en `CP3` (`ROC-AUC = 0.9950`).
   - **Explicabilidad (XAI):** Cálculo en tiempo real con `shap.TreeExplainer`, representación visual fiel al impacto SHAP (`format_shap_factor_for_ui`) y traducción automática en recomendaciones pedagógicas y planes de tutoría exportables en PDF.
   - **Seguridad y Privacidad por Diseño:** Anonimización irreversible `HMAC-SHA256` (`16` caracteres hex), contraseñas con `PBKDF2-HMAC-SHA256` (`100,000` iteraciones), consentimiento informado Opt-In (`comparte_con_tutor`) y aislamiento de roles para `ESTUDIANTE`, `AUTORIDAD` y `ADMIN`.
   - **Calidad de Software y Experiencia de Usuario:** **117 pruebas automatizadas aprobadas (`100% pass rate`)**, **86% de cobertura de código**, **0 vulnerabilidades altas o medias en Bandit**, y diseño institucional responsive verificado desde `1440×900` hasta `390×844`.
3. **Carácter No Bloqueante de las Observaciones (`5 MEDIUM`, `4 LOW`):** Ninguna de las 9 observaciones documentadas en la Sección 14 compromete la estabilidad del sistema, la validez científica de los resultados experimentales ni la demostración funcional completa ante el jurado de tesis.

---

## 18. PLAN DE REMEDIACIÓN PROPUESTO (SIN EJECUTAR EN ESTA FASE)

Para subsanar de forma ordenada las 9 observaciones no bloqueantes antes de un despliegue productivo institucional en la EPIS-UNSA, se propone el siguiente plan de remediación priorizado:

### Prioridad 1 — Corto Plazo (Pre-Despliegue Piloto en EPIS-UNSA)
1. **Alinear el cálculo de `meta_nota_min` e `imposible_ordinario` con `10.50` (`HALL-F5-01`):**
   - *Acción:* En `src/agents/alert_agent.py` (o en variables separadas de negocio dentro de `PreprocessingAgent`), calcular la nota mínima requerida mostrada al estudiante usando `(10.5 - PUNTOS_ACUM) / (PESO_PEND / 100.0)`, conservando `11.0 - PUNTOS_F1/F2` únicamente para el vector interno consumido por los modelos `.joblib`.
2. **Restringir el alcance horizontal del rol `DOCENTE` (`HALL-F5-02`):**
   - *Acción:* En `src/security/access_control.py:67`, reemplazar `pass` por `raise AuthorizationError("Acceso denegado: El docente solo puede gestionar matrículas de sus asignaturas asignadas.")` para usuarios no supervisores, y pasar `current_user` a `validar_y_procesar_acta_masiva()`.
3. **Corregir la idempotencia de `seed_initial_data()` (`HALL-F5-05`):**
   - *Acción:* En `src/database/db.py:313` y `349`, incluir explícitamente `id = 1` en los `INSERT OR IGNORE` de `perfil_semestre` y `explicaciones`, y limpiar las filas duplicadas históricas de `sata_unsa.db` mediante `DELETE FROM perfil_semestre WHERE id > 1; DELETE FROM explicaciones WHERE id > 1;`.

### Prioridad 2 — Mediano Plazo (Refinamiento Metodológico y Funcional)
4. **Sincronizar `fidelidad_r` con el estudio experimental SHAP-LIME (`HALL-F5-04`):**
   - *Acción:* Leer el valor `correlacion_pearson` (`0.7778`) desde `04_Modelo/fidelidad_shap_lime_cp1.json` al persistir registros en `explicaciones` (`src/database/db.py:902, 1544`), eliminando la constante `0.96`.
5. **Alimentar dinámicamente las tasas históricas de dificultad por curso y docente (`HALL-F5-03`):**
   - *Acción:* Agregar las columnas `dificultad_hist` en `catalogo_cursos` y `catalogo_docentes` en `src/database/db.py` y usarlas en `evaluate_and_persist_enrollment()` y `validar_y_procesar_acta_masiva()`.
6. **Disparar predicción `CP0` automática al inscribir asignatura (`HALL-F5-07`):**
   - *Acción:* Invocar `evaluate_and_persist_enrollment(mat_id, get_sma_system(), current_user=usuario)` inmediatamente después de `enroll_course(...)` en `app.py:2203`.

### Prioridad 3 — Mantenimiento y Documentación
7. **Actualizar tabla de credenciales en `README.md` (`HALL-F5-08`):**
   - *Acción:* Actualizar `README.md:104-111` con los usuarios vigentes (`20220638 / Alumno123*`, `docente_demo / Docente123*`, `tutor_epis / Tutor123*`, `admin / Admin123*`).
8. **Actualizar `.gitignore` y aplicar formato `ruff` (`HALL-F5-09`):**
   - *Acción:* Añadir `*.db-shm` y `*.db-wal` a `.gitignore` y ejecutar `python -m ruff check --fix src app.py tests`.
