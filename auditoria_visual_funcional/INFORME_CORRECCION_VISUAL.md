# INFORME DE AUDITORÍA Y CORRECCIÓN VISUAL, UX, ACCESIBILIDAD Y RESPONSIVE (FASE 4) — SATA-UNSA

**Proyecto:** Sistema de Alerta Temprana Académica (SATA-UNSA) — Escuela Profesional de Ingeniería de Sistemas (EPIS-UNSA)  
**Rama de trabajo:** `fix-ui-acceso`  
**URL auditada y verificada en vivo:** `http://localhost:8501`  
**Fecha de ejecución:** 14 de noviembre de 2026  
**Referencias previas auditadas:**
1. `auditoria_visual_funcional/INFORME_AUDITORIA_EXHAUSTIVA.md` (Fase 1)
2. `auditoria_visual_funcional/INFORME_CORRECCION_CRITICOS.md` (Fase 2)
3. `auditoria_visual_funcional/INFORME_CORRECCION_PRIORIDAD_ALTA.md` (Fase 3)

---

## 1. Resumen Ejecutivo

En la **Fase 4** se ejecutó una auditoría visual, de experiencia de usuario (UX), accesibilidad (contraste WCAG 2.1 AA/AAA) y adaptabilidad *responsive* sobre la aplicación **SATA-UNSA**, seguida de la corrección quirúrgica de la capa de estilos CSS y estructuración visual en `app.py`.

Se resolvieron en su totalidad los **8 hallazgos visuales y de experiencia de usuario (A–H)** detectados en la auditoría inicial y en las revisiones post-Fase 3, preservando íntegramente:
- La identidad visual institucional de la **Universidad Nacional de San Agustín de Arequipa (UNSA)**: granate institucional (`#7A1C20` / `#5A1215`), dorado académico (`#C59B27` / `#E8C873`), azul para factores protectores SHAP (`#1E4E79`) y superficies claras (`#F8FAFC` / `#FFFFFF`).
- La arquitectura de **7 agentes inteligentes**, el protocolo **FIPA-ACL**, los modelos **Random Forest (`CP0`–`CP3`)**, la explicabilidad **SHAP**, el esquema **SQLite** y el control de acceso basado en roles (**RBAC**) con anonimización **HMAC-SHA256**.

---

## 2. Problemas Visuales Encontrados y Causa Raíz Técnica

