# INFORME DE CORRECCIÓN DE DEFECTOS CRÍTICOS — SATA-UNSA (FASE 2)

**Proyecto:** Sistema de Alerta Temprana Académica (SATA-UNSA) — EPIS / FIPS, Universidad Nacional de San Agustín de Arequipa  
**Rama de trabajo:** `fix-ui-acceso`  
**Documento de referencia base:** `auditoria_visual_funcional/INFORME_AUDITORIA_EXHAUSTIVA.md`  
**Fecha de ejecución:** 13–14 de noviembre de 2026  
**Estado de regresión:** **102 pruebas aprobadas (`102 passed, 0 failed`)** · Cobertura global incrementada del **62 % al 65 %**

---

## 1. MATRIZ DE ESTADO ACTUALIZADA DE LOS 5 DEFECTOS CRÍTICOS

| ID | Defecto Crítico Identificado en Fase 1 | Archivos Modificados | Estado Antes (Fase 1) | Estado Después (Fase 2) | Verificación en Pruebas y Navegador | Evidencia Visual Post-Corrección |
| :-: | :--- | :--- | :---: | :---: | :--- | :--- |
| **CRÍTICO 1** | **Error de autorización del Administrador (`AuthorizationError`)** al entrar al `Panel de seguimiento` | `app.py`<br>`src/security/access_control.py`<br>`src/database/db.py` | **NO CUMPLE** (Crash en pantalla) | **CORREGIDO Y VERIFICADO** | `TestProblemaCritico1AdminAuthorization` (3 pruebas) + verificación en vivo en `http://localhost:8501` | `evidencias/05_post_correccion_criticos/01_admin_panel_rbac_sin_error.png` |
| **CRÍTICO 2** | **Error `KeyError: 'latencia_inf_media_ms'` en `Monitor Técnico OBJ5`** y ausencia de telemetría real | `src/database/db.py`<br>`src/agents/coordinator_agent.py`<br>`app.py` | **NO CUMPLE** (Crash en pantalla) | **CORREGIDO Y VERIFICADO** | `TestProblemaCritico2MonitorTecnicoOBJ5` (2 pruebas) + verificación con tabla vacía y con muestras reales | `evidencias/05_post_correccion_criticos/02_admin_monitor_obj5_vacio_sin_keyerror.png` |
| **CRÍTICO 3** | **Explicabilidad SHAP distorsionada** (`f["value"]` usado en lugar de `f["impact"]`, invirtiendo factores protectores) | `src/agents/xai_agent.py`<br>`app.py` | **NO CUMPLE** (Factor protector `-0.05` pintado como `+6.00` granate) | **CORREGIDO Y VERIFICADO** | `TestProblemaCritico3ExplicabilidadSHAP` (2 pruebas) + verificación visual en `Detalle con explicabilidad` | `evidencias/05_post_correccion_criticos/03_estudiante_xai_shap_impacto_real.png` |
| **CRÍTICO 4** | **Carga Masiva de Actas volátil** (procesamiento solo en memoria sin persistencia transaccional en SQLite) | `src/database/db.py`<br>`src/services/academic_service.py`<br>`src/security/crypto.py`<br>`src/agents/coordinator_agent.py`<br>`app.py` | **NO CUMPLE** (0 registros en SQLite tras carga) | **CORREGIDO Y VERIFICADO** | `TestProblemaCritico4PersistenciaCargaMasiva` (2 pruebas: persistencia, idempotencia y rollback) + carga en navegador | `evidencias/05_post_correccion_criticos/04_docente_carga_masiva_persistida.png`<br>`05_docente_panel_actualizado_post_acta.png` |
| **CRÍTICO 5** | **Violación de privacidad en rol `AUTORIDAD`** (exposición de filas e identificadores individuales en `Panel de seguimiento`) | `app.py`<br>`src/database/db.py`<br>`src/security/access_control.py` | **NO CUMPLE** (Exponía `CUI E7BB88B1B2BDD47F`) | **CORREGIDO Y VERIFICADO** | `TestProblemaCritico5PrivacidadAutoridad` (2 pruebas) + verificación en navegador con rol `tutor_epis` | `evidencias/05_post_correccion_criticos/06_autoridad_metricas_institucionales.png`<br>`07_autoridad_panel_agregado_sin_cui.png` |

---

## 2. DETALLE TÉCNICO DE LOS PROBLEMAS CORREGIDOS

### 2.1. Problema Crítico 1 — Error de Autorización del Administrador (`ADMIN`)

