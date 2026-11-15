# AUDITORÍA EXHAUSTIVA VISUAL, FUNCIONAL Y DE SEGURIDAD DE SATA-UNSA

**Proyecto:** Sistema de Alerta Temprana Académica (SATA-UNSA) — EPIS / FIPS, Universidad Nacional de San Agustín de Arequipa  
**Rama auditada:** `fix-ui-acceso`  
**URL de ejecución verificada:** `http://localhost:8501`  
**Fecha de auditoría:** 13 de noviembre de 2026  
**Alcance:** Inspección integral en navegador real (Escritorio `1280x800` y Móvil `375x812`) a través de los 4 roles del sistema (`ESTUDIANTE`, `DOCENTE`, `AUTORIDAD`, `ADMIN`) contrastada línea por línea con el código fuente (`app.py` y paquetes bajo `src/`). No se realizó ninguna modificación al código ni a la base de datos.

---

## A. RESUMEN EJECUTIVO

Se evaluaron **82 requisitos atómicos** desglosados en la matriz oficial de especificación (Sección B), calificando de manera independiente el **cumplimiento visual** y el **cumplimiento funcional** de cada componente.

### Tabla Consolidada de Cumplimiento (82 Requisitos Evaluados)

| Estado de Clasificación | Dimensión Visual (Cant.) | Dimensión Visual (%) | Dimensión Funcional (Cant.) | Dimensión Funcional (%) |
| :--- | :---: | :---: | :---: | :---: |
| **CUMPLE** | 49 | **59.76 %** | 41 | **50.00 %** |
| **CUMPLE PARCIALMENTE** | 21 | **25.61 %** | 16 | **19.51 %** |
| **NO CUMPLE** | 12 | **14.63 %** | 25 | **30.49 %** |
| **NO VERIFICABLE** | 0 | **0.00 %** | 0 | **0.00 %** |
| **TOTAL AUDITADO** | **82** | **100.00 %** | **82** | **100.00 %** |

* **Porcentaje de Cumplimiento Visual Estricto (`CUMPLE`):** **59.76 %** (49 / 82). *(Si se pondera `CUMPLE PARCIALMENTE` al 50 %, el índice visual ponderado es de **72.56 %**).*
* **Porcentaje de Cumplimiento Funcional Estricto (`CUMPLE`):** **50.00 %** (41 / 82). *(Si se pondera `CUMPLE PARCIALMENTE` al 50 %, el índice funcional ponderado es de **59.76 %**).*

### Distribución de Hallazgos por Severidad (22 Problemas Documentados en Sección D)

| Severidad | Cantidad | Resumen de Impacto Principal |
| :--- | :---: | :--- |
| **CRÍTICA** | **5** | 1) Crash `AuthorizationError` no capturado al entrar como `ADMIN` en `Panel de seguimiento`; 2) Crash `KeyError: 'latencia_inf_media_ms'` en `Monitor Técnico OBJ5`; 3) Exposición de datos individuales de alumnos al rol `AUTORIDAD` en `Panel de seguimiento` (violando el principio de vista agregada sin acceso a identidades); 4) Barras SHAP en Vista 2 muestran la nota/valor bruto observado (`+9.00`, `+8.00`, `+11.50`, `+6.00`) en lugar del impacto SHAP real (`f["impact"]`), invirtiendo factores protectores (`-0.05` en Carga Académica) a color granate positivo (`+6.00`); 5) Carga masiva de actas del Docente procesa en memoria volátil sin persistir notas, matrículas, predicciones, trazas FIPA-ACL ni métricas técnicas en SQLite. |
| **ALTA** | **8** | 6) Ausencia total de selectores de asignatura y estudiante para el rol `DOCENTE` en Vistas 2 y 4 (hardcodeado a `mat_id_act = 1` y `CUI 7f3a...c91`); 7) Botones `Programar tutoría`, `Ver explicación` y `Registrar tutoría` son simulacros visuales (`st.success` / `st.info`) sin persistencia ni navegación real; 8) Callejón sin salida para `AUTORIDAD` al pulsar `Ver explicación` (remite a una vista inexistente en su menú); 9) Bitácora de compromisos en Vista 4 es HTML estático con fechas hardcodeadas no interactivas; 10) Exportación PDF en Vista 4 inyecta factores SHAP, umbral (`34.0%`), meta (`13.5`) y recomendaciones hardcodeadas en lugar de la predicción real del alumno; 11) Ausencia del formulario de preguntas TAM en `Encuestas SUS / TAM` y rol hardcodeado como `DOCENTE_EVAL`; 12) Mensajes FIPA-ACL no se persisten en SQLite (`mensajes_bus` vacío), mostrando siempre 4 líneas estáticas de fallback; 13) Métricas de la sub-cabecera (`ESTUDIANTES EN SEGUIMIENTO`, `TUTORÍAS ESTA SEMANA`, `ÚLTIMA ACTUALIZACIÓN`) usan valores ficticios hardcodeados (`18` y `03` para Autoridad/Admin) o desincronizados (`00` en Docente). |
| **MEDIA** | **6** | 14) Ningún botón primario (`type="primary"`) tiene fondo granate debido a que el selector CSS `.stButton button:not([data-testid="baseButton-primary"])` sobreescribe todos los botones en versiones actuales de Streamlit (`stBaseButton-primary`); 15) Contraste ilegible en el Sidebar (texto de opciones radio en negro `#0F172A` y botón `Cerrar Sesión` en texto granate `#7A1C20` sobre fondo granate oscuro `#5A1215`); 16) Ligadura rota de Material Icons en el botón de colapso del sidebar que muestra el texto gigante cortado `keyboard_double_`; 17) Cuerpo de la terminal FIPA-ACL tiene fondo blanco (`#FFFFFF`) en lugar de fondo granate oscuro, performativas en minúscula y omite el contenido del mensaje cuando lee de BD; 18) Omisión visual del Checkpoint activo (`CP0`–`CP3`) en la tarjeta de diagnóstico de Vista 2 y omisión de la tendencia `"a la baja"` en Vista 4; 19) El gráfico longitudinal usa fallback estático (`Sem 1`, `Sem 8`, `Sem 16`) y umbrales fijos (`34%` y `75%`) que no se adaptan dinámicamente al checkpoint ni coinciden con la regla `0.75 * umbral` del backend. |
| **BAJA** | **3** | 20) El botón flotante `>>` de reapertura del sidebar (`position: fixed; z-index: 999999`) se superpone a los títulos y textos superiores al hacer scroll en escritorio y móvil; 21) Colisión sin espaciado (`0px`) entre el hash CUI y el nombre en las filas de estudiantes del Docente (`CUI E7BB88B1B2BDD47FEstudiante (A)`); 22) Columna `semestre` sin renombrar ni formatear en la tabla de `Métricas Institucionales` de Autoridad. |

---

## B. MATRIZ DETALLADA POR PANTALLA

