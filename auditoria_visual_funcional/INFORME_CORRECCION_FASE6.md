# INFORME DE CORRECCIÓN SELECTIVA DE HALLAZGOS DE AUDITORÍA — FASE 6 (SATA-UNSA)

**Proyecto:** Sistema de Alerta Temprana Académica (SATA-UNSA) — EPIS-UNSA<br>
**Rama de Trabajo:** `fix-ui-acceso`<br>
**Commit Base de Referencia:** `4430601` (`chore: cerrar auditoria final de aceptacion fase 5`)<br>
**Documento de Entrada:** `auditoria_visual_funcional/INFORME_AUDITORIA_FINAL_ACEPTACION.md`<br>
**Fecha de Ejecución:** 16 de noviembre de 2026

---

## 1. RESUMEN EJECUTIVO

En cumplimiento del plan de trabajo de la **Fase 6**, se procedió a verificar y corregir selectivamente los hallazgos prioritarios identificados en el Informe de Auditoría Final de Aceptación (`HALL-F5-01` a `HALL-F5-09`), respetando estrictamente las restricciones de integridad científica y arquitectónica del proyecto:
- **Cero modificaciones** sobre los modelos serializados `.joblib` (`CP0`–`CP3`), sus conjuntos y orden de características (`15`, `25`, `37` y `46` variables), sus umbrales calibrados (`0.285`, `0.340`, `0.495`, `0.765`), los datasets ni los scripts de entrenamiento.
- **Cero alteraciones** a la arquitectura de los 7 agentes ni al protocolo FIPA-ACL.
- **Cero escrituras o limpiezas** sobre la base de datos institucional `src/database/sata_unsa.db`.

### Tabla Resumen de Estado por Hallazgo

| Hallazgo | Prioridad | Descripción Corta | Resultado |
| :---: | :---: | :--- | :--- |
| **F5-01** | Prioridad 2 (`MEDIUM`) | Discrepancia `11.0` vs `10.50` en cálculo de puntos faltantes e imposibilidad matemática ordinaria | **Corregido** |
| **F5-02** | Prioridad 1 (`MEDIUM`) | Cláusula `pass` permisiva para rol `DOCENTE` ante cursos y matrículas de otros docentes | **Corregido** |
| **F5-03** | Prioridad 5 (`MEDIUM`) | Uso de priors institucionales fijos en 4 características contextuales de `CP0` | **Analizado / Pendiente de autorización** |
| **F5-04** | Prioridad 4 (`MEDIUM`) | Persistencia de constante ficticia `fidelidad_r = 0.96` en tabla `explicaciones` | **Corregido** |
| **F5-05** | Prioridad 3 (`MEDIUM`) | Inserciones duplicadas en `perfil_semestre` y `explicaciones` durante `seed_initial_data()` | **Corregido** |
| **F5-06** | `LOW` | Despacho síncrono monohilo sobre colas `queue.Queue` en `CoordinatorAgent` | **Revisado** *(Conservado por diseño determinista)* |
| **F5-07** | `LOW` | Evaluación automática de `CP0` al inscribir una nueva asignatura en `app.py` | **Revisado y Corregido** |
| **F5-08** | `LOW` | Credenciales demo antiguas en `README.md` | **Revisado y Corregido** |
| **F5-09** | `LOW` | Exclusión de archivos temporales SQLite (`*.db-shm`, `*.db-wal`) en `.gitignore` | **Revisado y Corregido** |

---

## 2. ESTADO DE GIT Y COMMIT DE REFERENCIA