* **Archivos modificados:**
  * `app.py`
  * `src/security/access_control.py`
  * `src/database/db.py`
* **Causa raíz:**
  Al iniciar sesión con el rol `ADMIN`, la primera vista del menú lateral (`Panel de seguimiento`) ejecutaba el bloque condicional `else:` (`app.py:1186-1187`), compartido por todos los roles distintos de `ESTUDIANTE`. Dicho bloque invocaba `get_course_students_table(curso_sel, "2026-B", current_user=usuario)`, función que en `src/database/db.py:680-681` lanza explícitamente `AuthorizationError("Principio de Privacidad: El Administrador no tiene acceso a notas individuales de estudiantes.")`.
* **Solución aplicada:**
  1. Se separó explícitamente la lógica de renderizado por rol en `Panel de seguimiento` dentro de `app.py` (`if rol == "ESTUDIANTE":`, `elif rol == "DOCENTE":`, `elif rol == "AUTORIDAD":`, `else: # ADMIN`).
  2. Para el rol `ADMIN`, nunca se invoca `get_course_students_table()`. En su lugar, se muestra una pantalla informativa y operativa controlada (`Panel Operativo de Administración (RBAC)`) que exhibe únicamente indicadores agregados de la asignatura (`Matrículas Evaluadas en Asignatura`, `Tasa de Riesgo Alto en Asignatura`) y el estado del monitor técnico (`Muestras Técnicas Registradas (OBJ5)`), ocultando los botones de acción individual (`Programar tutoría`, `Ver explicación`).
  3. En `src/security/access_control.py`, se reforzaron `validate_student_access()` y `validate_matricula_ownership()` para bloquear cualquier intento de acceso de `ADMIN` a perfiles, matrículas, notas o predicciones individuales, y se incorporó la matriz formal `ROLE_AUTHORIZED_VIEWS` junto con la función `can_access_view(role, view_name)`.
* **Resultados Antes vs. Después:**
  * **Antes:** Pantalla rota con traceback rojo `AuthorizationError` al iniciar sesión como `admin`.
  * **Después:** Inicio de sesión limpio, visualización de resumen operativo agregado y cumplimiento estricto de RBAC en capa de UI, servicios y base de datos.

---

### 2.2. Problema Crítico 2 — Error en Monitor Técnico OBJ5 y Telemetría Real

* **Archivos modificados:**
  * `src/database/db.py`
  * `src/agents/coordinator_agent.py`
  * `app.py`
* **Causa raíz:**
  En `src/database/db.py:779-786`, cuando la tabla `metricas_tecnicas` no tenía registros (`if not rows:`), la función `get_technical_metrics_summary()` devolvía un diccionario con las claves `"latencia_inf_media"`, `"latencia_xai_media"`, `"ram_media"` y `"overhead_media"` (omitiendo además `"latencia_inf_p95_ms"`), mientras que cuando existían filas devolvía `"latencia_inf_media_ms"`, `"latencia_inf_p95_ms"`, `"latencia_xai_media_ms"`, `"ram_media_mb"` y `"overhead_media_ms"`. Esto provocaba `KeyError: 'latencia_inf_media_ms'` en `app.py:1653`. Adicionalmente, `CoordinatorAgent.analyze_student_risk()` no instrumentaba ni persistía las mediciones reales mediante `log_technical_metrics()`.
* **Solución aplicada:**
  1. Se homologó el esquema de retorno de `get_technical_metrics_summary()` en `src/database/db.py` para garantizar siempre las 7 claves canónicas (`total_muestras`, `latencia_inf_media_ms`, `latencia_inf_p95_ms`, `latencia_xai_media_ms`, `latencia_total_media_ms`, `ram_media_mb`, `overhead_media_ms`), tanto con tabla vacía (`0.0`) como con muestras reales.
  2. En `src/agents/coordinator_agent.py`, se instrumentaron mediciones reales en milisegundos con `time.perf_counter()` para:
     * Latencia de inferencia pura del `PredictorAgent` (`latencia_inferencia_ms`).
     * Latencia de cálculo SHAP del `XaiAgent` (`latencia_xai_ms`).
     * Overhead real de despacho y recepción de colas en el `MessageBus` (`overhead_bus_ms`).
     * Latencia total end-to-end del pipeline de 6 agentes (`latencia_total_ms`).
     * Consumo real de memoria RSS del proceso mediante `psutil.Process(os.getpid()).memory_info().rss` (`ram_mb`).
  3. Se persisten las mediciones reales mediante `log_technical_metrics()` y se retorna el bloque `"telemetry"` en la respuesta del coordinador.
  4. En `app.py` (`Monitor Técnico OBJ5`), se diferenció explícitamente el estado sin muestras (`total_muestras == 0`, mostrando `"Sin muestras (0.0 ms)"` y un aviso de tabla vacía) respecto del estado con mediciones reales (`total_muestras > 0`, mostrando las medias, P95 real y cantidad de muestras).