| # | Pantalla | Rol | Elemento | Estado visual | Estado funcional | Severidad | Evidencia |
| :-: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | **Pantalla 0: Acceso / Login** | Todos | Escudo oficial UNSA | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 2 | Pantalla 0: Acceso / Login | Todos | Título SATA-UNSA | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 3 | Pantalla 0: Acceso / Login | Todos | Descripción de la plataforma | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 4 | Pantalla 0: Acceso / Login | Todos | Identificación de FIPS y EPIS | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 5 | Pantalla 0: Acceso / Login | Todos | Banner institucional granate | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 6 | Pantalla 0: Acceso / Login | Todos | Filigrana dorada (`.unsa-banner-fillet`) | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 7 | Pantalla 0: Acceso / Login | Todos | Correcta distribución de columnas (`[1.1, 1]`) | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 8 | Pantalla 0: Acceso / Login | Todos | Columna ética: Banner de Ingeniería de Sistemas (`banner_epis.png`) | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 9 | Pantalla 0: Acceso / Login | Todos | Columna ética: Declaración de estimaciones orientativas y no sentencias | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 10 | Pantalla 0: Acceso / Login | Todos | Columna ética: Información sobre HMAC-SHA256 | CUMPLE | CUMPLE | — | `evidencias/00_login/01_login_escritorio_arriba.png` |
| 11 | Pantalla 0: Acceso / Login | Todos | Columna ética: Información sobre PBKDF2 (100,000 iteraciones) | CUMPLE | CUMPLE | — | `evidencias/00_login/02_login_escritorio_abajo.png` |
| 12 | Pantalla 0: Acceso / Login | Todos | Columna ética: Declaración de protección y aislamiento de datos | CUMPLE | CUMPLE | — | `evidencias/00_login/02_login_escritorio_abajo.png` |
| 13 | Pantalla 0: Acceso / Login | Estudiante | Botón Acceso Rápido: Estudiante Demo | CUMPLE | CUMPLE | — | `evidencias/00_login/02_login_escritorio_abajo.png` |
| 14 | Pantalla 0: Acceso / Login | Docente | Botón Acceso Rápido: Docente/Tutor | CUMPLE | CUMPLE | — | `evidencias/00_login/02_login_escritorio_abajo.png` |
| 15 | Pantalla 0: Acceso / Login | Autoridad | Botón Acceso Rápido: Autoridad/Comité | CUMPLE | CUMPLE | — | `evidencias/00_login/02_login_escritorio_abajo.png` |
| 16 | Pantalla 0: Acceso / Login | Admin | Botón Acceso Rápido: Administrador | CUMPLE | CUMPLE | — | `evidencias/00_login/02_login_escritorio_abajo.png` |
| 17 | Pantalla 0: Acceso / Login | Todos | Pestaña Iniciar Sesión y Pestaña Registro de Estudiante | CUMPLE | CUMPLE | — | `evidencias/00_login/05_pestana_registro_estudiante.png` |
| 18 | Pantalla 0: Acceso / Login | Todos | Alternancia entre Estudiante y Docente/Personal (radio horizontal) | CUMPLE | CUMPLE | — | `evidencias/00_login/04_login_modo_personal.png` |
| 19 | Pantalla 0: Acceso / Login | Todos | Campos de credenciales, validaciones y mensajes de error | CUMPLE | CUMPLE | — | `evidencias/00_login/03_login_validacion_vacio.png`, `06_registro_validacion_error.png` |
| 20 | Pantalla 0: Acceso / Login | Todos | Botón granate `Ingresar al Portal del Estudiante` / `Ingresar al Sistema` | **NO CUMPLE** | CUMPLE | **MEDIA** | Se ve blanco/transparente con borde dorado por bug de especificidad CSS (`app.py:271`). Ver `01_login_escritorio_arriba.png` |
| 21 | **Cabecera Común Autenticada** | Todos | Escudo UNSA, Banner institucional, Facultad/Escuela y Semestre `2026-B` | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/03_vista1_panel_seguimiento_arriba.png` |
| 22 | Cabecera Común Autenticada | Todos | Sidebar granate y logo/banner EPIS | CUMPLE PARCIALMENTE | CUMPLE | **MEDIA** | Fondo granate correcto, pero opciones de radio se ven negras (`#0F172A`) e ilegibles sobre fondo granate (`app.py:199-202`). Ver `01_estudiante/01_cabecera_y_sidebar_abierto.png` |
| 23 | Cabecera Común Autenticada | Estudiante | Identificación del usuario: Hash anonimizado para estudiantes | CUMPLE | CUMPLE | — | Muestra `E7BB88B1B2BDD47F` en saludo y `E7BB88B1B2...` en sidebar (`01_estudiante/01_cabecera_y_sidebar_abierto.png`) |
| 24 | Cabecera Común Autenticada | Personal | Nombre de usuario y rol para personal (`docente_demo`, `tutor_epis`, `admin`) | CUMPLE | CUMPLE | — | `evidencias/04_administrador/01_cabecera_y_sidebar_admin.png` |
| 25 | Cabecera Común Autenticada | Todos | Menú de navegación correspondiente al rol | CUMPLE PARCIALMENTE | **CUMPLE PARCIALMENTE** | **CRÍTICA** | `ADMIN` incluye `Panel de seguimiento` que lanza `AuthorizationError`, y `AUTORIDAD` carece de `Detalle con explicabilidad` aunque el botón `Ver explicación` lo exige |
| 26 | Cabecera Común Autenticada | Todos | Botón `Cerrar Sesión` | **CUMPLE PARCIALMENTE** | CUMPLE | **MEDIA** | Funciona bien, pero su texto es color granate (`#7A1C20`) sobre fondo granate oscuro (`#5A1215`), casi invisible (`01_estudiante/01_cabecera_y_sidebar_abierto.png`) |
| 27 | Cabecera Común Autenticada | Todos | Colapso y reapertura del sidebar (Escritorio y Móvil) | **NO CUMPLE** | CUMPLE | **MEDIA** | Al abrirse muestra texto gigante roto `keyboard_double_` por sobreescritura de fuente de iconos (`app.py:225`) y el botón `>>` tapa los títulos al hacer scroll |
| 28 | Cabecera Común Autenticada | Todos | Tarjeta métrica 1: Estudiantes en seguimiento o asignaturas inscritas | **CUMPLE PARCIALMENTE** | **NO CUMPLE** | **ALTA** | En Estudiante dice `ESTUDIANTES EN SEGUIMIENTO` en vez de `ASIGNATURAS INSCRITAS`; en Docente muestra `00` fijo (no cambia con el selector); en Autoridad/Admin está hardcodeado en `18` (`app.py:1062-1086`) |
| 29 | Cabecera Común Autenticada | Todos | Tarjeta métrica 2: Tutorías esta semana | CUMPLE | **NO CUMPLE** | **ALTA** | Ficticio/hardcodeado: `1 if mis_mats else 0` en Estudiante, igual a `rojos` del primer curso (`00`) en Docente, y hardcodeado en `3` para Autoridad/Admin (`app.py:1065-1072`) |
| 30 | Cabecera Común Autenticada | Todos | Tarjeta métrica 3: Última actualización de inferencia | CUMPLE | **CUMPLE PARCIALMENTE** | **MEDIA** | Muestra siempre `datetime.date.today()` (`13/11/2026`) en lugar del timestamp real de la última inferencia en BD (`app.py:991, 1099`) |
| 31 | Cabecera Común Autenticada | Todos | Lema pedagógico: *"Estimación, no sentencia..."* | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/03_vista1_panel_seguimiento_arriba.png` |
| 32 | **Vista 1: Panel de Seguimiento** | Estudiante | Ausencia de selector global de asignatura (solo ve sus cursos) | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/04_vista1_panel_seguimiento_abajo.png` |
| 33 | Vista 1: Panel de Seguimiento | Docente / Autoridad / Admin | Selector de asignatura disponible | CUMPLE | CUMPLE | — | `evidencias/02_docente/02_vista1_panel_curso_eda.png` |
| 34 | Vista 1: Panel de Seguimiento | Todos | Tarjetas de riesgo: Riesgo Alto (rojo), Alerta Preventiva (amarillo), Riesgo Bajo (verde) | CUMPLE | CUMPLE | — | Colores, etiquetas, conteos y actualización al cambiar filtro verificados (`02_docente/02_vista1_panel_curso_eda.png`) |
| 35 | Vista 1: Panel de Seguimiento | Estudiante | Tabla/lista de información del Estudiante (Asignatura, Docente, Sección, Estado de riesgo) | CUMPLE | CUMPLE | — | Muestra `Sec. A · 2026-B`, `ESTRUCTURAS DE DATOS Y ALGORITMOS (Prof. DOCENTE PRINCIPAL 1)` y badge `ALTO` |
| 36 | Vista 1: Panel de Seguimiento | Docente | Tabla/lista de información del Docente (Estudiantes, ID anonimizado, Sección, Estado de riesgo) | **CUMPLE PARCIALMENTE** | CUMPLE | **BAJA** | Sin separación entre CUI hash y nombre: se lee pegado `CUI E7BB88B1B2BDD47FEstudiante (A)` (`02_docente/02_vista1_panel_curso_eda.png`) |
| 37 | Vista 1: Panel de Seguimiento | Autoridad | Tabla/lista en Panel de Seguimiento para Autoridad | CUMPLE PARCIALMENTE | **NO CUMPLE** | **CRÍTICA** | Expone registros individuales (`CUI E7BB88B1B2BDD47F`) al rol `AUTORIDAD`, contradiciendo el aislamiento de solo métricas agregadas (`app.py:1187`) |
| 38 | Vista 1: Panel de Seguimiento | Admin | Tabla/lista en Panel de Seguimiento para Administrador | **NO CUMPLE** | **NO CUMPLE** | **CRÍTICA** | Lanza excepción no capturada `AuthorizationError` en pantalla (`app.py:1187`, `04_administrador/02_vista1_crash_authorization_error.png`) |
| 39 | Vista 1: Panel de Seguimiento | Todos | Acción: Botón `Programar tutoría` | **CUMPLE PARCIALMENTE** | **NO CUMPLE** | **ALTA** | Botón sin fondo granate y acción simulada: solo imprime `st.success(...)` sin guardar en BD ni enviar mensaje al bus (`app.py:1214-1215`) |
| 40 | Vista 1: Panel de Seguimiento | Todos | Acción: Botón `Ver explicación` | CUMPLE | **NO CUMPLE** | **ALTA** | No navega a la vista XAI; solo muestra un `st.info` pasivo. Para `AUTORIDAD` sugiere abrir una pestaña que no existe en su menú (`03_autoridad/03_vista1_callejon_sin_salida_ver_explicacion.png`) |
| 41 | **Vista 2: Explicabilidad XAI - SHAP** | Estudiante | Selector de asignatura para Estudiante | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/08_vista2_explicabilidad_xai_barras_shap.png` |
| 42 | Vista 2: Explicabilidad XAI - SHAP | Docente | Selector de asignatura y estudiante anonimizado para Docente | **NO CUMPLE** | **NO CUMPLE** | **ALTA** | No existe ningún selector para el Docente; hardcodea `mat_id_act = 1` y `cui_tag = "CUI 7f3a...c91"` (`app.py:1241-1243`, `02_docente/03_vista2_explicabilidad_sin_selector.png`) |
| 43 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Diagnóstico: Identificador criptográfico | CUMPLE | **CUMPLE PARCIALMENTE** | **ALTA** | En Estudiante muestra su hash real (`CUI E7BB...47F`); en Docente muestra un string ficticio hardcodeado (`CUI 7f3a...c91`) que ni siquiera coincide con el hash del alumno demo |
| 44 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Diagnóstico: Medidor circular SVG y porcentaje exacto (`78%`) | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/08_vista2_explicabilidad_xai_barras_shap.png` |
| 45 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Diagnóstico: Estado del semáforo (`RIESGO ALTO`) y Semestre (`2026-B · EPIS`) | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/08_vista2_explicabilidad_xai_barras_shap.png` |
| 46 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Diagnóstico: Checkpoint activo (`CP0`, `CP1`, `CP2` o `CP3`) | **NO CUMPLE** | **NO CUMPLE** | **MEDIA** | Aunque `pred_rec` contiene `"checkpoint": "CP1"`, no se renderiza en ningún lugar de la tarjeta de diagnóstico (`app.py:1266-1285`) |
| 47 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Diagnóstico: Botón `Programar tutoría` | CUMPLE | **NO CUMPLE** | **ALTA** | Solo muestra un `st.success("Tutoría programada en la agenda del docente.")` estático sin persistencia (`app.py:1286-1287`) |
| 48 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Explicabilidad: Barras de contribución SHAP y valores cuantitativos reales | **CUMPLE PARCIALMENTE** | **NO CUMPLE** | **CRÍTICA** | Renderiza `f["value"]` (nota/valor bruto: `+9.00`, `+8.00`, `+11.50`, `+6.00`) en lugar de `f["impact"]` (valor SHAP: `+0.28`, `+0.24`, `+0.12`, `-0.05`) y calcula mal el ancho de barra (`app.py:1295-1301`) |
| 49 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Explicabilidad: Factores de riesgo en granate (`+`) y protectores en azul (`-`) | **NO CUMPLE** | **NO CUMPLE** | **CRÍTICA** | La condición `es_riesgo = f.get("direction") == "Riesgo" or val_raw > 0` evalúa `6.0 > 0` como `True`, pintando el factor protector (`Carga de cursos matriculados`, impacto `-0.05`) en granate con signo `+6.00` (`01_estudiante/08_vista2_explicabilidad_xai_barras_shap.png`) |
| 50 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Explicabilidad: Leyenda visual (`■ Aumenta el riesgo` / `■ Lo reduce`) | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/08_vista2_explicabilidad_xai_barras_shap.png` |
| 51 | Vista 2: Explicabilidad XAI - SHAP | Estudiante / Docente | Recomendaciones: Caja de sugerencias pedagógicas coherente con factores | CUMPLE | CUMPLE | — | `evidencias/02_docente/03_vista2_explicabilidad_sin_selector.png` |
| 52 | **Vista 3: Trazabilidad Multiagente FIPA-ACL** | Todos | Diagrama de 4 agentes (Datos, Predictor, Explicador, Tutor) y flujo | **CUMPLE PARCIALMENTE** | CUMPLE | **BAJA** | Con el sidebar expandido o en pantallas medianas se parte en 2 filas (2x2) y desaparece la línea dorada conectora `.stepped-line` (`01_estudiante/09_vista3_trazabilidad_fipa_acl.png`) |
| 53 | Vista 3: Trazabilidad Multiagente FIPA-ACL | Todos | Terminal de mensajes: Fondo granate oscuro y tipografía `JetBrains Mono` | **CUMPLE PARCIALMENTE** | CUMPLE | **MEDIA** | Solo la barra de título `.fipa-log-header` es granate oscuro; el cuerpo `.fipa-log-body` tiene fondo blanco `#FFFFFF` (`app.py:720-730`, `01_estudiante/09_vista3_trazabilidad_fipa_acl.png`) |
| 54 | Vista 3: Trazabilidad Multiagente FIPA-ACL | Todos | Terminal: Marca temporal, performativas, emisor, receptor, mensaje y orden cronológico de trazas reales del bus | **CUMPLE PARCIALMENTE** | **NO CUMPLE** | **ALTA** | `MessageBus.send` nunca llama a `log_bus_message()` en SQLite; la tabla `mensajes_bus` está vacía y la vista muestra siempre 4 líneas estáticas decorativas de fallback (`app.py:1377-1383`). Además, si hubiera filas en BD, el bucle `app.py:1386-1391` omite el contenido del mensaje |
| 55 | Vista 3: Trazabilidad Multiagente FIPA-ACL | Todos | Aislamiento por rol y ausencia de CUI/nombres en texto claro | CUMPLE | CUMPLE | — | `get_bus_messages_for_student` filtra por `cui_hash` y no expone CUI ni nombres en claro (`src/database/db.py:713-728`) |
| 56 | **Vista 4: Seguimiento y Plan de Tutoría** | Estudiante / Docente | Gráfico longitudinal: Evolución `CP0 → CP1 → CP2 → CP3`, eje temporal y probabilidad | **CUMPLE PARCIALMENTE** | **CUMPLE PARCIALMENTE** | **MEDIA** | Como solo hay 1 predicción en BD (`len(historial) < 2`), cae en un fallback estático con etiquetas `["Sem 1", "Sem 8", "Sem 16"]` y valores `[22.0, 48.0, 78.0]` en vez de checkpoints reales (`app.py:1436-1441`, `02_docente/05_vista4_seguimiento_y_plan_tutoria.png`) |
| 57 | Vista 4: Seguimiento y Plan de Tutoría | Estudiante / Docente | Gráfico longitudinal: Umbral preventivo y umbral crítico configurados según el modelo | CUMPLE | **CUMPLE PARCIALMENTE** | **MEDIA** | Dibuja líneas discontinuas fijas en `34.0%` (etiquetada como Preventivo, cuando `0.340` es el umbral **Crítico/Rojo** de `CP1`) y `75.0%` (Crítico), confundiendo el umbral preventivo real de CP1 (`0.75 * 0.340 = 25.5%`) con el crítico (`app.py:1451-1452` vs `academic_service.py:23-30`) |
| 58 | Vista 4: Seguimiento y Plan de Tutoría | Estudiante / Docente | Gráfico longitudinal: Puntos intermedios, punto actual destacado y tendencia (`al alza`, `a la baja`, `estable`) | CUMPLE | **CUMPLE PARCIALMENTE** | **MEDIA** | El cálculo `tendencia_txt = "al alza" if riesgos[-1] > riesgos[0] else "estable"` jamás evalúa `"a la baja"` cuando el riesgo disminuye (`app.py:1471`) |
| 59 | Vista 4: Seguimiento y Plan de Tutoría | Estudiante / Docente | Bitácora: Conversación inicial, Derivación, Reevaluación, casillas, fechas y estado | CUMPLE | **NO CUMPLE** | **ALTA** | Es HTML 100 % estático (`<div class="action-box">`) con fechas hardcodeadas (`12/09/2026`, `15/10/2026`, `02/11/2026`); las casillas no son interactivas ni guardan estado en BD (`app.py:1480-1497`) |
| 60 | Vista 4: Seguimiento y Plan de Tutoría | Estudiante / Docente | Acción: Botón `Registrar tutoría` (persistencia y confirmación) | **CUMPLE PARCIALMENTE** | **NO CUMPLE** | **ALTA** | Botón sin fondo granate y sin persistencia: solo muestra `st.success("Tutoría guardada en la bitácora docente y registrada en el bus.")` sin escribir en BD ni en el bus (`app.py:1502-1503`) |
| 61 | Vista 4: Seguimiento y Plan de Tutoría | Estudiante / Docente | Acción: Botón `Exportar informe PDF` (descarga, anonimización, resumen SHAP y recomendaciones reales) | CUMPLE | **CUMPLE PARCIALMENTE** | **ALTA** | Genera y descarga un PDF válido y anonimizado (`Ficha_Intervencion_SATA_E7BB88B1.pdf`), pero `app.py:1505-1519` le pasa factores SHAP, meta (`13.5`), promedio (`8.4`), umbral (`34.0`) y recomendaciones **hardcodeadas** en vez de los datos reales del alumno |
| 62 | **Vista Exclusiva Estudiante: Inscribir Asignatura** | Estudiante | Catálogo EPIS, selección de docente, sección y condición regular/repitente | CUMPLE | CUMPLE | — | `evidencias/01_estudiante/13_vista5_inscribir_asignatura.png` |
| 63 | Vista Exclusiva Estudiante: Inscribir Asignatura | Estudiante | Ponderaciones `EC1`, `EP1`, `EC2`, `EP2`, `EC3`, `EP3` y validación de suma del 100 % | CUMPLE | CUMPLE | — | Bloquea el botón y muestra `"Las ponderaciones deben sumar exactamente 100%."` (`01_estudiante/14_vista5_validacion_suma_100pct.png`) |
| 64 | Vista Exclusiva Estudiante: Inscribir Asignatura | Estudiante | Activación de inferencia CP0 al inscribir asignatura | CUMPLE | **CUMPLE PARCIALMENTE** | **MEDIA** | Inserta en `matriculas`, pero no dispara a `CoordinatorAgent` para generar la predicción inicial `CP0` (`app.py:1562-1566`) |
| 65 | **Vista Exclusiva Estudiante: Perfil Basal** | Estudiante | Campos IRA previo (`0–20`), Cursos reprobados (`0–20`), Créditos inscritos (`1–30`), Semestres desde ingreso (`1–16`) | CUMPLE | CUMPLE | — | Rangos, pasos, persistencia en `perfil_semestre` y validación verificados (`01_estudiante/15_vista6_perfil_basal.png`) |
| 66 | **Vista Exclusiva Docente: Carga Masiva de Actas** | Docente | Descarga de plantilla CSV (`plantilla_acta_sata.csv`) | CUMPLE | CUMPLE | — | Descarga verificada (`644 bytes`, 4 filas de ejemplo con cabeceras completas) |
| 67 | Vista Exclusiva Docente: Carga Masiva de Actas | Docente | Cargador CSV/XLSX drag-and-drop y botón de procesamiento | **CUMPLE PARCIALMENTE** | CUMPLE | **MEDIA** | Funciona para `.csv` y `.xlsx`, pero el botón primario carece de fondo granate (`02_docente/07_vista5_carga_masiva_procesada.png`) |
| 68 | Vista Exclusiva Docente: Carga Masiva de Actas | Docente | Validación de filas, reporte de observaciones y ejecución con Coordinador Multiagente | CUMPLE | CUMPLE | — | Valida rangos, suma de pesos 100 % e inyección CSV (`=`, `+`, `@`, `|`), y ejecuta `coordinator.analyze_student_risk` |
| 69 | Vista Exclusiva Docente: Carga Masiva de Actas | Docente | Persistencia real de las actas importadas en la base de datos | CUMPLE | **NO CUMPLE** | **CRÍTICA** | `validar_y_procesar_acta_masiva` procesa todo en memoria y devuelve un DataFrame visual, pero **no guarda nada en SQLite** (`matriculas`, `notas`, `predicciones`, `mensajes_bus` ni `metricas_tecnicas` se actualizan) |
| 70 | **Vista Exclusiva Autoridad: Métricas Institucionales** | Autoridad | Indicadores superiores y tabla agregada (Total estudiantes, Asignaturas, Críticos, Preventivos, Regulares, Tasa de riesgo) | **CUMPLE PARCIALMENTE** | CUMPLE | **BAJA** | Calcula datos reales agregados sin exponer identidades, pero deja la columna `semestre` en minúscula sin renombrar (`03_autoridad/04_vista2_metricas_institucionales_arriba.png`) |
| 71 | **Vista Exclusiva Administrador: Monitor Técnico OBJ5** | Admin | Latencia media, Latencia P95, Consumo RAM y Overhead del bus asíncrono | **NO CUMPLE** | **NO CUMPLE** | **CRÍTICA** | La pantalla explota con `KeyError: 'latencia_inf_media_ms'` en `app.py:1653` porque `metricas_tecnicas` está vacía y `get_technical_metrics_summary()` retorna claves con nombres distintos cuando no hay filas (`04_administrador/03_vista2_crash_monitor_tecnico_keyerror.png`) |
| 72 | **Vista Exclusiva Administrador: Encuestas SUS/TAM** | Admin | Estadísticas de resumen SUS y TAM | CUMPLE | CUMPLE | — | Muestra `0.0 / 100` y `0.0 / 5.0` con conteo de evaluadores (`04_administrador/05_vista4_encuestas_sus_tam_arriba.png`) |
| 73 | Vista Exclusiva Administrador: Encuestas SUS/TAM | Admin | Formulario de 10 ítems Likert SUS, cálculo normativo (`* 2.5`) y persistencia | CUMPLE | **CUMPLE PARCIALMENTE** | **ALTA** | El cálculo SUS es exacto, pero guarda todas las respuestas con el rol hardcodeado `"DOCENTE_EVAL"` (`app.py:1686`) y **carece por completo de formulario para la encuesta TAM** (`04_administrador/06_vista4_encuestas_sus_abajo_sin_tam.png`) |
| 74 | **Transversal: Visual y Responsive** | Todos | Paleta institucional (`#7A1C20`, `#C59B27`, `#1E4E79`) y tipografía (`Plus Jakarta Sans`, `JetBrains Mono`) | **CUMPLE PARCIALMENTE** | CUMPLE | **MEDIA** | Paleta y fuentes cargan desde Google Fonts, pero reglas CSS demasiado agresivas rompen los botones primarios, el contraste del sidebar y la fuente de iconos Material Symbols |
| 75 | Transversal: Visual y Responsive | Todos | Adaptación en Escritorio (`1280x800`) y Móvil (`375x812`) sin superposiciones ni cortes | **NO CUMPLE** | CUMPLE | **MEDIA** | El botón flotante `>>` se superpone a los textos superiores en todas las pantallas autenticadas; el sidebar abierto muestra `keyboard_double_` cortado |
| 76 | **Transversal: Seguridad y Privacidad** | Todos | Hashing irreversible de CUI con `HMAC-SHA256` y sal secreta local (`.salt_secret`) | CUMPLE | CUMPLE | — | Implementado correctamente en `src/security/crypto.py:31-40` |
| 77 | Transversal: Seguridad y Privacidad | Todos | Hashing de contraseñas con `PBKDF2-HMAC-SHA256` (100,000 iteraciones y sal aleatoria) + comparación en tiempo constante (`hmac.compare_digest`) | CUMPLE | CUMPLE | — | Implementado correctamente en `src/security/crypto.py:43-68` |
| 78 | Transversal: Seguridad y Privacidad | Estudiante | Aislamiento estricto de datos entre estudiantes (`validate_student_access`, `validate_matricula_ownership`) | CUMPLE | CUMPLE | — | Verificado en `src/security/access_control.py` y en las vistas del Estudiante |
| 79 | Transversal: Seguridad y Privacidad | Todos | Consentimiento informado (`comparte_con_tutor` / Opt-in) accesible desde la interfaz del estudiante | **NO CUMPLE** | **NO CUMPLE** | **ALTA** | Aunque existen `get_student_info` y `update_student_consent` en `src/database/db.py:401-420`, no están importadas ni expuestas en ninguna pantalla de `app.py`; un estudiante nuevo se registra con `comparte_con_tutor = 0` sin opción en UI para activarlo |
| 80 | Transversal: Reglas de Negocio | Estudiante / Docente | Registro intra-semestral de calificaciones parciales (`EC1..EP3`) en UI | **NO CUMPLE** | **NO CUMPLE** | **ALTA** | Aunque existen `save_grade` y `get_grades_for_enrollment` en `src/database/db.py:509-572`, no están importadas ni conectadas en `app.py` |
| 81 | Transversal: Reglas de Negocio | Estudiante / Docente | Simulador normativo del Examen Sustitutorio (`calcular_simulacion_sustitutorio`) en UI | **NO CUMPLE** | **NO CUMPLE** | **ALTA** | Aunque la función existe en `src/services/academic_service.py:59-145` y se anuncia en la portada de Login (*"Sustitutorio reemplaza únicamente el examen parcial más bajo"*), no está importada ni visible en ninguna pantalla de `app.py` |
| 82 | Transversal: Seguridad y Sesión | Todos | Cierre de sesión con limpieza completa de `st.session_state` y retorno a Pantalla 0 | CUMPLE | CUMPLE | — | Verificado en los 4 roles (`app.py:1051-1053`) |