- **Rama activa:** `fix-ui-acceso` (sincronizada con `origin/fix-ui-acceso`).
- **Commit base de referencia (`HEAD`):** `4430601 chore: cerrar auditoria final de aceptacion fase 5`.
- **Estado al inicio de Fase 6:** Árbol limpio con 0 modificaciones sobre `4430601`.
- **Estado actual previo a commit:** 10 archivos rastreados modificados (`.gitignore`, `README.md`, `app.py`, `src/agents/alert_agent.py`, `src/agents/preprocessing_agent.py`, `src/agents/xai_agent.py`, `src/database/db.py`, `src/security/access_control.py`, `src/services/academic_service.py`, `tests/conftest.py`) y 2 archivos nuevos no rastreados (`auditoria_visual_funcional/INFORME_CORRECCION_FASE6.md`, `tests/test_phase6_audit_fixes.py`). No se han preparado cambios en el staging (`git diff --cached --stat` vacío) ni se ha ejecutado commit/push.

---

## 3. ANÁLISIS, CAUSA RAÍZ Y CORRECCIÓN POR HALLAZGO

---

### 3.1. PRIORIDAD 1 — `F5-02`: Control de Acceso Docente (RBAC Horizontal)

- **Estado previo:** Confirmado en `src/security/access_control.py:66-67`, `src/database/db.py:1090-1133` y `src/services/academic_service.py:172`.
- **Evidencia del defecto:**
  En `validate_matricula_ownership()` (`src/security/access_control.py:66-67`) existía la rama:
  ```python
  elif rol == "DOCENTE" and mat_dict["docente"] != username and username not in ["docente_demo", "DOCENTE_EPIS", "admin"]:
      pass  # Permitido en demo / supervisión
  ```
  Asimismo, `get_course_students_table()` en `src/database/db.py` verificaba que el rol no fuera `ESTUDIANTE`, `ADMIN` ni `AUTORIDAD`, pero no comprobaba si el usuario con rol `DOCENTE` tenía asignaciones activas ni si la asignatura consultada pertenecía a otro docente.
- **Causa raíz:** En el sembrado inicial (`seed_initial_data()`), el usuario de demostración se denomina `username = "docente_demo"`, mientras que la columna `docente` en `matriculas` registra `"DOCENTE PRINCIPAL 1"`. Para evitar un fallo de coincidencia literal entre ambos strings durante la demo, se había introducido una cláusula `pass` que desactivaba el aislamiento horizontal entre docentes.
- **Archivos y funciones modificadas:**
  1. `src/security/access_control.py`:
     - Se definió `DOCENTE_ALIASES` y la función `get_authorized_teacher_names(current_user)` (líneas `15-38`), que vincula de forma explícita y controlada cada cuenta `DOCENTE` exclusivamente con su propio identificador normalizado (y su alias canónico de semilla en el caso de `docente_demo -> DOCENTE PRINCIPAL 1`), aplicando **denegación por defecto** si el rol no es `DOCENTE` o carece de identificador.
     - Se implementó `validate_course_teacher_access(current_user, curso, semestre, conn)` (líneas `41-88`), que verifica: (a) que el docente posea al menos una asignación activa en el sistema (denegando el acceso a docentes sin asignaciones), y (b) que la asignatura consultada no pertenezca a otro docente.
     - En `validate_matricula_ownership()` (líneas `138-156`), se eliminó el `pass` y se impuso la validación estricta `docente_mat in allowed_names`, lanzando `AuthorizationError` ante cualquier intento de consultar o modificar una matrícula ajena.
  2. `src/database/db.py`:
     - En `get_course_students_table()` (líneas `1140-1197`), se integró `validate_course_teacher_access()` y el filtrado estricto de filas por `allowed_teacher_names`.
     - Se añadió `get_courses_for_user(current_user, semestre)` (líneas `1200-1226`) para retornar a cada docente únicamente las asignaturas bajo su cargo.
  3. `src/services/academic_service.py` y `app.py`:
     - En `validar_y_procesar_acta_masiva()` (líneas `268-296, 339-347`), se incorporó el parámetro opcional `current_user` para impedir que un docente cargue actas a nombre de otro docente.
     - En `app.py` (líneas `38, 1302, 2221`), se conectó `get_courses_for_user()` y se pasó `current_user=usuario` al procesador de actas.