* **Resultados Antes vs. Después:**
  * **Antes:** Crash inmediato `KeyError: 'latencia_inf_media_ms'` en escritorio y móvil; tabla `metricas_tecnicas` permanentemente vacía.
  * **Después:** La vista carga sin errores tanto con tabla vacía como con mediciones reales, persistiendo cada inferencia en SQLite.

---

### 2.3. Problema Crítico 3 — Explicabilidad SHAP en Vista 2 (`Detalle con explicabilidad`)

* **Archivos modificados:**
  * `src/agents/xai_agent.py`
  * `app.py`
* **Causa raíz:**
  En `app.py:1295-1296`, el renderizador de barras SHAP leía `val_raw = float(f.get("value", 0.0))` (el valor observado de la variable académica, p. ej., nota `9.0`, `8.0`, IRA `11.5`, créditos `6`) en lugar de `f.get("impact")` (la contribución SHAP real calculada por `TreeExplainer`: `+0.28`, `+0.24`, `+0.12`, `-0.05`). Además, la condición `es_riesgo = f.get("direction") == "Riesgo" or val_raw > 0` evaluaba `6 > 0` como `True`, pintando los factores protectores en color granate de riesgo con `+6.00` y barras saturadas al `100%`.
* **Solución aplicada:**
  1. Se implementó en `src/agents/xai_agent.py` la función normalizadora `format_shap_factor_for_ui(factor, max_abs_impact)` y se blindó `XaiAgent.explain()` frente a valores `NaN` o nulos.
  2. La función extrae estrictamente `factor["impact"]` como contribución SHAP, conserva su signo original (`+` / `-`), asigna `var(--granate)` a impactos positivos que incrementan el riesgo (`impact > 0`) y `var(--azul-factor)` a impactos negativos que reducen el riesgo (`impact < 0`), y calcula el ancho porcentual de cada barra de manera estrictamente proporcional a `abs(impact) / max_abs_impact`.
  3. El valor observado de la variable (`factor["value"]`) se formatea y presenta por separado junto a la etiqueta del factor (`(Valor observado: 9)`, `(Valor observado: 6)`).
* **Resultados Antes vs. Después:**

| Factor en Estudiante Demo | Antes (Fase 1 — Incorrecto) | Después (Fase 2 — Correcto) |
| :--- | :--- | :--- |
| Evaluación Continua 1 | `+9.00` · Granate · Barra `100%` | **`+0.28`** `(Valor observado: 9)` · Granate · Barra `100%` |
| Examen Parcial 1 | `+8.00` · Granate · Barra `100%` | **`+0.24`** `(Valor observado: 8)` · Granate · Barra `86%` |
| Índice de Rendimiento Acumulado (IRA) | `+11.50` · Granate · Barra `100%` | **`+0.12`** `(Valor observado: 11.5)` · Granate · Barra `43%` |
| Carga de cursos matriculados | `+6.00` · **Granate (Invertido)** · Barra `100%` | **`-0.05`** `(Valor observado: 6)` · **Azul Protector** · Barra `18%` |

---

### 2.4. Problema Crítico 4 — Persistencia Transaccional de Carga Masiva de Actas

* **Archivos modificados:**
  * `src/security/crypto.py`
  * `src/database/db.py`
  * `src/services/academic_service.py`
  * `src/agents/coordinator_agent.py`
  * `app.py`
* **Causa raíz:**
  `validar_y_procesar_acta_masiva()` en `src/services/academic_service.py` validaba el DataFrame y ejecutaba `coordinator_agent.analyze_student_risk(payload)` en memoria, pero nunca escribía en SQLite ni anonimizaba el `id_estudiante` devuelto en la tabla de resultados.