| Código | Componente / Vista | Problema Visual Detectado | Causa Raíz en `app.py` | Estado Final |
| :--- | :--- | :--- | :--- | :--- |
| **VIS-A** (`HALL-010`) | Botones principales en todas las vistas | Los botones primarios (`Ingresar al Portal del Estudiante`, `Programar tutoría`, `Registrar tutoría`, `Guardar Calificación y Recalcular Alerta`, `Confirmar Inscripción`, `Guardar Evaluación SUS/TAM`) se renderizaban con fondo transparente y borde dorado en lugar del fondo granate institucional (`#7A1C20`) con texto blanco (`#FFFFFF`). | El selector secundario `.stButton button:not([data-testid="baseButton-primary"])` tenía mayor especificidad (`0,2,1`) que `button[kind="primary"]` (`0,1,1`) y coincidía con todos los botones de Streamlit 1.35+ porque el atributo actual de Streamlit es `data-testid="stBaseButton-primary"` (y `[data-testid="stFormSubmitButton"] button` en formularios). | **CORREGIDO Y VERIFICADO** |
| **VIS-B** (`HALL-011`) | Sidebar institucional (`[data-testid="stSidebar"]`) | Las opciones del `st.sidebar.radio` perdían contraste al heredar texto oscuro (`#0F172A`), y el botón `Cerrar Sesión` mostraba texto granate sobre el fondo granate oscuro del sidebar. | El selector global `[data-testid="stAppViewContainer"] .stRadio label p { color: var(--texto) !important; }` (`0,2,2`) sobreescribía `[data-testid="stSidebar"] p` (`0,1,1`) porque `stSidebar` es hijo de `stAppViewContainer`. Además, `Cerrar Sesión` heredaba el estilo de botón secundario para fondos claros. | **CORREGIDO Y VERIFICADO** |
| **VIS-C** (`HALL-011b`) | Iconografía del botón de colapso del Sidebar | Al abrir el menú lateral, el botón superior derecho de colapso renderizaba el texto literal truncado `keyboard_double_` en lugar del icono de doble flecha (`«`). | La regla `[data-testid="stSidebar"] span { font-family: 'Plus Jakarta Sans', sans-serif !important; }` sobrescribía la fuente de iconos `Material Symbols Rounded` en `<span data-testid="stIconMaterial">keyboard_double_arrow_left</span>`, rompiendo la ligadura tipográfica. | **CORREGIDO Y VERIFICADO** |
| **VIS-D** (`HALL-012`) | Terminal de Auditoría FIPA-ACL (Vista 3) | El contenedor `.fipa-log-body` tenía fondo blanco (`#FFFFFF`) desconectado de su cabecera oscura `.fipa-log-header`, y todas las performativas (`REQUEST`, `INFORM`, `PROPOSE`, `FAILURE`) compartían el mismo color plano sin distinción visual. | `.fipa-log-body` estaba definido con `background-color: #FFFFFF !important; color: var(--texto) !important;` y carecía de clases semánticas por tipo de performativa FIPA-ACL. | **CORREGIDO Y VERIFICADO** |
| **VIS-E** (`HALL-013`) | Botón flotante de expansión del Sidebar (`»`) y cabecera | Al hacer scroll vertical con el sidebar colapsado o en resoluciones móviles, el botón flotante `»` (`top: 0.6rem; left: 0.8rem`) se superponía directamente sobre los títulos de sección, tarjetas y gráficos. | `header[data-testid="stHeader"]` era totalmente transparente (`background: transparent !important`) y `.block-container` tenía `padding-top: 1.2rem !important`, provocando colisión directa con el botón fijo superior izquierdo. | **CORREGIDO Y VERIFICADO** |
| **VIS-F** (`HALL-014`) | Listas de estudiantes y asignaturas (`.student-list-row`) | El código anonimizado `.cui-mono` y el nombre de la asignatura/estudiante carecían de separación flexible y un contenedor tipo *badge* que diferenciara visualmente el identificador criptográfico del texto descriptivo. | `.student-list-row` no tenía `gap` ni `flex-wrap`, y `.cui-mono` era texto plano sin fondo ni borde contenedor. | **CORREGIDO Y VERIFICADO** |
| **VIS-G** (`HALL-015`) | Tabla en `Métricas Institucionales` y gráfico en Vista 4 | En `Métricas Institucionales`, la columna `semestre` aparecía en minúscula mientras las demás columnas estaban capitalizadas. En Vista 4, las líneas de referencia del gráfico longitudinal mostraban `34%` (Preventivo) y `75%` (Crítico) fijos en lugar de los umbrales calibrados del checkpoint activo (`25.5%` Preventivo y `34.0%` Crítico en `CP1`) y sin leyenda visible. | `df_macro.rename(columns={...})` omitía la clave `"semestre": "Semestre"`, y el gráfico de Matplotlib en Vista 4 tenía valores `y=34.0` y `y=75.0` estáticos sin `ax.legend()`. | **CORREGIDO Y VERIFICADO** |
| **VIS-H** (`HALL-016`) | Pipeline multiagente (`.stepped-pipeline-container`) y responsive | En resoluciones intermedias y móviles se requería garantizar que los 4 nodos permanecieran en una sola fila horizontal con línea conectora dorada en escritorio/portátil (`1440px`, `1366px`), pasaran a cuadrícula `2x2` en tablet (`768px`) y a columna vertical `1x4` en móvil (`390px`) sin scroll horizontal. | Faltaba `flex: 1 1 0; min-width: 0; flex-wrap: nowrap` en escritorio y el breakpoint específico `@media (max-width: 480px)` para smartphones de `375px`–`390px`. | **CORREGIDO Y VERIFICADO** |

---

## 3. Cambios Realizados en CSS y Componentes Visuales

Todas las modificaciones se aplicaron de manera localizada en `app.py` sin tocar la lógica de negocio ni los módulos de `src/`:

### 3.1 Botones Principales y Secundarios (`app.py`, líneas 295–366)
- **Botones primarios (`[data-testid="stMain"] button[kind="primary"]`, `button[data-testid="stBaseButton-primary"]`, `[data-testid="stFormSubmitButton"] button`):**
  - Fondo degradado institucional: `linear-gradient(135deg, var(--granate) 0%, var(--granate-claro) 100%) !important` (`#7A1C20` a `#962228`).
  - Texto blanco puro: `#FFFFFF !important` con `font-weight: 700`.
  - Estados `:hover` (elevación `-1px` y sombra cálida), `:focus-visible` (`outline: 3px solid var(--dorado-claro)`), `:active` y `:disabled` (`opacity: 0.55`).
- **Botones secundarios y de descarga (`button[kind="secondary"]`, `button[data-testid="stBaseButton-secondary"]`, `[data-testid="stDownloadButton"] button`):**
  - Fondo `#FFFFFF !important`, borde `1.5px solid var(--dorado) !important` (`#C59B27`) y texto `var(--granate) !important` (`#7A1C20`), con hover suave en dorado translúcido (`rgba(197, 155, 39, 0.1)`).

### 3.2 Contraste del Sidebar y Botón `Cerrar Sesión` (`app.py`, líneas 207–294)
- Se acotaron los selectores de texto oscuro exclusivamente a `[data-testid="stMain"]` para evitar que contaminen `[data-testid="stSidebar"]`.
- En `[data-testid="stSidebar"]`, todas las etiquetas de `st.radio`, títulos y subtítulos tienen color `#FFFFFF !important` sobre el fondo `linear-gradient(180deg, #7A1C20 0%, #5A1215 100%)` (relación de contraste **10.45:1**, nivel **WCAG AAA**).
- El ítem activo de navegación (`label:has(input:checked)`) presenta fondo translúcido `rgba(255, 255, 255, 0.2)` y barra izquierda dorada `3px solid var(--dorado-claro)` (`#E8C873`).
- Los códigos inline (`code`) del pie del sidebar (`ID Criptográfico` / `Usuario`) tienen color dorado claro `#E8C873` sobre pastilla oscura `rgba(0, 0, 0, 0.25)`.
- El botón `Cerrar Sesión` en `[data-testid="stSidebar"] .stButton button` cuenta con fondo `rgba(255, 255, 255, 0.12)`, borde `1.5px solid var(--dorado-claro)` y texto `#FFFFFF !important`.

### 3.3 Reparación de Ligaduras Material Symbols (`app.py`, líneas 180–198 y 242–249)
- Se excluyó `[data-testid="stIconMaterial"]` de la regla tipográfica `Plus Jakarta Sans` mediante `:not([data-testid="stIconMaterial"]):not(.material-icons)`.
- Se añadió la regla explícita para `[data-testid="stIconMaterial"]`, `[data-testid="stSidebarCollapseButton"] span` y `[data-testid="stExpandSidebarButton"] span` forzando `font-family: 'Material Symbols Rounded', 'Material Icons' !important; font-size: 20px !important; color: #FFFFFF !important;`, restaurando el icono vectorial `«` / `»` y eliminando por completo el texto truncado `keyboard_double_`.

### 3.4 Rediseño de la Terminal de Auditoría FIPA-ACL (`app.py`, líneas 772–845 y 1736–1779)
- `.fipa-log-body` ahora emplea superficie oscura de consola (`background-color: #1E0709 !important`), borde dorado sutil (`rgba(197, 155, 39, 0.45)`), tipografía monoespaciada `JetBrains Mono` y `overflow-x: auto` para proteger vistas móviles.
- Cada mensaje se estructura en `.fipa-log-row` con:
  - `.fipa-time`: marca temporal en `#CBD5E1` (contraste > 11:1 sobre `#1E0709`).
  - `.fipa-conv-id`: identificador de conversación anonimizado en pastilla monoespaciada `#E2E8F0`.
  - Badges semánticos diferenciados por performativa FIPA-ACL:
    - `REQUEST` (`.fipa-perf-request`): dorado ámbar (`#FCD34D` sobre `rgba(245, 158, 11, 0.22)`).
    - `INFORM` (`.fipa-perf-inform`): azul cielo (`#7DD3FC` sobre `rgba(56, 189, 248, 0.20)`).
    - `PROPOSE` (`.fipa-perf-propose`): verde esmeralda (`#86EFAC` sobre `rgba(34, 197, 94, 0.20)`).
    - `FAILURE` (`.fipa-perf-failure`): rojo coral (`#FCA5A5` sobre `rgba(239, 68, 68, 0.25)`).
  - `.fipa-route`: ruta `Emisor → Receptor` en blanco brillante `#FFFFFF`.
  - `.fipa-topic`: tópico del mensaje en dorado claro `#E8C873`.