---

## C. EVIDENCIAS VISUALES

Todas las capturas de pantalla fueron tomadas directamente del navegador en `http://localhost:8501` en resoluciones de **Escritorio (`1280x800`)** y **Móvil (`375x812`)**, y se encuentran organizadas por rol y pantalla dentro de `auditoria_visual_funcional/evidencias/`:

### 1. Pantalla 0: Acceso / Login (`auditoria_visual_funcional/evidencias/00_login/`)
1. `01_login_escritorio_arriba.png` — Banner institucional UNSA, columna de Identidad Institucional y Ética, y pestaña Iniciar Sesión (modo Estudiante). Se observa el botón primario `Ingresar al Portal del Estudiante` con fondo blanco/transparente en vez de granate.
2. `02_login_escritorio_abajo.png` — Pilares de seguridad (PBKDF2, HMAC-SHA256, XAI SHAP, Sustitutorio) y los 4 botones de Acceso Rápido de Evaluación.
3. `03_login_validacion_vacio.png` — Mensaje de validación en rojo al intentar ingresar con campos vacíos (`"Por favor complete su CUI y contraseña."`).
4. `04_login_modo_personal.png` — Alternancia del radio button a `Docente / Autoridad / Administrador`.
5. `05_pestana_registro_estudiante.png` — Pestaña `Registro de Estudiante` con campos de CUI oficial y confirmación de contraseña.
6. `06_registro_validacion_error.png` — Validación de longitud mínima en registro de estudiante.
7. `07_login_movil_arriba.png` — Adaptación responsive en móvil (`375x812`) de la cabecera y tarjeta ética.
8. `08_login_movil_abajo.png` — Adaptación responsive en móvil (`375x812`) de los botones de acceso rápido y formulario de autenticación.