---

### 3.2. PRIORIDAD 2 — `F5-01`: Umbral Académico de Aprobación (`10.50` vs `11.0`)

- **Estado previo:** Confirmado en `src/agents/preprocessing_agent.py:117-132` frente a `src/agents/preprocessing_agent.py:141` (`YA_APROBADO_CP3`) y `src/services/academic_service.py:104, 125`.
- **Evidencia del defecto:**
  - En `PreprocessingAgent._compute_features()`, `PUNTOS_FALT_F1` y `PUNTOS_FALT_F2` se calculaban como `max(0.0, 11.0 - PUNTOS_F1/F2)`, lo que hacía que `NOTA_MIN_PEND_F1/F2` e `IMPOSIBLE_APROBAR_F1/F2` exigieran `11.00` puntos exactos en lugar de `10.50` (nota que por redondeo normativo UNSA equivale a `11`).
  - Adicionalmente, en `calcular_simulacion_sustitutorio()` (`src/services/academic_service.py:126-127`), la operación `math.ceil(peor_nota + (10.5 - prom_ordinario) / peor_peso)` sin redondeo previo de precisión flotante podía elevar un borde exacto como `12.000000000000002` a `13` (o `20.000000000000004` a `21`).
- **Causa raíz:** El script de entrenamiento `02_Scripts/build_checkpoint_features.py` definió las columnas de entrada del modelo `NOTA_MIN_PEND_F1/F2` e `IMPOSIBLE_APROBAR_F1/F2` sobre `11.0`, y `AlertAgent` reutilizaba directamente esas columnas del vector de ML para mostrar la meta académica y la alerta de imposibilidad ordinaria al usuario.
- **Archivos y funciones modificadas (preservando intacto el vector de características de los modelos `.joblib`):**
  1. `src/services/academic_service.py`:
     - Se definió la constante única `UMBRAL_APROBACION_NORMATIVO: float = 10.50` (línea `20`).
     - En `calcular_simulacion_sustitutorio()` (líneas `129-131`), se corrigió la precisión de punto flotante (`s_min_exacta = round(peor_nota + (delta_necesario / peor_peso), 6)`) antes de `math.ceil()`, manteniendo blindadas las evaluaciones continuas (`EC1`, `EC2`, `EC3`) y reemplazando exclusivamente `min(EP1, EP2, EP3)`.
     - Se implementó `evaluar_condicion_academica_normativa()` (líneas `156-243`), que unifica el cálculo de puntos acumulados, redondeo normativo (`10.49 -> 10 desaprobado`, `10.50 -> 11 aprobado`), puntos faltantes hacia `10.50`, nota mínima pendiente, viabilidad ordinaria, simulación de sustitutorio en `CP3` y activación automática de **Alerta Roja (`ROJO`)** ante imposibilidad matemática.
  2. `src/agents/preprocessing_agent.py`:
     - En `_compute_features()` (líneas `112-156`), se conservaron intactas las características de entrada a los modelos `.joblib` (`NOTA_MIN_PEND_F1`, `IMPOSIBLE_APROBAR_F1`, `NOTA_MIN_PEND_F2`, `IMPOSIBLE_APROBAR_F2`, `YA_APROBADO_CP3`) y se añadieron las claves normativas basadas en `10.50` (`PUNTOS_FALT_NORM_F1/F2/CP3`, `NOTA_MIN_NORM_PEND_F1/F2`, `IMPOSIBLE_APROBAR_NORM_F1/F2/CP3`, `PROM_TOTAL_REDONDEADO`).
  3. `src/agents/alert_agent.py`:
     - En `create_alert_package()` (líneas `45-97`), se conectó la determinación de `imposible_ordinario`, `meta_nota_min`, `is_alert = True` y `risk_level = "CRÍTICO"` (`#D32F2F`) a las variables normativas `*_NORM_*` basadas en `10.50` (manteniendo fallback a `IMPOSIBLE_APROBAR_F1/F2` para compatibilidad con diccionarios sintéticos de pruebas unitarias previas).