* **Solución aplicada:**
  1. Se añadió `ensure_cui_hash(raw_id)` en `src/security/crypto.py` para garantizar que cualquier CUI o identificador sea transformado inmediatamente en su hash HMAC-SHA256 de 16 caracteres hexadecimales antes de ingresar al bus multiagente, a la base de datos o a las tablas de la interfaz.
  2. Se implementó `persist_acta_row_transactional(...)` en `src/database/db.py`, que ejecuta una transacción atómica SQLite (`BEGIN IMMEDIATE` ... `COMMIT`, con `ROLLBACK` automático ante cualquier error) por cada fila válida:
     * Asegura la existencia de la asignatura y docente en `catalogo_cursos` y `catalogo_docentes`.
     * Registra al estudiante anonimizado en `estudiantes`.
     * Crea o actualiza el perfil basal en `perfil_semestre` (`ira_acum`, `repeticiones_previas`, `creditos_matriculados`).
     * Crea o actualiza la matrícula en `matriculas` verificando `(cui_hash, semestre, curso)` para evitar duplicados al reimportar.
     * Inserta o actualiza las calificaciones parciales (`EC1..EP3`) en `notas` y registra la trazabilidad en `historial_cambios` cuando una nota se modifica.
     * Inserta o actualiza la predicción en `predicciones` y la explicación SHAP en `explicaciones` para `(matricula_id, checkpoint)` sin duplicar registros al reimportar.
     * Registra los mensajes FIPA-ACL en `mensajes_bus` y la telemetría en `metricas_tecnicas` asociados al `request_id` anonimizado.
  3. En `app.py` (`Carga Masiva de Actas`), se añadieron 3 indicadores de resumen del lote (`Total Filas Analizadas`, `Registros Procesados y Persistidos`, `Filas Rechazadas / Con Errores`).
* **Resultados Antes vs. Después:**
  * **Antes:** Los datos desaparecían al cambiar de vista; `id_estudiante` se mostraba en texto claro; `Panel de seguimiento` no reflejaba los alumnos cargados.
  * **Después:** Persistencia transaccional completa en las 9 tablas involucradas, anonimización HMAC-SHA256 total, idempotencia al reimportar el mismo archivo y actualización inmediata en `Panel de seguimiento` y `Métricas Institucionales`.

---

### 2.5. Problema Crítico 5 — Privacidad del Rol Autoridad (`AUTORIDAD`)

* **Archivos modificados:**
  * `app.py`
  * `src/database/db.py`
  * `src/security/access_control.py`
* **Causa raíz:**
  En `app.py:1186-1209`, el rol `AUTORIDAD` compartía la rama de código del `DOCENTE`, invocando `get_course_students_table()` y renderizando filas individuales con el hash de cada estudiante (`CUI E7BB88B1B2BDD47F`) y botones de acción individual.
* **Solución aplicada:**
  1. En `src/database/db.py`, se bloqueó el rol `AUTORIDAD` dentro de `get_course_students_table()` lanzando `AuthorizationError`, así como en `validate_student_access()` y `validate_matricula_ownership()` en `src/security/access_control.py`.
  2. Se implementó la consulta agregada `get_course_sections_summary(curso, semestre)` en `src/database/db.py`, que agrupa por `seccion` y `docente` devolviendo únicamente conteos y tasas (`total_alumnos`, `rojos`, `amarillos`, `verdes`, `promedio_riesgo_pct`, `tasa_riesgo_pct`), sin ningún `cui_hash`, CUI, nombre ni calificación individual.
  3. En `app.py` (`Panel de seguimiento`), la rama `elif rol == "AUTORIDAD":` muestra el aviso institucional de privacidad por diseño y la tabla agregada por sección, sin botones individuales.
* **Resultados Antes vs. Después:**
  * **Antes:** `AUTORIDAD` veía filas individuales de estudiantes (`CUI E7BB88B1B2BDD47F`) y el botón `Ver explicación` que conducía a un callejón sin salida.
  * **Después:** `AUTORIDAD` visualiza exclusivamente métricas agregadas por asignatura y sección en todas sus vistas, con bloqueo garantizado también en la capa de datos.

---

## 3. PRUEBAS EJECUTADAS Y COBERTURA

### 3.1. Aislamiento de Base de Datos de Pruebas
Se incorporó en `tests/conftest.py` el fixture de sesión `isolated_test_database(tmp_path_factory)` (`autouse=True`), que redirige `src.database.db.DB_PATH` a una base de datos SQLite temporal durante la ejecución de `pytest`. Esto garantiza que ninguna prueba unitaria, de integración o de carga masiva contamine la base de datos institucional `src/database/sata_unsa.db`.

