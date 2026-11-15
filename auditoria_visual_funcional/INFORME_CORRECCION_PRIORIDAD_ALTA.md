# INFORME TÉCNICO DE CORRECCIÓN DE DEFECTOS DE PRIORIDAD ALTA — SATA-UNSA (FASE 3)

- **Sistema:** SATA-UNSA (Sistema de Alerta Temprana Académica — EPIS / FIPS — UNSA)
- **Rama de trabajo:** `fix-ui-acceso`
- **Entorno verificado en vivo:** `http://localhost:8501`
- **Documentos base de referencia:**
  - [INFORME_AUDITORIA_EXHAUSTIVA.md](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/INFORME_AUDITORIA_EXHAUSTIVA.md) (Fase 1)
  - [INFORME_CORRECCION_CRITICOS.md](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/INFORME_CORRECCION_CRITICOS.md) (Fase 2)

---

## 1. Resumen Ejecutivo

En esta tercera fase de ingeniería se resolvieron íntegramente los **cinco grupos de defectos de Prioridad Alta (A–E)** detectados durante la auditoría exhaustiva original de SATA-UNSA, manteniendo intactos los modelos serializados Random Forest (`CP0`–`CP3`), los umbrales calibrados (`0.285`, `0.340`, `0.495`, `0.765`), el protocolo FIPA-ACL, la criptografía `HMAC-SHA256` / `PBKDF2-HMAC-SHA256`, la base de datos SQLite en modo WAL y las cinco correcciones críticas de la Fase 2.

| Grupo | Defecto de Prioridad Alta | Estado | Verificación |
| :--- | :--- | :---: | :--- |
| **A** | Selectores reales de asignatura y estudiante anonimizado para `DOCENTE` (eliminación de `mat_id_act = 1` y `7f3a...c91`) | **CORREGIDO** | Código + Pytest + Navegador |
| **B** | Integración real del bus FIPA-ACL con `mensajes_bus` y performativas `REQUEST`, `INFORM`, `PROPOSE` y `FAILURE` | **CORREGIDO** | Código + Pytest + Navegador |
| **C** | Eliminación de datos ficticios en sub-cabecera común (`18`, `3`) y en reportes PDF (`generate_intervention_pdf`) | **CORREGIDO** | Código + Pytest + Navegador |
| **D** | Módulo funcional de tutorías, bitácora, checklist interactivo y botón `Ver explicación` con persistencia real en SQLite | **CORREGIDO** | Código + Pytest + Navegador |
| **E** | Formulario completo TAM e integración de funciones backend (`calcular_simulacion_sustitutorio`, `save_grade`, `update_student_consent`) | **CORREGIDO** | Código + Pytest + Navegador |

- **Resultado de la suite de pruebas (`pytest --cov=src --cov=app`):** **116 pruebas aprobadas, 0 fallidas** (incremento desde 102 pruebas en Fase 2).
- **Cobertura global de código:** **86 %** (incremento de +21 puntos porcentuales respecto al 65 % de Fase 2).

---

## 2. Defectos Corregidos

### A. Selectores reales para el rol `DOCENTE`
- **Problema original:** En las vistas `Detalle con explicabilidad` (Vista 2) y `Seguimiento y plan de tutoría` (Vista 4), el rol `DOCENTE` carecía de selectores de asignatura y estudiante; el código fijaba estáticamente `mat_id_act = 1` y la cadena ficticia `CUI 7f3a...c91`.
- **Solución implementada:**
  - Se incorporaron selectores encadenados de **Asignatura** (`catalogo_cursos`) y **Estudiante (ID Anonimizado)** alimentados en tiempo real por `get_course_students_table(curso_sel, "2026-B", current_user=usuario)`.
  - Se eliminaron por completo de `app.py` las asignaciones estáticas `mat_id_act = 1` y `7f3a...c91`.
  - Se respeta estrictamente el consentimiento informado (*opt-in*): cuando `comparte_con_tutor == 1` se muestra el hash truncado del estudiante, y cuando `comparte_con_tutor == 0` se muestra el código reservado `RES-XXXXXX`.
  - Si una asignatura no posee matrículas evaluadas aún, se presenta un estado vacío explícito e informativo sin inventar datos de respaldo.