---

### 3.3. PRIORIDAD 3 — `F5-05`: Idempotencia de `seed_initial_data()`

- **Estado previo:** Confirmado en `src/database/db.py:312-356` y `1634-1636`.
- **Evidencia del defecto:** Cada ejecución de `seed_initial_data()` (invocada automáticamente al importar `src.database.db`) ejecutaba `INSERT OR IGNORE INTO perfil_semestre` e `INSERT OR IGNORE INTO explicaciones` sin verificar la existencia previa de la clave de negocio `(cui_hash, semestre)` ni `(prediccion_id)`. Asimismo, `save_student_profile()` ejecutaba siempre `INSERT` en lugar de actualizar el perfil existente del semestre.
- **Causa raíz:** Las tablas `perfil_semestre` y `explicaciones` tienen clave primaria autoincremental `id`, por lo que `INSERT OR IGNORE` sin restricción `UNIQUE` sobre las columnas de negocio nunca detectaba colisión e insertaba un nuevo registro en cada importación.
- **Archivos y funciones modificadas:**
  1. `src/database/db.py`:
     - Se habilitó la configuración de ruta por entorno `DB_PATH = os.environ.get("SATA_DB_PATH") or ...` (líneas `24-26`).
     - En `init_database()` (líneas `252-267`), se crean índices únicos sobre las claves naturales de negocio (`idx_perfil_cui_semestre` en `perfil_semestre(cui_hash, semestre)` e `idx_explicaciones_prediccion` en `explicaciones(prediccion_id)`) siempre que la tabla no contenga duplicados históricos preexistentes (respetando la prohibición de no limpiar ni alterar la base institucional).
     - En `seed_initial_data()` (líneas `273-432`), se reemplazó la inserción ciega por verificación explícita de existencia mediante las claves de negocio `(cui_hash, semestre)` en `perfil_semestre` y `prediccion_id = 1` en `explicaciones` (sin forzar `id = 1`), ejecutando `conn.commit()` únicamente si hubo cambios efectivos (`conn.total_changes > changes_before`).
     - En `save_student_profile()` (líneas `536-563`), se implementó lógica `UPSERT` (`UPDATE` si ya existe registro para `(cui_hash, semestre)`, o `INSERT` si es nuevo).
  2. `tests/conftest.py`:
     - Se configuró `os.environ.setdefault("SATA_DB_PATH", ...)` hacia un directorio temporal antes de importar `src.agents.coordinator_agent` (líneas `17-20`), garantizando que ni siquiera la importación inicial de `pytest` toque `src/database/sata_unsa.db`.

---

### 3.4. PRIORIDAD 4 — `F5-04`: Fidelidad XAI (`fidelidad_r`)

- **Estado previo:** Confirmado en `src/database/db.py:350, 902, 907, 922, 1544`.
- **Evidencia del defecto y distinción metodológica:**
  1. **Correlación global SHAP-LIME offline (`0.7778`):** El archivo `04_Modelo/fidelidad_shap_lime_cp1.json` contiene el resultado del experimento offline de validación cruzada entre SHAP y LIME en el Checkpoint 1 sobre `N = 100` estudiantes y `25` variables (`2,500` pares, correlación de Pearson `r = 0.7778` y coincidencia direccional de `77.78%`). Es una métrica **global de cohorte offline**, no una métrica por estudiante individual ni calculada en `CP0`, `CP2` o `CP3`.
  2. **Fidelidad local en tiempo de ejecución (`None`):** En producción interactiva, `XaiAgent` utiliza exclusivamente `shap.TreeExplainer(model)`, el cual calcula valores de Shapley exactos sobre el ensamble de árboles (propiedad de exactitud local aditiva $\sum \phi_i = f(x) - E[f(x)]$) y **no ejecuta un modelo sustituto LIME en tiempo real**, por lo que no existe un coeficiente `r` local por instancia en tiempo de ejecución.
  3. **Constante `0.96`:** El valor `0.96` que se insertaba en `explicaciones.fidelidad_r` era una constante ficticia hardcodeada en `db.py`.