### 2. Rol 1: Estudiante Demo (`auditoria_visual_funcional/evidencias/01_estudiante/`)
9. `01_cabecera_y_sidebar_abierto.png` — Sesión de Estudiante con sidebar desplegado: evidencia la ligadura rota **`keyboard_double_`**, el texto de navegación en negro (`#0F172A`) sobre fondo granate (`#7A1720`) y el botón `Cerrar Sesión` con texto granate casi invisible sobre fondo granate oscuro.
10. `02_sidebar_colapsado.png` — Prueba de colapso del sidebar lateral y aparición del botón flotante `>>`.
11. `03_vista1_panel_seguimiento_arriba.png` — Cabecera común autenticada del Estudiante: saludo anonimizado (`Hola, E7BB88B1B2BDD47F`), las 3 tarjetas de métricas (`ESTUDIANTES EN SEGUIMIENTO: 01`, `TUTORÍAS ESTA SEMANA: 01`, `ÚLTIMA ACTUALIZACIÓN: 13/11/2026`) y lema pedagógico.
12. `04_vista1_panel_seguimiento_abajo.png` — Vista 1 (`Panel de seguimiento`) del Estudiante: ausencia de selector global de curso, 3 tarjetas de semáforo (`01` Alto, `00` Preventiva, `00` Bajo), fila de matrícula y botones inferiores.
13. `05_vista1_accion_programar_tutoria.png` — Clic en `Programar tutoría` mostrando mensaje estático `st.success`.
14. `06_vista1_accion_ver_explicacion.png` — Clic en `Ver explicación` mostrando mensaje pasivo `st.info` sin redirección automática.
15. `07_vista2_explicabilidad_xai_arriba.png` — Vista 2 (`Detalle con explicabilidad`) superior.
16. `08_vista2_explicabilidad_xai_barras_shap.png` — Vista 2 inferior: medidor circular SVG (`78%`), omisión de la etiqueta de Checkpoint (`CP1`), y bug crítico en barras SHAP donde se grafican las notas/valores brutos (`+9.00`, `+8.00`, `+11.50`, `+6.00`) todos en granate positivo en lugar de los impactos SHAP (`+0.28`, `+0.24`, `+0.12`, `-0.05`).
17. `09_vista3_trazabilidad_fipa_acl.png` — Vista 3 (`Trazabilidad multiagente`): nodos dispuestos en 2x2 sin línea conectora, cuerpo de terminal con fondo blanco (`#FFFFFF`), mensajes de fallback estáticos y botón `>>` superpuesto al título `"Cómo se calculó esta alerta"`.
18. `10_vista4_plan_tutoria_arriba.png` — Vista 4 (`Seguimiento y plan de tutoría`) superior.
19. `11_vista4_plan_tutoria_bitacora.png` — Vista 4 inferior: bitácora estática con casillas HTML no interactivas y botón `>>` tapando el título `"Evolución y plan de tutoría"`.
20. `12_vista4_accion_registrar_tutoria.png` — Clic en `Registrar tutoría` (confirmación visual sin persistencia en BD).
21. `13_vista5_inscribir_asignatura.png` — Vista exclusiva `Inscribir Asignatura`: selectores y ponderaciones del sílabo (`EC1..EP3`).
22. `14_vista5_validacion_suma_100pct.png` — Validación funcional activa cuando las ponderaciones suman 105 % (`!= 100%`).
23. `15_vista6_perfil_basal.png` — Vista exclusiva `Perfil Basal` con los 4 indicadores históricos del estudiante.
24. `16_movil_panel_seguimiento.png` — Vista 1 del Estudiante en viewport móvil (`375x812`).
25. `17_movil_explicabilidad_xai.png` — Vista 2 del Estudiante en viewport móvil (`375x812`).

### 3. Rol 2: Docente / Tutor (`auditoria_visual_funcional/evidencias/02_docente/`)
26. `01_cabecera_y_panel_inicial.png` — Sesión de `docente_demo` con sub-cabecera en `00` y curso por defecto (`ANALISIS Y DISENO DE ALGORITMOS`).
27. `02_vista1_panel_curso_eda.png` — Cambio de filtro a `ESTRUCTURAS DE DATOS Y ALGORITMOS`: las tarjetas de riesgo cambian a `01`, pero la fila inferior muestra el texto colisionado `CUI E7BB88B1B2BDD47FEstudiante (A)` sin espacio intermedio.
28. `03_vista2_explicabilidad_sin_selector.png` — Vista 2 del Docente: ausencia total de selector de asignatura o estudiante, mostrando el identificador hardcodeado `CUI 7f3a...c91`.
29. `04_vista3_trazabilidad_fipa_acl.png` — Vista 3 del Docente con mensajes de fallback.
30. `05_vista4_seguimiento_y_plan_tutoria.png` — Vista 4 del Docente: gráfico longitudinal con eje X estático (`Sem 1`, `Sem 8`, `Sem 16`), umbrales discontinuos y bitácora estática.
31. `06_vista5_carga_masiva_inicial.png` — Vista exclusiva `Carga Masiva de Actas`: botón de descarga de plantilla CSV y cargador drag-and-drop.
32. `07_vista5_carga_masiva_procesada.png` — Procesamiento de `plantilla_acta_sata.csv` con las 4 filas evaluadas por el Coordinador Multiagente.
33. `08_movil_carga_masiva.png` — Vista de Carga Masiva en móvil (`375x812`).
34. `09_movil_panel_seguimiento.png` — Panel de seguimiento del Docente en móvil (`375x812`).

### 4. Rol 3: Autoridad / Comité (`auditoria_visual_funcional/evidencias/03_autoridad/`)
35. `01_cabecera_y_panel_inicial.png` — Sesión de `tutor_epis` (`AUTORIDAD`) mostrando métricas hardcodeadas en sub-cabecera (`18` y `03`).
36. `02_vista1_panel_curso_eda.png` — En `Panel de seguimiento`, el rol `AUTORIDAD` visualiza el registro individual `CUI E7BB88B1B2BDD47FEstudiante (A)`.
37. `03_vista1_callejon_sin_salida_ver_explicacion.png` — Al pulsar `Ver explicación`, el sistema indica abrir `'Detalle con explicabilidad'` en el menú lateral, opción que no existe para `AUTORIDAD`.
38. `04_vista2_metricas_institucionales_arriba.png` — Vista exclusiva `Métricas Institucionales`: indicadores globales (`9` asignaturas, `1` estudiante evaluado, `1` alerta roja = `100.0%`).
39. `05_vista2_metricas_institucionales_tabla.png` — Tabla agregada por asignatura (se aprecia la columna `semestre` sin renombrar).
40. `06_vista3_trazabilidad_fipa_acl.png` — Vista 3 para `AUTORIDAD`.
41. `07_movil_metricas_institucionales.png` — Vista de `Métricas Institucionales` en móvil (`375x812`).

### 5. Rol 4: Administrador (`auditoria_visual_funcional/evidencias/04_administrador/`)
42. `01_cabecera_y_sidebar_admin.png` — Sesión de `admin` (`ADMIN`) con sidebar abierto.
43. `02_vista1_crash_authorization_error.png` — **Evidencia de Crash Crítico #1:** `src.security.access_control.AuthorizationError: Principio de Privacidad: El Administrador no tiene acceso a notas individuales de estudiantes` en `app.py:1187` al entrar a la vista por defecto `Panel de seguimiento`.
44. `03_vista2_crash_monitor_tecnico_keyerror.png` — **Evidencia de Crash Crítico #2:** `KeyError: 'latencia_inf_media_ms'` en `app.py:1653` al abrir `Monitor Técnico OBJ5`.
45. `04_vista3_trazabilidad_fipa_acl.png` — Vista 3 (`Trazabilidad multiagente`) para `ADMIN`.
46. `05_vista4_encuestas_sus_tam_arriba.png` — Vista exclusiva `Encuestas SUS / TAM` superior: métricas de resumen SUS y TAM e inicio del cuestionario SUS.
47. `06_vista4_encuestas_sus_abajo_sin_tam.png` — Parte final del formulario en `Encuestas SUS / TAM`: termina en el ítem 10 de SUS (`Guardar Evaluación SUS`) sin incluir ningún formulario para TAM.
48. `07_movil_monitor_tecnico_keyerror.png` — Crash `KeyError` reproducido en móvil (`375x812`).
49. `08_movil_encuestas_sus.png` — Formulario de encuestas SUS en móvil (`375x812`).

---

## D. PROBLEMAS ENCONTRADOS (DIAGNÓSTICO TÉCNICO Y CAUSA RAÍZ)