### 3.2. Resultados de la Suite Completa (`pytest`)
* **Total de pruebas ejecutadas:** **102 pruebas** (`91` preexistentes + `11` nuevas en `tests/test_critical_fixes.py`).
* **Resultado:** **`102 passed, 0 failed`** en `121.10s`.
* **Verificación de invariantes:**
  * Los 4 modelos `.joblib` (`CP0`, `CP1`, `CP2`, `CP3`) y sus umbrales calibrados (`0.285`, `0.340`, `0.495`, `0.765`) se mantuvieron intactos (`TestModelsPerformanceAndRecall`: Recall >= 80 % en los 4 checkpoints).
  * Cero fuga de datos intra-semestral (`TestNoDataLeakage`: 15, 25, 37 y 46 features).
  * Cumplimiento de normativa UNSA de examen sustitutorio (`TestNormativaUNSA`).
  * Cumplimiento de Hipótesis H3 de latencia `< 1.5 s` en 100 corridas (`TestPerformanceAndLatencyH3`).
  * Cero emojis en código fuente (`test_no_emojis_in_source_code_ui`).

### 3.3. Comparativa de Cobertura de Código (Antes vs. Después)

| Módulo | Cobertura Antes (Fase 1) | Cobertura Después (Fase 2) | Variación |
| :--- | :---: | :---: | :---: |
| `src/database/db.py` | 55 % | **71 %** | **+16 %** |
| `src/security/access_control.py` | 45 % | **61 %** | **+16 %** |
| `src/security/crypto.py` | 85 % | **86 %** | **+1 %** |
| `src/agents/coordinator_agent.py` | 97 % | **96 %** | -1 % (líneas de manejo defensivo de excepción) |
| `src/agents/alert_agent.py` | 100 % | **100 %** | = |
| `src/agents/predictor_agent.py` | 94 % | **94 %** | = |
| `src/agents/preprocessing_agent.py` | 96 % | **96 %** | = |
| `src/reports/pdf_generator.py` | 97 % | **97 %** | = |
| **TOTAL GLOBAL** | **62 %** (`91 passed`) | **65 %** (`102 passed`) | **+3 % (+11 tests)** |

---

## 4. PROBLEMAS NO CRÍTICOS QUE PERMANECEN PENDIENTES (PARA FASES POSTERIORES)

Siguiendo la restricción de Fase 2 de **corregir exclusivamente los 5 defectos críticos** sin realizar refactorizaciones generales ni rediseñar la interfaz, los hallazgos de severidad **Alta, Media y Baja** documentados en `INFORME_AUDITORIA_EXHAUSTIVA.md` permanecen registrados para una fase posterior de mejoras funcionales y visuales:

1. **Selectores para el rol `DOCENTE` en Vistas 2 y 4 (Severidad Alta):** En `Detalle con explicabilidad` y `Seguimiento y plan de tutoría`, el rol `DOCENTE` aún consulta por defecto `mat_id_act = 1` sin un selector interactivo de asignatura y estudiante.
2. **Persistencia de acciones de tutoría y bitácora interactiva (Severidad Alta):** Los botones `Programar tutoría` y `Registrar tutoría`, así como las 3 casillas de verificación de la bitácora en Vista 4, continúan siendo controles de demostración sin tabla dedicada en SQLite.
3. **Formulario de encuesta TAM (Severidad Alta):** En `Encuestas SUS / TAM` se visualizan las métricas de `SUS` y `TAM`, pero el formulario interactivo captura únicamente los 10 ítems de `SUS`.
4. **Ajustes de especificidad CSS en botones primarios y contraste del Sidebar (Severidad Media):** Los selectores CSS `.stButton button:not([data-testid="baseButton-primary"])` y `[data-testid="stSidebar"] span` en `app.py` pueden actualizarse en la fase de pulido visual para restaurar el fondo granate en botones primarios, el texto blanco en el radio del sidebar y ocultar la ligadura `keyboard_double_`.

---

## 5. RIESGOS RESIDUALES

1. **Concurrencia de escritura masiva en SQLite local:** Aunque el modo `WAL` (`PRAGMA journal_mode=WAL`) y `BEGIN IMMEDIATE` con `timeout=20.0` soportan adecuadamente el uso concurrente de lectura y cargas por lotes docentes en un servidor institucional departamental, ante cargas simultáneas de múltiples docentes subiendo archivos de miles de filas al mismo instante podría presentarse espera de bloqueo de archivo propia de SQLite.
2. **Recarga de módulos en caliente en Streamlit:** Cuando se actualizan firmas de funciones en paquetes bajo `src/`, el servidor Streamlit requiere reinicio del proceso si ya tenía dichos módulos cacheados en `sys.modules` (verificado y resuelto durante el despliegue de Fase 2).