- **Archivos y funciones modificadas:**
  1. `src/agents/xai_agent.py`:
     - En `XaiAgent.explain()` (línea `116`), se devuelve explícitamente `"fidelidad_r": None`.
     - Se implementó `normalize_local_fidelity(fidelidad)` (líneas `120-135`), que devuelve `None` cuando no existe medición local válida y rechaza valores booleanos, no numéricos o fuera de `[-1.0, 1.0]`.
     - Se implementó `get_offline_shap_lime_benchmark(models_dir)` (líneas `138-163`), que expone de forma diferenciada (`scope = "OFFLINE_GLOBAL_BENCHMARK"`) los resultados de `04_Modelo/fidelidad_shap_lime_cp1.json`.
  2. `src/database/db.py`:
     - En `seed_initial_data()` (línea `385`), `save_prediction_result()` (línea `708`), `persist_acta_row_transactional()` (líneas `806, 955-976`) y `evaluate_and_persist_enrollment()` (línea `1638`), se eliminó el literal `0.96` y se persistió `normalize_local_fidelity(xai.get("fidelidad_r"))` (`None` / `NULL` en SQLite cuando no se calcula fidelidad local).
     - Para evitar ciclos de importación (`ImportError` por dependencias circulares `db -> xai_agent -> agents.__init__ -> coordinator_agent -> db`), la función `normalize_local_fidelity` se importa de manera estrictamente local dentro de `save_prediction_result()`, `persist_acta_row_transactional()` y `evaluate_and_persist_enrollment()`, eliminando toda importación a nivel superior de módulo en `db.py`.

---

### 3.5. PRIORIDAD 5 — `F5-03`: Análisis de Priors de CP0 (Train-Serving Analysis)

- **Estado:** **Analizado / Pendiente de autorización** (Sin modificar valores ni modelos, en estricto cumplimiento de la restricción de la Sección 6).
- **Inspección del pipeline de entrenamiento vs. inferencia interactiva:**
  1. **Cómo se generaron en entrenamiento (`02_Scripts/build_features.py` y `02_Scripts/build_checkpoint_features.py`):**
     - En `build_features.py:68-139`, las variables `TASA_APROB_ACUM`, `DIFICULTAD_CURSO_HIST`, `DIFICULTAD_DOCENTE_HIST` y `DIFICULTAD_CURSO_DOCENTE_HIST` se construyeron sobre el corpus histórico longitudinal completo de la EPIS-UNSA (`2018-A` a `2025-B`, `matriculados_consolidado_full.csv` y `plan_funcionamiento_consolidado.csv`) usando una **ventana expansiva desplazada un periodo (`expanding().shift(1)`)** para evitar fuga de datos.
     - En `build_checkpoint_features.py:141-147`, cuando un registro carecía de historial previo (`NaN`), el pipeline activaba la bandera binaria `*_SIN_DATO = 1` e imputaba la media poblacional de la partición de entrenamiento (`<= 2022`).
  2. **Comparación con la inferencia interactiva (`src/agents/preprocessing_agent.py`, `src/database/db.py`, `src/services/academic_service.py`):**
     - La base de datos operativa `sata_unsa.db` contiene únicamente matrículas del semestre activo (`2026-B`) y **no almacena** el padrón histórico 2018–2025 (excluido por privacidad y tamaño).
     - En consecuencia, calcular dinámicamente `DIFICULTAD_CURSO_HIST` o `DIFICULTAD_DOCENTE_HIST` a partir de las tablas actuales de SQLite produciría una **distorsión severa train-serving (*train-serving skew*)**, ya que reemplazaría tasas históricas multi-anuales estabilizadas (`~0.08–0.12`) por proporciones muestrales de pocos alumnos del semestre en curso.
     - Se observó únicamente una diferencia menor entre los priors de `PreprocessingAgent.default_historical` (`TASA_APROB_ACUM=0.88`, `DIFICULTAD_CURSO_HIST=0.08`, `DIFICULTAD_DOCENTE_HIST=0.07`, `DIFICULTAD_CURSO_DOCENTE_HIST=0.08` con `*_SIN_DATO=1`) y los valores pasados en `db.py:1523-1531` y `academic_service.py:391-399` (`0.85, 0.12, 0.08, 0.10` con `*_SIN_DATO=0`).
  3. **Decisión y solicitud de autorización:**
     - Conforme a la restricción explícita de la Fase 6 (*"no modifiques estos valores ni sustituyas los priors por estadísticas dinámicas sin demostrar que se conserva la misma definición y distribución de las características utilizadas en el entrenamiento"*), **no se modificaron estos valores**.
     - Para alinearlos en el futuro sin reentrenar modelos, se requeriría autorización para exportar una tabla estática de solo lectura (`tasas_historicas_congeladas_2018_2025.json`) generada exactamente por `build_features.py` por asignatura normalizada.