### PROBLEMA 1: Crash por `AuthorizationError` no capturado al iniciar sesión como Administrador
- **Descripción:** Al autenticarse con el rol `ADMIN`, la primera vista seleccionada por defecto es `"Panel de seguimiento"`, la cual invoca `get_course_students_table(curso_sel, "2026-B", current_user=usuario)` y aborta la ejecución con una excepción no controlada en pantalla.
- **Ubicación:** Vista 1 (`Panel de seguimiento`) — Rol `ADMIN`.
- **Comportamiento esperado:** El Administrador no debe ver un traceback en pantalla; o bien `"Panel de seguimiento"` no debe listar registros individuales para `ADMIN` (mostrando únicamente el resumen agregado del curso o un aviso controlado), o bien la vista inicial del Administrador debe ser `"Monitor Técnico OBJ5"`.
- **Comportamiento observado:** Aparece un cuadro rojo de excepción de Streamlit con el traceback completo (`AuthorizationError: Principio de Privacidad: El Administrador no tiene acceso a notas individuales de estudiantes.`).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1034-L1040) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1186-L1190), en conjunto con [db.py](file:///d:/TESIS%20FINAL/src/database/db.py#L677-L682).
- **Causa probable:** En `app.py:1186`, la rama `else:` agrupa a `DOCENTE`, `AUTORIDAD` y `ADMIN` para llamar a `get_course_students_table()`, pero `db.py:680` lanza explícitamente `AuthorizationError` cuando `current_user.get("role") == "ADMIN"`.
- **Severidad:** **CRÍTICA**
- **Recomendación de solución:** En `app.py:1186`, restringir la llamada a `get_course_students_table()` exclusivamente a `rol == "DOCENTE"` (o capturar `AuthorizationError` mostrando un mensaje informativo institucional), o retirar `"Panel de seguimiento"` de `menu_items` para `ADMIN`.

### PROBLEMA 2: Crash por `KeyError: 'latencia_inf_media_ms'` en el Monitor Técnico OBJ5
- **Descripción:** Al ingresar a la vista exclusiva `"Monitor Técnico OBJ5"` del Administrador, la pantalla se rompe por completo con `KeyError: 'latencia_inf_media_ms'`.
- **Ubicación:** Vista `"Monitor Técnico OBJ5"` — Rol `ADMIN`.
- **Comportamiento esperado:** Mostrar las 4 tarjetas métricas (`Latencia Media Inferencia`, `Latencia P95 Inferencia`, `Uso Promedio RAM`, `Overhead Bus Asíncrono`) con sus unidades y valores reales o `0.0 ms` cuando aún no existan muestras en la tabla `metricas_tecnicas`.
- **Comportamiento observado:** Excepción `KeyError: 'latencia_inf_media_ms'` que impide renderizar toda la vista.
- **Archivo relacionado:** [db.py](file:///d:/TESIS%20FINAL/src/database/db.py#L770-L800) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1651-L1657).
- **Causa probable:** En `db.py:779-786`, cuando la tabla `metricas_tecnicas` está vacía (`if not rows:`), la función `get_technical_metrics_summary()` retorna un diccionario con claves **inconsistentes** (`"latencia_inf_media"`, `"ram_media"`, `"overhead_media"` y omite `"latencia_inf_p95_ms"`), mientras que cuando hay filas (`db.py:793-800`) retorna `"latencia_inf_media_ms"`, `"latencia_inf_p95_ms"`, `"ram_media_mb"`, `"overhead_media_ms"`. Además, ninguna operación en `app.py` ni en `CoordinatorAgent` llama nunca a `log_technical_metrics()`, por lo que `metricas_tecnicas` permanece siempre vacía.
- **Severidad:** **CRÍTICA**
- **Recomendación de solución:** Unificar las claves del diccionario de retorno en `db.py:779-786` (`"latencia_inf_media_ms"`, `"latencia_inf_p95_ms"`, `"latencia_xai_media_ms"`, `"ram_media_mb"`, `"overhead_media_ms"`) e instrumentar `CoordinatorAgent.analyze_student_risk()` (o `seed_initial_data()`) para registrar mediciones reales mediante `log_technical_metrics()`.

### PROBLEMA 3: Barras de Explicabilidad XAI grafican el valor bruto de la variable en lugar del valor SHAP e invierten factores protectores
- **Descripción:** En la Vista 2 (`Detalle con explicabilidad`), las barras horizontales no muestran el impacto SHAP (`f["impact"]`), sino el valor bruto de la variable (`f["value"]`: nota `9.00`, nota `8.00`, IRA `11.50`, créditos `6.00`) precedido de un signo `+`. Peor aún, los factores protectores con valor bruto positivo (como `Carga de cursos matriculados = 6`, cuyo impacto SHAP real es `-0.05` y dirección `"Protección"`) se colorean en **granate de riesgo (`#7A1C20`)** con signo `+6.00` en lugar de **azul protector (`#1E4E79`)** con `-0.05`.
- **Ubicación:** Vista 2 (`Detalle con explicabilidad`) — Roles `ESTUDIANTE` y `DOCENTE`.
- **Comportamiento esperado:** Cada barra debe mostrar el valor cuantitativo de contribución SHAP (`+0.28`, `+0.24`, `+0.12`, `-0.05`), pintar en granate los factores que aumentan el riesgo (`impact > 0`) y en azul los factores protectores (`impact < 0`), con longitudes de barra proporcionales al impacto SHAP.
- **Comportamiento observado:** Se muestran `+9.00`, `+8.00`, `+11.50` y `+6.00`, todas en color granate y con anchos diminutos (6 % a 11 %).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1292-L1313), [db.py](file:///d:/TESIS%20FINAL/src/database/db.py#L318-L323) y [xai_agent.py](file:///d:/TESIS%20FINAL/src/agents/xai_agent.py#L94-L102).
- **Causa probable:** Tanto `xai_agent.py:96-101` como `db.py:318-323` guardan la nota/valor observado en `"value"` y la contribución SHAP en `"impact"`. Sin embargo, `app.py:1295-1296` lee `val_raw = float(f.get("value", 0.0))` en vez de `float(f.get("impact", f.get("value", 0.0)))`, y evalúa `es_riesgo = f.get("direction") == "Riesgo" or val_raw > 0`. Como `val_raw` (`6.0`) es `> 0`, fuerza `es_riesgo = True` aunque `"direction"` sea `"Protección"` e `"impact"` sea `-0.05`.
- **Severidad:** **CRÍTICA**
- **Recomendación de solución:** En `app.py:1295`, extraer `shap_val = float(f.get("impact", f.get("value", 0.0)))`, determinar `es_riesgo = (shap_val >= 0)` (o `f.get("direction") == "Riesgo"`), mostrar opcionalmente el valor observado junto al nombre (`f"{f_nombre} ({f.get('value')})"`) y graficar `shap_val` con su signo real (`+` / `-`) y color (`--granate` vs `--azul-factor`).

### PROBLEMA 4: Procesamiento de Carga Masiva de Actas no persiste datos en SQLite
- **Descripción:** En la vista exclusiva del Docente (`Carga Masiva de Actas`), al subir un archivo CSV/XLSX y pulsar `"Validar y Procesar Acta con Sistema Multiagente"`, el sistema ejecuta el pipeline en memoria y muestra la tabla de resultados en pantalla, pero no inserta ni actualiza ningún registro en la base de datos SQLite (`sata_unsa.db`).
- **Ubicación:** Vista `"Carga Masiva de Actas"` — Rol `DOCENTE`.
- **Comportamiento esperado:** Las filas válidas procesadas deben persistirse (anonimizando el CUI con `hash_cui`) en las tablas `estudiantes`, `matriculas`, `notas`, `predicciones`, `explicaciones`, `mensajes_bus` y `metricas_tecnicas`, de modo que al volver al `"Panel de seguimiento"` o `"Métricas Institucionales"` los estudiantes importados aparezcan reflejados.
- **Comportamiento observado:** Al cambiar al `"Panel de seguimiento"` tras importar 4 estudiantes de `ANALISIS Y DISENO DE ALGORITMOS`, el curso sigue mostrando `00` estudiantes.
- **Archivo relacionado:** [academic_service.py](file:///d:/TESIS%20FINAL/src/services/academic_service.py#L169-L352) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1609-L1618).
- **Causa probable:** `validar_y_procesar_acta_masiva()` solo invoca `coordinator_agent.analyze_student_risk(payload)` y agrega diccionarios a la lista en memoria `filas_procesadas`, sin invocar `enroll_course()`, `save_grade()` ni `save_prediction_result()`.
- **Severidad:** **CRÍTICA**
- **Recomendación de solución:** Persistir cada fila válida procesada en SQLite dentro de una transacción (creando/actualizando el estudiante con `hash_cui`, su matrícula, sus notas parciales y el resultado de predicción/explicación).

### PROBLEMA 5: Exposición de registros individuales de estudiantes al rol Autoridad en el Panel de Seguimiento
- **Descripción:** La especificación establece que el rol `AUTORIDAD` debe visualizar únicamente información agregada y macro por asignatura sin acceso a identidades individuales. Aunque su vista `"Métricas Institucionales"` cumple esto, el rol `AUTORIDAD` también tiene acceso a `"Panel de seguimiento"`, donde al elegir `"ESTRUCTURAS DE DATOS Y ALGORITMOS"` visualiza la lista individual de estudiantes (`CUI E7BB88B1B2BDD47F`).
- **Ubicación:** Vista 1 (`Panel de seguimiento`) — Rol `AUTORIDAD`.
- **Comportamiento esperado:** El rol `AUTORIDAD` solo debe ver conteos agregados por asignatura y sección, sin listar hashes individuales de estudiantes en `"Panel de seguimiento"`.
- **Comportamiento observado:** `get_course_students_table()` bloquea a `ESTUDIANTE` y `ADMIN`, pero permite a `AUTORIDAD` listar filas individuales.
- **Archivo relacionado:** [db.py](file:///d:/TESIS%20FINAL/src/database/db.py#L670-L682) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1186-L1209).
- **Causa probable:** Falta incluir `AUTORIDAD` en la restricción de privacidad individual o mostrar una vista resumen agregada en `app.py:1186` cuando `rol == "AUTORIDAD"`.
- **Severidad:** **CRÍTICA**
- **Recomendación de solución:** En `app.py:1186`, mostrar la lista individual de estudiantes únicamente cuando `rol == "DOCENTE"`, presentando para `AUTORIDAD` un resumen agregado por sección o redirigiéndolo a `"Métricas Institucionales"`.

### PROBLEMA 6: Ausencia total de selectores de asignatura y estudiante para el Docente en las Vistas 2 y 4
- **Descripción:** En `"Detalle con explicabilidad"` (Vista 2) y `"Seguimiento y plan de tutoría"` (Vista 4), el rol `DOCENTE` no dispone de ningún selector (`st.selectbox`) para elegir la asignatura ni el estudiante anonimizado a consultar.
- **Ubicación:** Vistas 2 y 4 — Rol `DOCENTE`.
- **Comportamiento esperado:** El Docente debe poder seleccionar primero la asignatura y luego el identificador anonimizado del estudiante perteneciente a dicha asignatura.
- **Comportamiento observado:** Ambas vistas tienen hardcodeado `mat_id_act = 1` y `cui_tag = "CUI 7f3a...c91"` (un hash ficticio estático que ni siquiera coincide con el hash real `E7BB88B1B2BDD47F` de la matrícula `id = 1`).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1241-L1243) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1428-L1432).
- **Causa probable:** Implementación incompleta de la rama `else:` (`rol != "ESTUDIANTE"`) en ambas vistas, donde se dejaron valores constantes de maqueta.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Añadir en las Vistas 2 y 4 para `rol == "DOCENTE"` un selector de asignatura seguido de un selector de estudiante alimentado por `get_course_students_table(curso_sel, "2026-B", current_user=usuario)`, actualizando `st.session_state["selected_student_mat"]`.

### PROBLEMA 7: Acciones `Programar tutoría`, `Ver explicación` y `Registrar tutoría` son simulacros sin efecto real
- **Descripción:** Los botones interactivos de acción en las Vistas 1, 2 y 4 no ejecutan lógica de negocio ni navegación:
  1. `Programar tutoría` (Vista 1 y Vista 2) solo muestra un banner `st.success` estático sin guardar registro en la base de datos.
  2. `Ver explicación` (Vista 1) no redirige a la Vista 2; solo muestra un `st.info` pidiendo al usuario cambiar manualmente de pestaña en el menú lateral.
  3. `Registrar tutoría` (Vista 4) solo muestra un `st.success` estático sin persistir acuerdos en la bitácora ni emitir un mensaje en el bus FIPA-ACL.
- **Ubicación:** Vistas 1, 2 y 4 — Todos los roles.
- **Comportamiento esperado:** `Ver explicación` debe cambiar programáticamente la vista activa a `"Detalle con explicabilidad"` para el alumno/curso seleccionado; `Programar tutoría` y `Registrar tutoría` deben persistir el evento en una tabla de tutorías/bitácora en SQLite y registrar el mensaje correspondiente en el bus.
- **Comportamiento observado:** Mensajes efímeros de interfaz que desaparecen al recargar o cambiar de vista.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1213-L1219), [app.py](file:///d:/TESIS%20FINAL/app.py#L1286-L1287) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1501-L1503).
- **Causa probable:** Los botones fueron conectados únicamente a llamadas `st.success()` / `st.info()` de prototipo.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Vincular `nav_sel` a `st.session_state` para permitir navegación directa desde `Ver explicación`, y crear la función de persistencia de sesiones de tutoría en `src/database/db.py`.

### PROBLEMA 8: Callejón sin salida en botón `Ver explicación` para el rol Autoridad
- **Descripción:** Cuando el usuario con rol `AUTORIDAD` hace clic en `"Ver explicación"` dentro de `"Panel de seguimiento"`, aparece el mensaje: *"Abra la pestaña 'Detalle con explicabilidad' en el menú lateral para consultar el desglose SHAP."* Sin embargo, el menú lateral de `AUTORIDAD` solo contiene `["Panel de seguimiento", "Métricas Institucionales", "Trazabilidad multiagente"]`.
- **Ubicación:** Vista 1 (`Panel de seguimiento`) — Rol `AUTORIDAD`.
- **Comportamiento esperado:** No mostrar botones que refieran a vistas inexistentes o no autorizadas para el rol activo.
- **Comportamiento observado:** Instrucción contradictoria hacia una vista inaccesible para el rol.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1028-L1033) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1212-L1219).
- **Causa probable:** Los botones inferiores de Vista 1 se renderizan sin verificar el rol del usuario autenticado.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Ocultar los botones de intervención individual en Vista 1 cuando `rol in ["AUTORIDAD", "ADMIN"]`.