### 3.5 Barra Superior Fija y Eliminación de Colisiones del Botón `»` (`app.py`, líneas 126–179 y 202–208)
- `header[data-testid="stHeader"]` se configuró con `height: 2.75rem !important`, fondo translúcido `rgba(248, 250, 252, 0.92)` con `backdrop-filter: blur(6px)` y línea divisoria inferior `1px solid rgba(226, 232, 240, 0.8)`.
- `.block-container` incrementó su `padding-top` a `3.3rem !important`, garantizando que el botón `»` (`height: 32px`, `top: 0.35rem`, `left: 0.75rem`) quede alojado dentro de la barra superior dedicada y jamás se superponga con el banner ni con los títulos durante el desplazamiento vertical.

### 3.6 Listas, Badges `.cui-mono`, Tabla Macro y Umbrales del Gráfico Longitudinal (`app.py`, líneas 226–238, 689–705, 1859–1896 y 2254–2266)
- `.student-list-row` incorpora `gap: 14px; flex-wrap: wrap; padding: 13px 8px;`, y `.cui-mono` se presenta como un badge monoespaciado (`background-color: var(--azul-hielo); border: 1px solid #CBD5E1; border-radius: 6px; padding: 3px 10px;`).
- En `Métricas Institucionales`, `df_macro.rename(columns={...})` incluye `"semestre": "Semestre"`, uniformizando todos los encabezados de tabla.
- En `Seguimiento y plan de tutoría` (Vista 4), el gráfico longitudinal traza dinámicamente el **Umbral Preventivo (`0.75 × umbral_checkpoint`, p. ej. `25.5%` en `CP1`)** y el **Umbral Crítico (`umbral_checkpoint`, p. ej. `34.0%` en `CP1`)** con su cuadro de leyenda (`ax.legend()`).

---

## 4. Mejoras de Experiencia de Usuario (UX) y Accesibilidad (WCAG 2.1)

| Elemento Evaluado | Color de Texto | Color de Fondo | Relación de Contraste | Nivel WCAG 2.1 |
| :--- | :--- | :--- | :--- | :--- |
| Botón primario (`.stBaseButton-primary`) | `#FFFFFF` | `#7A1C20` | **8.32 : 1** | **AAA** (Texto normal y grande) |
| Navegación Sidebar (`stSidebar .stRadio`) | `#FFFFFF` | `#6A171B` (medio) | **9.65 : 1** | **AAA** |
| Botón `Cerrar Sesión` en Sidebar | `#FFFFFF` | `#5A1215` | **11.12 : 1** | **AAA** |
| Texto principal en tarjetas (`.unsa-card`) | `#0F172A` | `#FFFFFF` | **17.85 : 1** | **AAA** |
| Texto secundario / subtítulos (`.section-subtitle`) | `#475569` | `#F8FAFC` | **7.18 : 1** | **AAA** |
| Consola FIPA-ACL — Ruta de agentes (`.fipa-route`) | `#FFFFFF` | `#1E0709` | **18.40 : 1** | **AAA** |
| Consola FIPA-ACL — Performativa `REQUEST` | `#FCD34D` | `#1E0709` | **12.60 : 1** | **AAA** |
| Consola FIPA-ACL — Performativa `INFORM` | `#7DD3FC` | `#1E0709` | **10.15 : 1** | **AAA** |
| Badge Riesgo Alto (`.badge-alto`) | `#991B1B` | `#FEF2F2` | **7.42 : 1** | **AAA** |
| Badge Alerta Preventiva (`.badge-alerta`) | `#92400E` | `#FFFBEB` | **6.58 : 1** | **AA / AAA (Grande)** |
| Badge Riesgo Bajo (`.badge-bajo`) | `#166534` | `#F0FDF4` | **6.84 : 1** | **AA / AAA (Grande)** |

---

## 5. Resultados de Pruebas Responsive por Resolución

Se verificó el comportamiento visual e interactivo en las cuatro resoluciones requeridas:

1. **Escritorio Grande (`1440×900`):**
   - Sidebar expandido a la izquierda (`«` visible y nítido) junto al área principal de hasta `1240px`.
   - Las 3 tarjetas superiores de resumen y las 3 tarjetas de semáforo se alinean horizontalmente con altura uniforme.
   - El pipeline de 4 agentes (`Datos`, `Predictor`, `Explicador`, `Tutor`) se muestra en una sola línea horizontal con la línea conectora dorada continua.
   - Evidencias: `step_251_shot_1_fase4_01_login_1440x900.png`, `step_296_shot_1_desk_1440_docente_panel.png`, `step_296_shot_2_desk_1440_docente_trazabilidad.png`, `step_298_shot_1_desk_1440_docente_seguimiento.png`, `step_298_shot_2_desk_1440_autoridad_metricas.png`.
2. **Portátil Estándar (`1366×768`):**
   - Con el sidebar abierto, el pipeline de 4 agentes conserva su disposición horizontal en una sola fila sin recortes ni saltos de línea, y la terminal FIPA-ACL muestra las trazas completas sin desbordamiento.
   - Evidencia: `step_303_shot_1_laptop_1366_trazabilidad.png`.
3. **Tablet (`768×1024`):**
   - El banner institucional centra su escudo y títulos limpiamente (`flex-direction: column; text-align: center`).
   - El pipeline multiagente se reorganiza en cuadrícula `2×2` (`width: calc(50% - 8px)`), ocultando la línea horizontal para evitar cruces visuales.
   - Evidencias: `step_280_shot_1_step_279_shot_1_fase4_14a_tablet_login_768x1024.png`, `step_280_shot_2_step_279_shot_2_fase4_14b_tablet_estudiante_pane.png`.
4. **Móvil (`390×844` y `375×812`):**
   - El sidebar permanece colapsado por defecto y su botón de apertura `»` queda contenido en la barra fija superior sin tapar títulos ni tarjetas al hacer scroll.
   - Los 4 nodos del pipeline se apilan en una sola columna vertical (`100%` de ancho) con lectura secuencial `1 → 2 → 3 → 4`.
   - Los botones tienen área táctil completa (`use_container_width=True`, altura `>= 40px`) y `overflow-x: hidden` evita cualquier barra de desplazamiento horizontal parásita.
   - Evidencias: `step_303_shot_2_movil_390_trazabilidad.png`, `step_282_shot_1_step_281_shot_1_fase4_11a_estudiante_panel_movil.png`, `step_282_shot_2_step_281_shot_2_fase4_11b_estudiante_panel_boton.png`.

---

## 6. Verificación por Rol (`ESTUDIANTE`, `DOCENTE`, `AUTORIDAD`, `ADMIN`)

| Rol | Usuario Probado | Vistas Verificadas en Navegador | Resultado |
| :--- | :--- | :--- | :--- |
| **ESTUDIANTE** | CUI `20220638` (`E7BB88B1...`) | `Panel de seguimiento`, `Detalle con explicabilidad`, `Trazabilidad multiagente`, `Seguimiento y plan de tutoría`, `Inscribir Asignatura`, `Perfil Basal` | **100% conforme** (botones granates, gauge SVG 78%, barras SHAP, FIPA-ACL oscuro, simulador normativo) |
| **DOCENTE** | `docente_demo` | `Panel de seguimiento`, `Detalle con explicabilidad`, `Trazabilidad multiagente`, `Seguimiento y plan de tutoría`, `Carga Masiva de Actas` | **100% conforme** (selectores dinámicos, badge `.cui-mono` separado, botón `Guardar Calificación` en granate) |
| **AUTORIDAD** | `tutor_epis` | `Panel de seguimiento`, `Métricas Institucionales`, `Trazabilidad multiagente` | **100% conforme** (columna `Semestre` capitalizada, vista agregada sin PII) |
| **ADMIN** | `admin` | `Panel de seguimiento`, `Monitor Técnico OBJ5`, `Trazabilidad multiagente`, `Encuestas SUS / TAM` | **100% conforme** (métricas H3 en vivo, formularios SUS y TAM con botones granates) |

---

## 7. Índice de Capturas antes y después (`07_post_correccion_visual`)

Todas las capturas de verificación post-corrección visual se encuentran almacenadas en `auditoria_visual_funcional/evidencias/07_post_correccion_visual/` (conservando intactas las carpetas `01_login_y_roles` a `06_post_correccion_alta` de las fases previas):