---

### 3.6. REVISIÓN DE HALLAZGOS `LOW` (`F5-06` a `F5-09`)

- **`F5-06` (Despacho síncrono del `CoordinatorAgent`):** **Revisado y conservado.** La arquitectura utiliza colas FIFO `queue.Queue` reales y mensajes `AgentMessage` FIPA-ACL con despacho determinista por turnos en un hilo, lo que evita condiciones de carrera en el ciclo de renderizado reactivo de Streamlit y mantiene una latencia `< 150 ms`.
- **`F5-07` (Evaluación automática de `CP0` al matricular un curso):** **Corregido** en `app.py:2150-2152`, invocando `evaluate_and_persist_enrollment(mat_new_id, coordinator, current_user=usuario)` inmediatamente después de `enroll_course()`.
- **`F5-08` (Credenciales demo en `README.md`):** **Corregido** en `README.md:106-111`, actualizando la tabla documental con los 4 perfiles vigentes (`20220638 / Alumno123*`, `docente_demo / Docente123*`, `tutor_epis / Tutor123*`, `admin / Admin123*`).
- **`F5-09` (Archivos SQLite WAL/SHM en `.gitignore`):** **Corregido** en `.gitignore:33-35`, añadiendo `*.db-shm` y `*.db-wal` para evitar que archivos temporales de concurrencia de SQLite aparezcan como no rastreados.

---

## 4. PRUEBAS AÑADIDAS, RESULTADOS Y COBERTURA

### 4.1. Nuevas Pruebas Añadidas (`tests/test_phase6_audit_fixes.py`)
Se creó el módulo `tests/test_phase6_audit_fixes.py` con **13 pruebas automatizadas** organizadas en 4 clases correspondientes a cada prioridad:
1. `TestPrioridad1F502ControlAccesoDocente` (4 tests):
   - `test_docente_accesses_own_course_and_students`
   - `test_docente_denied_access_to_other_teacher_course_and_enrollment`
   - `test_docente_without_assignments_denied_by_default`
   - `test_admin_and_autoridad_preserve_legitimate_permissions_and_restrictions`
2. `TestPrioridad2F501UmbralAcademicoNormativo` (5 tests):
   - `test_final_rounded_grade_10_49_fails_and_triggers_red_alert`
   - `test_final_rounded_grade_10_50_passes`
   - `test_scenarios_still_mathematically_possible_to_pass_towards_10_50`
   - `test_scenarios_mathematically_impossible_to_pass_trigger_red_alert`
   - `test_substitutory_replaces_only_lowest_partial_and_never_continuous`