### PROBLEMA 9: Bitácora de tutoría en Vista 4 es HTML estático no interactivo
- **Descripción:** Las 3 filas de compromisos de la bitácora en `"Seguimiento y plan de tutoría"` (`Acción 1: conversación inicial...`, `Acción 2: derivar a reforzamiento...`, `Acción 3: reevaluar el semáforo...`) están escritas como bloques `<div>` estáticos con fechas fijas (`12/09/2026`, `15/10/2026`, `02/11/2026`).
- **Ubicación:** Vista 4 (`Seguimiento y plan de tutoría`) — Roles `ESTUDIANTE` y `DOCENTE`.
- **Comportamiento esperado:** Casillas de verificación reales (`st.checkbox`) editables por el Docente/Tutor, con fechas reales y persistencia del estado de cada compromiso en la base de datos.
- **Comportamiento observado:** Cajas decorativas `<div class="action-box checked">&#10003;</div>` que no responden al clic ni cambian de estado.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1480-L1497).
- **Causa probable:** Maquetación estática copiada del mockup sin respaldo de tabla en SQLite ni widgets interactivos.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Reemplazar los `<div>` estáticos por controles `st.checkbox` (habilitados para `DOCENTE` y de solo lectura para `ESTUDIANTE`) respaldados en SQLite.

### PROBLEMA 10: Exportación de Informe PDF en Vista 4 utiliza datos hardcodeados en lugar de la predicción real
- **Descripción:** Al pulsar `"Exportar informe PDF"` en la Vista 4, `app.py` llama a `generate_intervention_pdf()` pasándole parámetros estáticos hardcodeados en el código (`checkpoint="CP1"`, `umbral_pct=34.0`, `meta_nota_min=13.5`, `promedio_acumulado=8.4`, `top_factors=[{"label": "Asistencia acumulada baja", "value": 0.42, "direction": "Riesgo"}]`, `recommendations=["Plan de tutoría individual y seguimiento en laboratorio de programación."]`) en lugar de consultar `get_latest_prediction(mat_id_act)`. Además, como el factor hardcodeado no incluye la clave `"impact"`, en la tabla del PDF generado la columna `"Impacto en la Probabilidad"` imprime `+0.0000`.
- **Ubicación:** Vista 4 (`Seguimiento y plan de tutoría`) — Roles `ESTUDIANTE` y `DOCENTE`.
- **Comportamiento esperado:** El PDF descargado debe contener el checkpoint, umbral, nota mínima meta, promedio acumulado, factores SHAP (con su impacto real) y recomendaciones reales almacenadas para esa matrícula en la base de datos.
- **Comportamiento observado:** El PDF contiene datos fijos que no coinciden con los factores SHAP ni las recomendaciones mostradas en la Vista 2 para el mismo estudiante.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1505-L1526) y [pdf_generator.py](file:///d:/TESIS%20FINAL/src/reports/pdf_generator.py#L180-L189).
- **Causa probable:** Llamada a `generate_intervention_pdf()` con literales de prueba en vez de extraer los campos de `get_latest_prediction(mat_id_act, current_user=usuario)`.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Consultar `pred_actual = get_latest_prediction(mat_id_act, current_user=usuario)` en `app.py:1504` y pasar sus valores reales (`checkpoint`, `umbral * 100`, `semaforo`, `meta_nota_min`, `promedio_acumulado`, `top_factors`, `recommendations`) a `generate_intervention_pdf()`.

### PROBLEMA 11: Ausencia del formulario TAM y rol hardcodeado en la vista `Encuestas SUS / TAM`
- **Descripción:** En la vista `"Encuestas SUS / TAM"` se muestran las tarjetas de puntuación media para **SUS** y **TAM**, pero el formulario inferior solo permite responder los 10 ítems de **SUS**; no existe ningún formulario o pestaña para registrar la encuesta **TAM**. Además, al guardar la encuesta SUS, se invoca `save_survey(usuario["username"], "DOCENTE_EVAL", "SUS", ...)` con el rol hardcodeado `"DOCENTE_EVAL"` aunque quien la responde sea `ADMIN` u otro perfil.
- **Ubicación:** Vista `"Encuestas SUS / TAM"` — Rol `ADMIN`.
- **Comportamiento esperado:** Incluir tanto el cuestionario SUS como el cuestionario TAM (Utilidad Percibida y Facilidad de Uso Percibida en escala Likert 1–5) y registrar el rol real del evaluador.
- **Comportamiento observado:** `Puntuación Media TAM (Aceptación)` permanece perpetuamente en `0.0 / 5.0 (0 evaluadores)` porque no hay interfaz para alimentar encuestas TAM.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1660-L1691).
- **Causa probable:** Solo se codificó el bloque `st.form("form_sus_eval")` omitiendo el formulario para `TAM`.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Agregar pestañas (`st.tabs(["Cuestionario SUS", "Cuestionario TAM"])`) con los ítems Likert de TAM y su cálculo de promedio sobre 5.0, pasando `usuario["role"]` a `save_survey()`.

### PROBLEMA 12: Terminal FIPA-ACL desconectada de la persistencia del bus (muestra registros estáticos de fallback)
- **Descripción:** En la Vista 3 (`Trazabilidad multiagente`), `app.py` consulta la tabla `mensajes_bus` mediante `get_bus_messages_for_student()` o `get_recent_bus_messages()`. Sin embargo, ni `MessageBus.send()` (`src/messaging/bus.py`) ni `CoordinatorAgent.analyze_student_risk()` (`src/agents/coordinator_agent.py`) ni `seed_initial_data()` llaman jamás a `log_bus_message()`. Como consecuencia, la tabla `mensajes_bus` está permanentemente vacía y la terminal FIPA-ACL muestra siempre las 4 líneas estáticas decorativas del bloque `if not mensajes_reales:` (`[10:14:22] inform Ingestion → Predictor...`). Adicionalmente, cuando `mensajes_reales` sí contiene datos (`app.py:1386-1391`), el código construye la tupla `(f"[{t_str}]", perf, f"{rem} → {dest}")` **omitiendo el tópico y el contenido del mensaje**, y `get_recent_bus_messages()` en `db.py:748` ni siquiera selecciona la columna `contenido_json`.
- **Ubicación:** Vista 3 (`Trazabilidad multiagente`) — Todos los roles.
- **Comportamiento esperado:** Mostrar trazas reales generadas en el bus de mensajes con marca temporal real, performativa en mayúsculas (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`), emisor, receptor, tópico/resumen del mensaje y orden cronológico.
- **Comportamiento observado:** Muestra siempre las mismas 4 líneas estáticas con hora fija `[10:14:22]`–`[10:14:25]` y performativas en minúscula (`inform`, `propose`).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1372-L1396), [bus.py](file:///d:/TESIS%20FINAL/src/messaging/bus.py#L23-L35) y [db.py](file:///d:/TESIS%20FINAL/src/database/db.py#L731-L753).
- **Causa probable:** `log_bus_message()` fue definida en `db.py` pero nunca se invocó desde `MessageBus.send()` ni desde `CoordinatorAgent`.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Invocar `log_bus_message()` al enviar mensajes en el bus (o al cierre de `CoordinatorAgent.analyze_student_risk()`), sembrar la traza inicial del alumno demo en `seed_initial_data()`, y mostrar el tópico/resumen junto con la performativa en mayúsculas en `app.py:1386-1395`.

### PROBLEMA 13: Métricas de la Cabecera Común Autenticada muestran datos ficticios hardcodeados o desincronizados
- **Descripción:** Las 3 tarjetas superiores presentes en todas las vistas autenticadas presentan graves inconsistencias funcionales:
  1. Para `AUTORIDAD` y `ADMIN` (`app.py:1070-1072`), se asignan literales ficticios hardcodeados: `total_est = 18` y `tutorias_sem = 3` (mientras que en la BD solo existe `1` estudiante matriculado, como bien muestra `Métricas Institucionales`).
  2. Para `DOCENTE` (`app.py:1060-1065`), calcula `resumen_curso` usando siempre `catalogo[0]["nombre"]` (`"ANALISIS Y DISENO DE ALGORITMOS"`), mostrando `00` estudiantes y `00` tutorías incluso cuando el docente selecciona `"ESTRUCTURAS DE DATOS Y ALGORITMOS"` en el selector inferior. Además, asigna `tutorias_sem = resumen_curso["rojos"]` (número de alertas rojas, no tutorías programadas).
  3. Para `ESTUDIANTE` (`app.py:1066-1069`), la etiqueta de la primera tarjeta sigue diciendo `"ESTUDIANTES EN SEGUIMIENTO"` en lugar de `"ASIGNATURAS INSCRITAS"`, y `tutorias_sem` está hardcodeado como `1 if mis_mats else 0`.
  4. La tercera tarjeta (`"ÚLTIMA ACTUALIZACIÓN"`) muestra siempre `fecha_hoy` (`datetime.date.today()`) en lugar de la fecha real de la última inferencia registrada en la tabla `predicciones`.
- **Ubicación:** Cabecera Común Autenticada — Todos los roles.
- **Comportamiento esperado:** Mostrar métricas reales extraídas de la base de datos, adaptando la etiqueta de la primera tarjeta según el rol (`ASIGNATURAS INSCRITAS` para Estudiante vs `ESTUDIANTES EN SEGUIMIENTO` para personal) y sincronizándola con el curso seleccionado.
- **Comportamiento observado:** Valores ficticios (`18`, `03`, `01`) o congelados en `00`.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1059-L1101).
- **Causa probable:** Cálculos simplificados con literales estáticos en la cabecera antes de leer el selector de curso.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Consultar en SQLite el conteo real de estudiantes evaluados, el conteo real de tutorías registradas y el `MAX(fecha)` de la tabla `predicciones`, cambiando dinámicamente la etiqueta de la primera tarjeta para `ESTUDIANTE`.

### PROBLEMA 14: Funcionalidades de backend implementadas pero ausentes en la interfaz (Consentimiento Opt-in, Registro de Notas y Simulador de Sustitutorio)
- **Descripción:** Existen tres módulos clave desarrollados en `src/` y mencionados en la especificación/portada que no tienen ninguna representación visual ni acceso en `app.py`:
  1. **Simulador del Examen Sustitutorio (`calcular_simulacion_sustitutorio` en `academic_service.py:59-145`):** Se anuncia en la Pantalla 0 (*"Sustitutorio reemplaza únicamente el examen parcial más bajo"*), pero no se invoca en ninguna vista.
  2. **Registro intra-semestral de notas (`save_grade`, `get_grades_for_enrollment` en `db.py:509-572`):** Ni el estudiante ni el docente tienen un formulario para registrar o actualizar notas parciales (`EC1..EP3`) y recalcular el riesgo en tiempo real.
  3. **Consentimiento informado / Opt-in (`update_student_consent` en `db.py:409-420`):** Cuando un estudiante nuevo se registra en la pestaña `"Registro de Estudiante"`, se crea con `comparte_con_tutor = 0` (`db.py:390`), pero no existe ningún switch o casilla en su sesión para otorgar o revocar dicho consentimiento.
- **Ubicación:** Vistas de Estudiante y Docente (`app.py`).
- **Comportamiento esperado:** Toda funcionalidad de negocio declarada y codificada en los servicios debe ser accesible desde la interfaz gráfica.
- **Comportamiento observado:** Funciones huérfanas en `src/` sin importar en `app.py`.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L25-L50), [academic_service.py](file:///d:/TESIS%20FINAL/src/services/academic_service.py#L59-L145) y [db.py](file:///d:/TESIS%20FINAL/src/database/db.py#L409-L420).
- **Causa probable:** Durante el rediseño visual de `app.py` hacia los mockups se omitieron los controles operativos de notas, simulación de sustitutorio y consentimiento.
- **Severidad:** **ALTA**
- **Recomendación de solución:** Integrar el panel de simulación de sustitutorio y actualización de notas en las vistas de seguimiento/explicabilidad, e incluir el control de consentimiento informado en `"Perfil Basal"` y en `"Registro de Estudiante"`.

### PROBLEMA 15: Ningún botón primario (`type="primary"`) se renderiza en color granate
- **Descripción:** Todos los botones definidos con `type="primary"` en la aplicación (`Ingresar al Portal del Estudiante`, `Ingresar al Sistema`, `Registrar Cuenta`, `Programar tutoría`, `Registrar tutoría`, `Confirmar Inscripción de Asignatura`, `Validar y Procesar Acta con Sistema Multiagente`) se visualizan con fondo transparente/blanco, borde dorado y texto granate (el estilo de botón secundario), en lugar de tener fondo granate sólido con texto blanco.
- **Ubicación:** Transversal — Todas las pantallas (`app.py`).
- **Comportamiento esperado:** Los botones primarios deben lucir el degradado institucional granate (`linear-gradient(135deg, var(--granate), var(--granate-claro))`) con texto blanco `#FFFFFF`.
- **Comportamiento observado:** Todos los botones lucen idénticos (transparentes con borde dorado).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L254-L288).
- **Causa probable:** En las versiones actuales de Streamlit, el atributo `data-testid` de los botones primarios cambió de `"baseButton-primary"` a `"stBaseButton-primary"`. La regla de botón secundario en `app.py:271` usa el selector `.stButton button:not([data-testid="baseButton-primary"])` con `!important`. Como ningún botón tiene `data-testid="baseButton-primary"`, ese selector coincide con **todos los botones de la aplicación** y, al tener mayor especificidad CSS `(0, 2, 1)` que `button[kind="primary"]` `(0, 1, 1)`, sobreescribe a todos los botones primarios.
- **Severidad:** **MEDIA**
- **Recomendación de solución:** Actualizar los selectores en `app.py:254-288` para incluir `[data-testid="stBaseButton-primary"]` y cambiar la regla secundaria a `button[kind="secondary"], .stButton button[data-testid="stBaseButton-secondary"]`.