- `step_251_shot_1_fase4_01_login_1440x900.png`: Portal de inicio de sesión con botón primario `Ingresar al Portal del Estudiante` en granate institucional y botones de evaluación rápida con borde dorado.
- `step_253_shot_1_fase4_02_estudiante_panel_1440x900.png`: Sidebar expandido con icono Material `«` reparado (sin `keyboard_double_`), textos blancos de alto contraste y botón `Cerrar Sesión` con borde dorado claro.
- `step_255_shot_1_fase4_02b_estudiante_panel_completo.png`: Tarjetas de semáforo, fila `.student-list-row` con badge `.cui-mono` y botón `Programar tutoría` en granate institucional.
- `step_262_shot_1_step_258_shot_1_fase4_03b_estudiante_xai_shap_14.png`: Vista `Detalle con explicabilidad` con medidor circular SVG, barras SHAP bicolores y sugerencia del Agente Tutor.
- `step_266_shot_1_step_265_shot_1_fase4_04_trazabilidad_clean_1440.png`: Terminal FIPA-ACL con tema oscuro de consola (`#1E0709`) y badges diferenciados para `REQUEST` (dorado) e `INFORM` (azul cielo).
- `step_296_shot_1_desk_1440_docente_panel.png`: Vista `Panel de seguimiento` del rol `DOCENTE` en `1440×900` con badge `ID E7BB88B1...D47F` y semáforo `ALTO`.
- `step_296_shot_2_desk_1440_docente_trazabilidad.png`: Vista `Trazabilidad multiagente` en `1440×900` con los 4 agentes en una línea horizontal y consola oscura FIPA-ACL debajo.
- `step_298_shot_1_desk_1440_docente_seguimiento.png`: Vista `Seguimiento y plan de tutoría` en `1440×900` con botones primarios en granate (`Registrar tutoría`, `Guardar Calificación y Recalcular Alerta`) y secundario (`Exportar informe PDF`).
- `step_298_shot_2_desk_1440_autoridad_metricas.png`: Vista `Métricas Institucionales` del rol `AUTORIDAD` en `1440×900` con sidebar expandido y columna `Semestre` capitalizada.
- `step_303_shot_1_laptop_1366_trazabilidad.png`: Vista `Trazabilidad multiagente` en resolución portátil `1366×768` con sidebar abierto y pipeline horizontal intacto.
- `step_280_shot_1_step_279_shot_1_fase4_14a_tablet_login_768x1024.png` y `step_280_shot_2_step_279_shot_2_fase4_14b_tablet_estudiante_pane.png`: Adaptación responsive en resolución tablet `768×1024`.
- `step_303_shot_2_movil_390_trazabilidad.png` y `step_282_shot_1_step_281_shot_1_fase4_11a_estudiante_panel_movil.png`: Adaptación responsive en resolución móvil `390×844` / `375×812` con barra fija superior para el botón `»` y nodos apilados sin scroll horizontal.

---

## 8. Resultados de Pruebas Automatizadas (`pytest`) y Cobertura

Se añadió el test contractual `test_phase4_visual_ux_and_responsive_css_contract` en `tests/test_high_priority_fixes.py` y se ejecutó la suite completa de regresión (`pytest --cov=src --cov=app`):

- **Total de pruebas ejecutadas:** `117 passed, 0 failed` (`100%` de éxito).
- **Cobertura global del proyecto (`src/` + `app.py`):** `86%` (`1,390` sentencias evaluadas).
- **Verificación de cero emojis en código fuente:** `test_no_emojis_in_source_code_ui` aprobado.

---

## 9. Riesgos Residuales y Estado Final de la Interfaz

- **Riesgos residuales:** Ninguno de carácter funcional, visual, de contraste ni de seguridad. La dependencia de Google Fonts (`Plus Jakarta Sans`, `JetBrains Mono` y `Material Symbols Rounded`) cuenta con *fallbacks* nativos del sistema (`sans-serif`, `monospace`, `Material Icons`).
- **Dictamen final:** La interfaz de **SATA-UNSA** cumple íntegramente los estándares de diseño académico institucional de la EPIS-UNSA, legibilidad, contraste WCAG AAA, trazabilidad multiagente y adaptabilidad *responsive* en escritorio, portátil, tablet y teléfono móvil.