3. `TestPrioridad3F505IdempotenciaSeedInitialData` (1 test integral multi-etapa):
   - `test_first_second_and_repeated_module_initializations_create_zero_duplicates`
4. `TestPrioridad4F504FidelidadXaiCoherente` (3 tests):
   - `test_normalize_local_fidelity_rejects_fictitious_or_invalid_values`
   - `test_runtime_predictions_persist_null_fidelidad_instead_of_fictitious_096`
   - `test_offline_global_shap_lime_benchmark_is_distinct_and_accessible`

### 4.2. Comparativa de Ejecución y Cobertura (Antes vs. Después de Fase 6)

| Métrica | Antes de Fase 6 (Cierre Fase 5) | Después de Fase 6 (Actual) | Variación |
| :--- | :---: | :---: | :---: |
| **Total de Pruebas Ejecutadas** | `117 passed, 0 failed` | **`130 passed, 0 failed`** | **`+13 pruebas nuevas`** |
| **Cobertura Global (`TOTAL`)** | `86%` (`2,291` stmts) | **`87%` (`2,470` stmts)** | **`+1%` global** |
| `src/agents/preprocessing_agent.py` | `96%` | **`100%`** | `+4%` |
| `src/agents/alert_agent.py` | `100%` | **`100%`** | `=` |
| `src/agents/xai_agent.py` | `82%` | **`85%`** | `+3%` |
| `src/database/db.py` | `90%` | **`91%`** | `+1%` |
| `src/services/academic_service.py` | `83%` | **`85%`** | `+2%` |
| `src/security/access_control.py` | `84%` | **`84%`** | `=` (`+38` stmts nuevas) |

---

## 5. RIESGOS, OBSERVACIONES TÉCNICAS Y DICTAMEN FINAL

### 5.1. Riesgos y Observaciones Detectadas en Verificación
1. **Resolución de Ciclo de Importación en `src/database/db.py`:** Se eliminó la importación de `normalize_local_fidelity` a nivel superior de módulo en `db.py:14`, trasladándola al interior de las funciones de persistencia (`save_prediction_result`, `persist_acta_row_transactional` y `evaluate_and_persist_enrollment`). Se verificó la importación aislada con `python -c "import src.database.db; print('IMPORT_DB_OK')"` (exit code 0), la importación de la aplicación con `python -c "import app; print('IMPORT_APP_OK')"` (exit code 0) y las 13 pruebas específicas (exit code 0).
2. **Congelamiento de Tasas Históricas 2018–2025 por Asignatura (`F5-03`):** Para sustituir los priors constantes de `DIFICULTAD_CURSO_HIST` y `DIFICULTAD_DOCENTE_HIST` en inferencia interactiva sin provocar *train-serving skew*, se requiere autorización para extraer de los datasets históricos originales un catálogo JSON anonimizado de tasas históricas por asignatura y docente.
3. **Limpieza de Duplicados Históricos en `src/database/sata_unsa.db` (`F5-05`):** Aunque `seed_initial_data()` ya es 100% idempotente y no vuelve a insertar filas duplicadas, la base de datos institucional en disco conserva las 55 filas redundantes generadas en fases anteriores porque las reglas de la Fase 6 prohíben modificar o eliminar registros de `src/database/sata_unsa.db`. Si el usuario lo autoriza posteriormente, puede ejecutarse una sentencia puntual de depuración sobre `sata_unsa.db`.

### 5.2. Dictamen de Verificación Previa al Commit
> **VERIFICACIÓN TÉCNICA Y CIENTÍFICA APROBADA AL 100% (`130/130` pruebas aprobadas, `87%` de cobertura global, ciclo de importación resuelto, modelos `.joblib`, umbrales calibrados y base de datos institucional 100% intactos). Estado: LISTO PARA COMMIT.**