### PROBLEMA 16: Contraste ilegible en el Sidebar (texto negro y botón `Cerrar Sesión` granate sobre fondo granate oscuro)
- **Descripción:** En el menú lateral (`.stSidebar`), tanto el título `"Navegación:"` como todas las opciones del `st.radio` se muestran en color negro oscuro (`#0F172A`) sobre el fondo granate (`#7A1C20` a `#5A1215`). Asimismo, el botón `"Cerrar Sesión"` dentro del sidebar hereda el estilo secundario con texto granate (`#7A1C20`) sobre fondo granate oscuro (`#5A1215`), resultando casi invisible.
- **Ubicación:** Sidebar común autenticado — Todos los roles.
- **Comportamiento esperado:** Todos los textos del sidebar y el botón `"Cerrar Sesión"` deben mostrarse en color blanco (`#FFFFFF`) o dorado claro (`#E8C873`) con alto contraste AAA sobre el fondo granate.
- **Comportamiento observado:** Texto negro y texto granate sobre fondo granate oscuro (relación de contraste `< 2.1 : 1`, incumpliendo WCAG AA).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L194-L203), [app.py](file:///d:/TESIS%20FINAL/app.py#L224-L232) y [app.py](file:///d:/TESIS%20FINAL/app.py#L280-L282).
- **Causa probable:** El selector `[data-testid="stAppViewContainer"] .stRadio label p` en `app.py:199` tiene mayor especificidad CSS que `[data-testid="stSidebar"] p` en `app.py:224` (porque `stSidebar` está dentro de `stAppViewContainer`), forzando `color: var(--texto) !important` (`#0F172A`) dentro del sidebar. De igual forma, `.stButton button:not(...) *` fuerza `color: var(--granate) !important` en el botón `"Cerrar Sesión"`.
- **Severidad:** **MEDIA**
- **Recomendación de solución:** Restringir la regla de `app.py:194-203` a `[data-testid="stMain"]` en lugar de `[data-testid="stAppViewContainer"]`, y agregar una regla específica para `[data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] .stButton button *` con `color: #FFFFFF !important; border-color: var(--dorado-claro) !important;`.

### PROBLEMA 17: Ligadura rota `keyboard_double_` en el botón de colapso del Sidebar
- **Descripción:** Cuando el sidebar está desplegado, en su esquina superior derecha aparece el texto gigante blanco **`keyboard_double_`** desbordado y cortado en lugar del icono de flecha doble (`«`).
- **Ubicación:** Cabecera del Sidebar — Todos los roles.
- **Comportamiento esperado:** Mostrar únicamente el icono vectorial o glifo de colapso del sidebar sin texto de ligadura desbordado.
- **Comportamiento observado:** La cadena literal `keyboard_double_arrow_left` se renderiza con la fuente `Plus Jakarta Sans` y se corta como `keyboard_double_`.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L224-L232).
- **Causa probable:** La regla `[data-testid="stSidebar"] span { font-family: 'Plus Jakarta Sans', sans-serif !important; }` sobreescribe la fuente `Material Symbols Rounded` que Streamlit utiliza en `<span data-testid="stIconMaterial">keyboard_double_arrow_left</span>`.
- **Severidad:** **MEDIA**
- **Recomendación de solución:** Excluir los iconos de Material Symbols en el selector CSS: `[data-testid="stSidebar"] span:not([data-testid="stIconMaterial"])` o restaurar `font-family: 'Material Symbols Rounded' !important;` para `[data-testid="stIconMaterial"]`.

### PROBLEMA 18: Cuerpo de la terminal FIPA-ACL con fondo blanco en lugar de granate oscuro
- **Descripción:** La especificación exige que la terminal de mensajes FIPA-ACL tenga **fondo granate oscuro** y tipografía monoespaciada `JetBrains Mono`. En la implementación actual, solo la franja superior del título (`.fipa-log-header`) tiene fondo granate oscuro, mientras que el cuerpo de la terminal (`.fipa-log-body`) tiene fondo blanco (`#FFFFFF`).
- **Ubicación:** Vista 3 (`Trazabilidad multiagente`) — Todos los roles.
- **Comportamiento esperado:** Cuerpo de terminal con fondo granate oscuro (`#5A1215` o `#2A080A`), texto claro de alto contraste y performativas destacadas en dorado/ámbar.
- **Comportamiento observado:** Cuerpo de tarjeta blanco con texto oscuro y performativas en minúscula.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L710-L734).
- **Causa probable:** En `.fipa-log-body` (`app.py:721`) se definió `background-color: #FFFFFF !important;`.
- **Severidad:** **MEDIA**
- **Recomendación de solución:** Cambiar `.fipa-log-body` a `background-color: var(--granate-oscuro) !important; color: #F8FAFC !important;` y `.fipa-performative` a `color: var(--dorado-claro) !important; text-transform: uppercase;`.

### PROBLEMA 19: Omisión del Checkpoint en Vista 2 e inconsistencias en el gráfico longitudinal de Vista 4
- **Descripción:**
  1. En la Vista 2 (`Detalle con explicabilidad`), la tarjeta de diagnóstico no muestra en ningún lugar el Checkpoint activo (`CP0`, `CP1`, `CP2` o `CP3`) a pesar de ser un requisito explícito de la especificación.
  2. En la Vista 4 (`Seguimiento y plan de tutoría`), el gráfico longitudinal muestra en el eje X `["Sem 1", "Sem 8", "Sem 16"]` con valores fijos `[22.0, 48.0, 78.0]` en vez de la evolución por Checkpoints (`CP0 → CP1 → CP2 → CP3`).
  3. Las líneas horizontales de umbral en el gráfico están fijadas en `34.0%` (etiquetada como `"Umbral Preventivo (34%)"`) y `75.0%` (`"Umbral Crítico (75%)"`), confundiendo el umbral crítico calibrado de `CP1` (`0.340 = 34.0%` según `PredictorAgent.THRESHOLDS`) con el umbral preventivo (`0.75 * 0.340 = 25.5%` según `calcular_semaforo()`).
  4. El cálculo de tendencia (`tendencia_txt = "al alza" if riesgos[-1] > riesgos[0] else "estable"`) nunca reporta `"a la baja"` cuando el riesgo desciende.
- **Ubicación:** Vistas 2 y 4 — Roles `ESTUDIANTE` y `DOCENTE`.
- **Comportamiento esperado:** Mostrar explícitamente el Checkpoint en Vista 2; graficar `CP0 → CP1 → CP2 → CP3` en Vista 4 con los umbrales reales del modelo (preventivo `0.75 * th` y crítico `th`) y clasificar la tendencia en `"al alza"`, `"a la baja"` o `"estable"`.
- **Comportamiento observado:** Checkpoint ausente en Vista 2; umbrales confundidos y tendencia incompleta en Vista 4.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L1268-L1285) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1435-L1477).
- **Causa probable:** Valores estáticos codificados en la capa de presentación sin consultar `THRESHOLDS` ni `calcular_semaforo()`.
- **Severidad:** **MEDIA**
- **Recomendación de solución:** Renderizar `pred_rec.get("checkpoint", "CP1")` en la tarjeta izquierda de Vista 2; usar los umbrales reales en Vista 4 y corregir la expresión condicional de tendencia para incluir `"a la baja"` cuando `riesgos[-1] < riesgos[0]`.