### B. Integración real del bus FIPA-ACL
- **Problema original:** `CoordinatorAgent.analyze_student_risk()` no persistía los mensajes individuales del bus en la tabla `mensajes_bus` durante las evaluaciones directas, `RecommendationAgent` emitía `INFORM` en lugar de `PROPOSE`, y la vista `Trazabilidad multiagente` contenía 4 líneas de texto ficticias hardcodeadas como fallback.
- **Solución implementada:**
  - En `src/agents/recommendation_agent.py`, la respuesta con el plan de acción pedagógico utiliza la performativa estándar **`PROPOSE`**.
  - En `src/messaging/bus.py`, `MessageBus._extract_topic()` clasifica semánticamente el tópico de cada mensaje (`INGEST`, `INGEST_OK`, `VALIDATION_FAILURE`, `PREPROCESS`, `FEATURES_CP*`, `PREDICT`, `PREDICT_CP*`, `EXPLAIN`, `SHAP_CP*`, `RECOMMEND`, `PROPOSE_TUTORIA_CP*`, `GENERATE_ALERT`, `ALERT_*`) sin exponer datos sensibles.
  - En `src/agents/coordinator_agent.py`, `analyze_student_risk()` persiste todos los mensajes FIPA-ACL generados en la conversación mediante `log_bus_message()` (tanto en ejecuciones exitosas como cuando `IngestionAgent` emite **`FAILURE`**), agrupando el commit por transacción para preservar la latencia H3 (`< 1.5 s`).
  - En `app.py` (Vista 3), se eliminó el arreglo ficticio de mensajes y se conectó directamente con `get_bus_messages_for_student()` (para `ESTUDIANTE`) y `get_recent_bus_messages()` (para personal autorizado), mostrando marca temporal, ID de conversación anonimizado, performativa (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`), emisor, receptor y tópico.

### C. Eliminación de datos ficticios de la cabecera y de los reportes PDF
- **Problema original:**
  1. La sub-cabecera común asignaba valores estáticos `total_est = 18` y `tutorias_sem = 3` para `AUTORIDAD` y `ADMIN`, `tutorias_sem = 1` para `ESTUDIANTE`, y mostraba la fecha del reloj del sistema en lugar de la fecha real de actualización en base de datos.
  2.En Vista 4, el botón `Exportar informe PDF` invocaba `generate_intervention_pdf()` con valores hardcodeados (`umbral_pct=34.0`, `meta_nota_min=13.5`, `promedio_acumulado=8.4`, `[{"label": "Asistencia acumulada baja", "value": 0.42}]`), y la gráfica longitudinal inventaba `["Sem 1", "Sem 8", "Sem 16"]` / `[22.0, 48.0, 78.0]`.
- **Solución implementada:**
  - Se implementó `get_header_metrics(current_user, semestre="2026-B")` en `src/database/db.py`, que consulta SQLite en tiempo real:
    - Para `ESTUDIANTE`: `ASIGNATURAS INSCRITAS` (`COUNT(*)` en `matriculas`), `TUTORÍAS REGISTRADAS` (`COUNT(*)` en `tutorias`) y `ÚLTIMA ACTUALIZACIÓN` (`MAX(fecha)` de sus predicciones).
    - Para `DOCENTE`, `AUTORIDAD` y `ADMIN`: `ESTUDIANTES EN SEGUIMIENTO` (`COUNT(*)` en `matriculas` del semestre), `TUTORÍAS ESTA SEMANA` (`COUNT(*)` en `tutorias`) y `ÚLTIMA ACTUALIZACIÓN` (`MAX(fecha)` en `predicciones`).
  - En Vista 4 (`app.py`), `generate_intervention_pdf()` recibe exclusivamente los campos reales de `get_latest_prediction(mat_id_act, current_user=usuario)` (`checkpoint`, `probabilidad * 100`, `umbral * 100`, `semaforo`, `meta_nota_min`, `promedio_acumulado`, `imposible_ordinario`, `top_factors`, `recommendations`).
  - La gráfica longitudinal grafica únicamente los checkpoints reales persistidos en `get_prediction_history(mat_id_act, current_user=usuario)`.

### D. Módulo funcional de tutorías, bitácora y navegación `Ver explicación`
- **Problema original:** Los botones `Programar tutoría` y `Registrar tutoría` solo mostraban un banner `st.success` sin guardar nada en SQLite; las 3 casillas del plan de acción eran `<div>` estáticos con fechas fijas; no existía tabla de historial de tutorías; y el botón `Ver explicación` solo mostraba un mensaje informativo sin navegar.
- **Solución implementada:**
  - Se creó la tabla relacional `tutorias` en `init_database()` (`src/database/db.py`) con clave foránea a `matriculas(id)` y columnas para `estado` (`PROGRAMADA`, `REALIZADA`, `SEGUIMIENTO`), `fecha_sesion`, `observaciones`, `accion_1_ok`, `accion_2_ok`, `accion_3_ok`, `responsable`, `rol_registro` y `fecha_registro`.
  - Se implementaron las funciones `schedule_tutoring_session()`, `register_tutoring_session()`, `get_tutoring_history()` y `get_tutoring_checklist_state()`, todas protegidas por `validate_matricula_ownership()` y con registro de trazabilidad en `mensajes_bus`.
  - `register_tutoring_session()` valida que la fecha y las observaciones pedagógicas obligatorias estén completas antes de persistir en SQLite y mostrar confirmación.
  - En Vista 4 se integraron 3 controles interactivos `st.checkbox` (`Acción 1`, `Acción 2`, `Acción 3`), campos de fecha, estado y observaciones, y la tabla **Historial y Bitácora de Sesiones de Tutoría**.
  - En Vista 1, el botón `Ver explicación` sincroniza `st.session_state["selected_student_mat"]` y `st.session_state["pending_nav"] = "Detalle con explicabilidad"`, redirigiendo inmediatamente mediante `st.rerun()`.

### E. Formulario TAM completo y conexión de funciones backend huérfanas
- **Problema original:** La vista `Encuestas SUS / TAM` solo contenía el formulario SUS (guardando siempre el rol estático `"DOCENTE_EVAL"`) y carecía del cuestionario TAM. Además, las funciones `calcular_simulacion_sustitutorio`, `save_grade` y `update_student_consent` no estaban conectadas a ningún flujo de la interfaz.
- **Solución implementada:**
  1. **Formulario TAM (`Encuestas SUS / TAM`):** Se organizó la vista en dos pestañas (`Cuestionario SUS` y `Cuestionario TAM`), incorporando los 6 ítems estandarizados de Davis (Utilidad Percibida `PU1`–`PU3`, Facilidad de Uso Percibida `PEOU1`–`PEOU2` e Intención de Uso `BI1`) en escala Likert 1–5, persistiendo mediante `save_survey(usuario["username"], rol, "TAM", ...)` y actualizando el indicador `Puntuación Media TAM (Aceptación)`.
  2. **`calcular_simulacion_sustitutorio`:** Integrada en Vista 4 dentro del panel **Simulador Normativo de Examen Sustitutorio (UNSA)**, permitiendo evaluar con las notas actuales o proyectadas (`EC1..EP3`) y los pesos del sílabo qué examen parcial (`min(EP1, EP2, EP3)`) se reemplaza y cuál es la nota mínima requerida para alcanzar el promedio aprobatorio normativo (`>= 10.50`).
  3. **`save_grade` + `evaluate_and_persist_enrollment` + `get_grade_change_history`:** Conectadas en Vista 4 dentro del panel **Registro y Rectificación de Notas Parciales**, permitiendo registrar o rectificar calificaciones (`EC1..EP3` o `Ausente/NSP`), generando automáticamente el registro de auditoría en `historial_cambios` y recalculando la alerta con el Sistema Multiagente.
  4. **`update_student_consent`:** Conectada en la vista **Perfil Basal** del rol `ESTUDIANTE` mediante el formulario **Consentimiento Informado y Privacidad de Tutoría (Opt-In)**, permitiendo al alumno activar o revocar el uso compartido de su identificador con el tutor (`comparte_con_tutor`).

---

## 3. Archivos Modificados y Creados

| Archivo | Tipo de Cambio | Descripción Técnica |
| :--- | :---: | :--- |
| [src/database/db.py](file:///d:/TESIS%20FINAL/src/database/db.py) | Modificado | Tabla `tutorias`, siembra inicial FIPA-ACL/tutoría, y funciones `get_enrollment_by_id`, `get_grade_change_history`, `get_tutoring_checklist_state`, `get_tutoring_history`, `schedule_tutoring_session`, `register_tutoring_session`, `get_header_metrics`, `evaluate_and_persist_enrollment` y soporte de conexión compartida en `log_bus_message`. |
| [src/agents/recommendation_agent.py](file:///d:/TESIS%20FINAL/src/agents/recommendation_agent.py) | Modificado | Emisión de performativa estándar FIPA-ACL `PROPOSE` al entregar el plan de intervención pedagógica. |
| [src/messaging/bus.py](file:///d:/TESIS%20FINAL/src/messaging/bus.py) | Modificado | Extracción de tópico semántico (`_extract_topic`) y marca temporal ISO en `get_history_summary()`. |
| [src/agents/coordinator_agent.py](file:///d:/TESIS%20FINAL/src/agents/coordinator_agent.py) | Modificado | Persistencia transaccional en SQLite de todos los mensajes FIPA-ACL (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`) mediante `log_bus_message()` cuando `persist_telemetry=True`. |
| [app.py](file:///d:/TESIS%20FINAL/app.py) | Modificado | Cabecera conectada a `get_header_metrics()`, selectores reales para `DOCENTE`, terminal FIPA-ACL sin datos ficticios, módulo completo de tutorías/bitácora/PDF real, navegación `Ver explicación`, formulario TAM, simulador de sustitutorio, registro de notas y gestión de consentimiento *opt-in*. |
| [tests/test_high_priority_fixes.py](file:///d:/TESIS%20FINAL/tests/test_high_priority_fixes.py) | Creado | 14 nuevas pruebas unitarias y de integración (`AppTest`) que validan todos los requisitos de los Grupos A–E y permisos por rol. |

---

## 4. Funciones Conectadas en la Interfaz

| Función Backend | Módulo | Vista donde quedó integrada | Rol autorizado |
| :--- | :--- | :--- | :--- |
| `get_header_metrics` | `src/database/db.py` | Sub-cabecera común (todas las vistas autenticadas) | Todos los roles (aislado por rol) |
| `schedule_tutoring_session` | `src/database/db.py` | Vista 1 (`Panel de seguimiento`) y Vista 2 (`Detalle con explicabilidad`) | `ESTUDIANTE`, `DOCENTE` |
| `register_tutoring_session` | `src/database/db.py` | Vista 4 (`Seguimiento y plan de tutoría`) | `ESTUDIANTE`, `DOCENTE` |
| `get_tutoring_history` | `src/database/db.py` | Vista 4 (`Historial y Bitácora de Sesiones de Tutoría`) | `ESTUDIANTE`, `DOCENTE` |
| `get_tutoring_checklist_state` | `src/database/db.py` | Vista 4 (`Plan de Acción Tutorial y Compromisos Pedagógicos`) | `ESTUDIANTE`, `DOCENTE` |
| `save_grade` + `evaluate_and_persist_enrollment` | `src/database/db.py` | Vista 4 (`Registro y Rectificación de Notas Parciales`) | `ESTUDIANTE`, `DOCENTE` |
| `get_grade_change_history` | `src/database/db.py` | Vista 4 (`Auditoría de rectificaciones registradas`) | `ESTUDIANTE`, `DOCENTE` |
| `calcular_simulacion_sustitutorio` | `src/services/academic_service.py` | Vista 4 (`Simulador Normativo de Examen Sustitutorio`) | `ESTUDIANTE`, `DOCENTE` |
| `update_student_consent` | `src/database/db.py` | Vista `Perfil Basal` (`Consentimiento Informado y Privacidad Opt-In`) | `ESTUDIANTE` |
| `save_survey(..., "TAM", ...)` | `src/database/db.py` | Vista `Encuestas SUS / TAM` (Pestaña `Cuestionario TAM`) | `ADMIN` |

---

## 5. Pruebas Creadas y Resultados de Cobertura (`pytest`)

Se ejecutó la suite completa de pruebas automatizadas con aislamiento total de base de datos (`isolated_test_database`):

```text
116 passed in 116.55s (0:01:56)
TOTAL coverage: 86% (2286 statements, 315 missed)
```

### Desglose de Cobertura por Módulo
| Módulo | Sentencias | Sin cubrir | Cobertura Fase 2 | Cobertura Fase 3 |
| :--- | :---: | :---: | :---: | :---: |
| `app.py` | 692 | 151 | 8 % | **78 %** |
| `src/agents/alert_agent.py` | 35 | 0 | 100 % | **100 %** |
| `src/agents/base_agent.py` | 16 | 0 | 100 % | **100 %** |
| `src/agents/coordinator_agent.py` | 128 | 6 | 97 % | **95 %** |
| `src/agents/ingestion_agent.py` | 84 | 20 | 76 % | **76 %** |
| `src/agents/predictor_agent.py` | 50 | 2 | 96 % | **96 %** |
| `src/agents/preprocessing_agent.py` | 83 | 3 | 96 % | **96 %** |
| `src/agents/recommendation_agent.py` | 45 | 5 | 89 % | **89 %** |
| `src/agents/xai_agent.py` | 91 | 16 | 82 % | **82 %** |
| `src/database/db.py` | 567 | 57 | 83 % | **90 %** |
| `src/messaging/bus.py` | 52 | 7 | 88 % | **87 %** |
| `src/reports/pdf_generator.py` | 150 | 4 | 97 % | **97 %** |
| `src/security/access_control.py` | 38 | 6 | 84 % | **84 %** |
| `src/security/crypto.py` | 44 | 6 | 86 % | **86 %** |
| `src/services/academic_service.py` | 176 | 30 | 90 % | **83 %** |
| **TOTAL GLOBAL** | **2286** | **315** | **65 %** | **86 %** |

---

## 6. Verificación Visual y Funcional en Navegador (`http://localhost:8501`)

Todas las correcciones fueron verificadas directamente en el navegador sobre `http://localhost:8501` y sus capturas de evidencia se almacenaron en `auditoria_visual_funcional/evidencias/06_post_correccion_prioridad_alta/`:

1. **Selectores reales de Asignatura y Estudiante en `DOCENTE` + Navegación `Ver explicación`:**
   - [01_docente_selectores_xai.png](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/evidencias/06_post_correccion_prioridad_alta/01_docente_selectores_xai.png)
2. **Terminal FIPA-ACL conectada a `mensajes_bus` con performativas `REQUEST`, `INFORM`, `PROPOSE`:**
   - [02_docente_trazabilidad_fipa_acl.png](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/evidencias/06_post_correccion_prioridad_alta/02_docente_trazabilidad_fipa_acl.png)
   - [04_estudiante_trazabilidad_fipa_acl.png](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/evidencias/06_post_correccion_prioridad_alta/04_estudiante_trazabilidad_fipa_acl.png)
3. **Módulo de Tutorías, Checklist Interactivo, Bitácora Histórica, Registro de Notas y Simulador de Sustitutorio:**
   - [03_docente_seguimiento_bitacora.png](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/evidencias/06_post_correccion_prioridad_alta/03_docente_seguimiento_bitacora.png)
4. **Cuestionario TAM (Technology Acceptance Model) funcional en `Encuestas SUS / TAM`:**
   - [05_admin_encuestas_sus_tam.png](file:///d:/TESIS%20FINAL/auditoria_visual_funcional/evidencias/06_post_correccion_prioridad_alta/05_admin_encuestas_sus_tam.png)

---

## 7. Estado de las Funcionalidades por Rol

| Rol | Vistas Autorizadas | Estado Funcional | Privacidad y RBAC |
| :--- | :--- | :---: | :--- |
| **ESTUDIANTE** | `Panel de seguimiento`, `Detalle con explicabilidad`, `Trazabilidad multiagente`, `Seguimiento y plan de tutoría`, `Inscribir Asignatura`, `Perfil Basal` | **100 % Operativo** | Estricto aislamiento a sus propias matrículas; control *opt-in* en `Perfil Basal`. |
| **DOCENTE** | `Panel de seguimiento`, `Detalle con explicabilidad`, `Trazabilidad multiagente`, `Seguimiento y plan de tutoría`, `Carga Masiva de Actas` | **100 % Operativo** | Selectores reales por curso y alumno anonimizado; respeta `RES-XXXXXX` cuando no hay *opt-in*. |
| **AUTORIDAD** | `Panel de seguimiento` (agregado por sección), `Métricas Institucionales`, `Trazabilidad multiagente` | **100 % Operativo** | Acceso exclusivo a métricas consolidadas; bloqueado a registros individuales. |
| **ADMIN** | `Panel de seguimiento` (operativo RBAC), `Monitor Técnico OBJ5`, `Trazabilidad multiagente`, `Encuestas SUS / TAM` | **100 % Operativo** | Telemetría real OBJ5 y encuestas SUS/TAM; bloqueado a notas individuales. |

---

## 8. Observaciones Restantes de Prioridad Media o Baja

- **Prioridad Baja (Estética en Viewport Móvil `< 768px`):** En resoluciones móviles muy estrechas, cuando el menú lateral desplegable permanece abierto cubre parcialmente el área derecha hasta que el usuario lo repliega con el botón superior `<<`. No afecta la funcionalidad ni el diseño en escritorio.
- **Integridad de Datos Institucionales:** La base de datos `src/database/sata_unsa.db` se mantiene limpia con únicamente los catálogos oficiales EPIS-UNSA y la semilla de demostración anonimizada.