### PROBLEMA 20: Superposición del botón flotante `>>` de reapertura del Sidebar sobre títulos y textos
- **Descripción:** Cuando el sidebar está colapsado (tanto en escritorio `1280x800` como en móvil `375x812`), el botón granate `>>` (`[data-testid="stExpandSidebarButton"]`) queda fijo en `top: 0.6rem; left: 0.8rem; z-index: 999999` y se superpone directamente sobre el texto del pie de sub-cabecera (`"Datos anonimizados con CUI hash..."`), los títulos de sección (`"¿Qué influyó en este resultado?"`, `"Cómo se calculó esta alerta"`, `"Evolución y plan de tutoría"`) y las métricas al hacer scroll vertical.
- **Ubicación:** Transversal — Todas las vistas autenticadas al hacer scroll con el sidebar colapsado.
- **Comportamiento esperado:** El botón de reapertura del sidebar no debe tapar títulos ni textos de lectura del contenedor principal.
- **Comportamiento observado:** Superposición directa verificada en más de 15 capturas (ej. `01_estudiante/09_vista3_trazabilidad_fipa_acl.png`, `01_estudiante/11_vista4_plan_tutoria_bitacora.png`, `04_administrador/05_vista4_encuestas_sus_tam_arriba.png`).
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L125-L149) y [app.py](file:///d:/TESIS%20FINAL/app.py#L185-L191).
- **Causa probable:** `.block-container` tiene `padding-top: 1.2rem` y `padding-left: 2rem` (`1rem` en móvil), lo cual deja el contenido alineado debajo de la coordenada fija del botón flotante.
- **Severidad:** **BAJA**
- **Recomendación de solución:** Incrementar el `padding-top` o `padding-left` del contenedor o mantener la barra superior `header[data-testid="stHeader"]` con fondo sólido institucional (`var(--fondo)`) para que el contenido al hacer scroll pase limpiamente por debajo del encabezado sin colisionar visualmente con el botón.

### PROBLEMA 21: Colisión de texto sin espacio entre el CUI hash y el nombre en la lista de estudiantes del Docente
- **Descripción:** En el `"Panel de seguimiento"` para `DOCENTE` y `AUTORIDAD`, cada fila de estudiante renderiza `<span class="cui-mono">CUI {cui_txt}</span><span class="student-name">{nom_txt}</span>` dentro de un contenedor flex `.student-list-row` que no tiene propiedad `gap`. Como resultado, ambos textos quedan pegados sin separación: `CUI E7BB88B1B2BDD47FEstudiante (A)`.
- **Ubicación:** Vista 1 (`Panel de seguimiento`) — Roles `DOCENTE` y `AUTORIDAD`.
- **Comportamiento esperado:** Separación visual clara (al menos `12px`–`16px` o columnas definidas) entre el identificador anonimizado, la sección y el estado de riesgo.
- **Comportamiento observado:** Texto fusionado `CUI E7BB88B1B2BDD47FEstudiante (A)`.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L568-L583) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1203-L1209).
- **Causa probable:** Falta `gap: 14px;` en la clase CSS `.student-list-row`.
- **Severidad:** **BAJA**
- **Recomendación de solución:** Añadir `gap: 16px;` a `.student-list-row` en `app.py:568`.

### PROBLEMA 22: Columna `semestre` sin renombrar y diagrama de agentes sin línea conectora en resoluciones medias
- **Descripción:**
  1. En `"Métricas Institucionales"` (`app.py:1638-1643`), `df_macro.rename(columns=...)` renombra todas las columnas excepto `"semestre"`, que aparece en minúscula (`semestre`) junto a encabezados capitalizados (`Asignatura`, `Total Estudiantes`, etc.).
  2. En `"Trazabilidad multiagente"`, el diagrama horizontal de 4 nodos se envuelve en una cuadrícula 2x2 cuando el sidebar está expandido o en pantallas medianas, ocultando la línea dorada conectora `.stepped-line`.
- **Ubicación:** Vista `"Métricas Institucionales"` y Vista 3 (`"Trazabilidad multiagente"`).
- **Comportamiento esperado:** Encabezados de tabla uniformes (`"Semestre"`) y los 4 nodos del pipeline alineados en una sola fila en escritorio (`1280x800`).
- **Comportamiento observado:** Columna `semestre` en minúscula y nodos en disposición 2x2.
- **Archivo relacionado:** [app.py](file:///d:/TESIS%20FINAL/app.py#L668-L680) y [app.py](file:///d:/TESIS%20FINAL/app.py#L1638-L1643).
- **Causa probable:** Falta `"semestre": "Semestre"` en el diccionario de `rename()` y el ancho `width: 23%` con `flex-wrap` colapsa en contenedores reducidos por el sidebar.
- **Severidad:** **BAJA**
- **Recomendación de solución:** Añadir `"semestre": "Semestre"` en `app.py:1639` y ajustar `.stepped-nodes` para mantener los 4 nodos en línea horizontal en resoluciones `> 640px`.

---

## E. RESUMEN DE DISEÑO (EVALUACIÓN DE CONSISTENCIA VISUAL Y UI/UX)

1. **Identidad Visual y Paleta Institucional:**
   - **Aciertos:** La cabecera institucional (`.unsa-header-banner`) con el escudo oficial de la UNSA, el fondo granate oscuro con trama diagonal sutil, el filete dorado inferior (`.unsa-banner-fillet`), las tarjetas de semáforo (`RIESGO ALTO`, `ALERTA PREVENTIVA`, `RIESGO BAJO`) y el medidor circular SVG mantienen una estética académica sobria, limpia y libre de emojis no deseados.
   - **Deficiencias:** El fallo de especificidad CSS en `.stButton button:not([data-testid="baseButton-primary"])` priva a toda la interfaz de sus botones primarios granates, haciendo que las acciones principales carezcan de jerarquía visual frente a las acciones secundarias. Asimismo, el cuerpo blanco de la terminal FIPA-ACL rompe la especificación de terminal oscura institucional.

2. **Tipografía y Contraste:**
   - **Aciertos:** El uso combinado de `Plus Jakarta Sans` para títulos/cuerpo y `JetBrains Mono` para hashes criptográficos, porcentajes y registros de auditoría aporta rigor técnico y excelente legibilidad en el contenedor principal.
   - **Deficiencias Críticas de Contraste:** En el sidebar lateral (`.stSidebar`), la colisión de reglas CSS fuerza texto oscuro (`#0F172A`) para los radio buttons y texto granate (`#7A1C20`) para el botón `"Cerrar Sesión"` sobre un fondo granate oscuro (`#5A1215`), provocando un contraste deficiente que dificulta severamente la lectura del menú de navegación. Además, forzar `Plus Jakarta Sans` sobre todos los `<span>` del sidebar rompe la fuente `Material Symbols Rounded`, mostrando la cadena cruda `keyboard_double_`.

3. **Distribución, Componentes y Responsividad (Escritorio vs. Móvil):**
   - **Aciertos:** En resolución móvil (`375x812`), las columnas de Login, las tarjetas de métricas superiores y las tarjetas de semáforo colapsan de forma ordenada a una sola columna vertical sin generar scroll horizontal innecesario en el body.
   - **Deficiencias:** El botón flotante `>>` de reapertura del sidebar carece de una franja superior reservada y se superpone a los títulos y textos superiores al hacer scroll tanto en escritorio como en móvil. En las filas de la lista de estudiantes del Docente falta un `gap` horizontal, provocando que el hash CUI y el nombre del estudiante aparezcan pegados.

---

## F. PLAN DE CORRECCIÓN PRIORIZADO

### 1. Problemas Críticos (Bloqueantes para Sustentación — Prioridad Inmediata)
1. **Corregir el `KeyError: 'latencia_inf_media_ms'` en `Monitor Técnico OBJ5` (`src/database/db.py:779-786` y `app.py:1651-1657`):** Homologar las claves retornadas por `get_technical_metrics_summary()` cuando la tabla está vacía e instrumentar `log_technical_metrics()` en `CoordinatorAgent.analyze_student_risk()` y en `seed_initial_data()`.
2. **Corregir el `AuthorizationError` en `Panel de seguimiento` para `ADMIN` y el acceso individual para `AUTORIDAD` (`app.py:1186-1209`):** Mostrar la tabla individual de estudiantes exclusivamente para `rol == "DOCENTE"`. Para `AUTORIDAD` y `ADMIN`, mostrar un resumen agregado por asignatura/sección o remover `"Panel de seguimiento"` del menú de `ADMIN`.
3. **Corregir las barras SHAP y la dirección de factores protectores en Vista 2 (`app.py:1292-1313`):** Graficar `f.get("impact")` en lugar de `f.get("value")`, asignar color granate (`--granate`) solo cuando `impact > 0` y azul (`--azul-factor`) cuando `impact < 0`, mostrando el signo real (`+` / `-`) y escalando el ancho de barra respecto a la magnitud de `impact`.
4. **Conectar la Carga Masiva de Actas a la persistencia real en SQLite (`src/services/academic_service.py:314-338`):** Guardar cada registro válido procesado por el SMA en las tablas `estudiantes`, `matriculas`, `notas`, `predicciones`, `explicaciones`, `mensajes_bus` y `metricas_tecnicas`.

### 2. Problemas de Alta Prioridad (Funcionalidad Principal e Integridad de Datos)
5. **Añadir selectores de Asignatura y Estudiante Anonimizado para el Docente en las Vistas 2 y 4 (`app.py:1241`, `app.py:1428`):** Reemplazar el hardcodeo `mat_id_act = 1` y `CUI 7f3a...c91` por selectores reales alimentados desde `get_course_students_table()`.
6. **Conectar la terminal FIPA-ACL a registros reales del bus (`src/messaging/bus.py`, `src/agents/coordinator_agent.py`, `app.py:1372-1396`):** Invocar `log_bus_message()` durante la ejecución del pipeline multiagente, sembrar las trazas iniciales en `seed_initial_data()`, mostrar performativas en mayúsculas (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`) e incluir el tópico/resumen del mensaje en la terminal.
7. **Reemplazar datos ficticios en la Cabecera Común y en la exportación PDF (`app.py:1059-1101`, `app.py:1505-1526`):** Alimentar las 3 tarjetas superiores con consultas reales a SQLite (cambiando la etiqueta a `ASIGNATURAS INSCRITAS` para el Estudiante y sincronizando con el curso activo del Docente) y pasar a `generate_intervention_pdf()` los datos reales de `get_latest_prediction()`.
8. **Hacer funcionales la Bitácora de Tutoría y los botones `Programar tutoría`, `Registrar tutoría` y `Ver explicación` (`app.py:1213-1219`, `1480-1504`):** Implementar navegación real hacia Vista 2 al pulsar `Ver explicación` (ocultándolo para `AUTORIDAD`/`ADMIN`), convertir las acciones de la bitácora en `st.checkbox` persistentes y guardar las tutorías programadas/registradas en la base de datos.
9. **Completar el formulario de encuesta TAM y exponer las funciones huérfanas de backend (`app.py`):** Añadir el cuestionario TAM en `"Encuestas SUS / TAM"`, e integrar en la interfaz el simulador de Examen Sustitutorio (`calcular_simulacion_sustitutorio`), el registro de notas parciales (`save_grade`) y el switch de consentimiento informado (`update_student_consent`).

### 3. Problemas de Prioridad Media (Presentación Visual y Precisión de Indicadores)
10. **Restaurar el color granate en todos los botones primarios (`app.py:254-288`):** Actualizar los selectores CSS a `[data-testid="stBaseButton-primary"]` y `[data-testid="stBaseButton-secondary"]`.
11. **Corregir el contraste del Sidebar y la ligadura rota `keyboard_double_` (`app.py:194-232`):** Limitar la regla de texto oscuro a `[data-testid="stMain"]`, excluir `[data-testid="stIconMaterial"]` de la sobreescritura de `font-family`, y forzar texto blanco/dorado en el botón `"Cerrar Sesión"` del sidebar.
12. **Aplicar fondo granate oscuro al cuerpo de la terminal FIPA-ACL (`app.py:720-734`):** Cambiar `.fipa-log-body` a fondo `var(--granate-oscuro)` con texto claro.
13. **Mostrar el Checkpoint activo en Vista 2 y corregir umbrales y tendencia en el gráfico longitudinal de Vista 4 (`app.py:1268-1285`, `1435-1477`):** Incluir el badge de `CP0`–`CP3` en Vista 2, graficar los umbrales reales del checkpoint activo (`0.75 * th` preventivo y `th` crítico) y añadir el caso `"a la baja"` en el cálculo de tendencia.

### 4. Mejoras Estéticas (Baja Prioridad)
14. **Evitar superposición del botón flotante `>>` con los títulos de página (`app.py:110-134`, `185-191`):** Ajustar el espaciado superior/izquierdo o el fondo de `stHeader`.
15. **Añadir `gap: 16px` en `.student-list-row` (`app.py:568`):** Separar visualmente el código `CUI <hash>` del nombre/sección del estudiante.
16. **Renombrar la columna `"semestre"` a `"Semestre"` en `Métricas Institucionales` (`app.py:1638`) y mantener los 4 nodos del diagrama multiagente en una sola fila en escritorio.**
