# Protocolo de Validación XAI: Guía de Entrevista Cognitiva con Docentes (OBJ3 Act3)
**Proyecto:** Sistema de Alerta Temprana con Sistemas Multiagente, Machine Learning e Inteligencia Artificial Explicable (XAI)  
**Institución:** Escuela Profesional de Ingeniería de Sistemas — UNSA  
**Investigador:** Paolo Sebastián Ramírez Melendres  
**Asesora:** Dr(a). Eveling Gloria Castro Gutierrez  
**Fecha de Aplicación:** Octubre 2026  

---

## 1. Ficha Técnica y Objetivo de la Actividad

- **Objetivo:** Evaluar la fidelidad percibida, comprensibilidad, utilidad práctica y nivel de confianza de las explicaciones generadas por los módulos XAI (SHAP y LIME) en docentes universitarios de la Escuela Profesional de Ingeniería de Sistemas.
- **Técnica:** Entrevista cognitiva basada en el protocolo *Think-Aloud* (pensamiento en voz alta) y preguntas de sondeo retrospectivo (*cognitive probing*).
- **Muestra objetivo:** 5 a 8 docentes ordinarios/contratados que dicten asignaturas del plan de estudios con distinto perfil de exigencia.
- **Duración estimada:** 30 a 40 minutos por sesión.
- **Material de estímulo:** Tres fichas de estudiantes reales del conjunto de prueba (2024–2025) evaluados en el **Checkpoint 1 (Fase 1)**: Alto Riesgo, Bajo Riesgo y Caso Límite.

---

## 2. Formato de Consentimiento Informado

```
UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA
FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS
ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS

CONSENTIMIENTO INFORMADO PARA DOCENTES PARTICIPANTES

Título de la Investigación:
"Sistema de Alerta Temprana con Machine Learning e Inteligencia Artificial Explicable (XAI) 
basado en una Arquitectura de Sistemas Multiagente para la Predicción del Riesgo Académico"

Investigador: Bach. Paolo Sebastián Ramírez Melendres
Asesora: Dr(a). Eveling Gloria Castro Gutierrez

Estimado(a) docente:
Se le invita a participar en un estudio orientado a evaluar la claridad y utilidad de las explicaciones 
generadas por un sistema inteligente de alerta temprana diseñado para la EPIS-UNSA. Su participación es 
completamente voluntaria y consistirá en una entrevista individual de aproximadamente 35 minutos donde 
revisará tres casos representativos de predicción académica generados por el sistema.

Confidencialidad y Ética:
1. Toda la información recabada se utilizará con fines estrictamente académicos y de investigación para la tesis de grado.
2. Los datos de los estudiantes presentados han sido rigurosamente anonimizados mediante códigos hash criptográficos, 
   garantizando la protección de la privacidad institucional.
3. Sus opiniones y respuestas serán tratadas de manera anónima y agregada.
4. Usted tiene la libertad de interrumpir su participación en cualquier momento sin penalización alguna.

Declaro que he leído la información anterior y acepto participar voluntariamente en la presente entrevista cognitiva.

Nombre del Docente: ____________________________________________________
Firma: _____________________________       Fecha: ______________________
```

---

## 3. Estímulos Visuales: Fichas Clínicas de los 3 Casos Reales (Checkpoint 1)

Cada docente recibirá sucesivamente las siguientes tres fichas generadas en la Fase 1 del semestre:

### Ficha A: Caso de Alto Riesgo
- **Asignatura:** Análisis y Diseño de Algoritmos (Semestre 2024-B)
- **Probabilidad de Reprobación predicha por el sistema:** **$97.29\%$** (Nivel de Riesgo: **CRÍTICO**)
- **Resultado Académico Real:** Reprobó la asignatura.
- **Datos observados en la Fase 1:**
  - `EC1` (Evaluación Continua 1): **0.0** (Condición: **AUSENTE**)
  - `EP1` (Examen Parcial 1): **05.0** (Desaprobado)
  - `PROM_F1` (Promedio ponderado Fase 1): **02.50 / 20**
  - `IRA_ACUM` (Promedio ponderado histórico): **10.50**
  - `NOTA_MIN_PEND_F1`: Requiere promediar **$\ge 13.12$** en todas las evaluaciones restantes para alcanzar nota 11.
- **Factores Explicativos XAI (SHAP):**
  1. $\uparrow$ Ausencia en la Evaluación Continua 1 (+0.28 empuje hacia riesgo).
  2. $\uparrow$ Calificación crítica en Examen Parcial 1 (+0.24).
  3. $\uparrow$ Riesgo histórico previo en materias correlativas (+0.19).
  4. $\uparrow$ Alta dificultad histórica de la asignatura (+0.12).

---

### Ficha B: Caso de Bajo Riesgo
- **Asignatura:** Teoría de la Computación (Semestre 2025-A)
- **Probabilidad de Reprobación predicha por el sistema:** **$0.00\%$** (Nivel de Riesgo: **NULO / SEGURO**)
- **Resultado Académico Real:** Aprobó la asignatura con 18.
- **Datos observados en la Fase 1:**
  - `EC1`: **19.0** (Excelente)
  - `EP1`: **18.0** (Excelente)
  - `PROM_F1`: **18.57 / 20**
  - `IRA_ACUM`: **16.32**
  - `NOTA_MIN_PEND_F1`: Solo requiere promediar **$\ge 06.92$** en lo pendiente para aprobar.
- **Factores Explicativos XAI (SHAP):**
  1. $\downarrow$ Calificaciones sobresalientes en Fase 1 (-0.38 empuje hacia aprobación).
  2. $\downarrow$ Alto rendimiento histórico acumulado previa matrícula (-0.31).
  3. $\downarrow$ Baja exigencia histórica relativa (-0.08).

---

### Ficha C: Caso Límite (Estudiante en Discrepancia)
- **Asignatura:** Seguridad Informática (Semestre 2025-A)
- **Probabilidad de Reprobación predicha por el sistema:** **$33.05\%$** (Umbral de Alerta Temprana: **$0.340$**)
- **Resultado Académico Real:** Aprobó la asignatura con 12.
- **Datos observados en la Fase 1:**
  - `EC1`: **15.0** (Aprobado y regular en entregas)
  - `EP1`: **04.0** (Caída severa en el examen teórico)
  - `PROM_F1`: **10.67 / 20**
  - `IRA_ACUM`: **12.39**
  - `NOTA_MIN_PEND_F1`: Requiere promediar **$\ge 11.16$** en Fase 2 y 3.
- **Factores Explicativos XAI (SHAP):**
  1. $\uparrow$ Nota insuficiente en el Examen Parcial 1 (+0.22 empuje hacia riesgo).
  2. $\downarrow$ Cumplimiento y buena nota en Evaluación Continua 1 (-0.18 hacia aprobación).
  3. $\downarrow$ Historial de superación de cursos en matrícula regular (-0.09).

---

## 4. Guía Semiestructurada de Entrevista (Preguntas de Sondeo)

### Bloque 1: Comprensibilidad de las Explicaciones (Claridad Cognitiva)
1. Al observar los gráficos de barras y valores de impacto (SHAP), ¿le resulta claro qué factores están empujando la predicción hacia el riesgo y cuáles hacia la aprobación?
2. ¿El lenguaje utilizado (términos como "nota mínima requerida", "riesgo previo acumulado", "evaluación continua") coincide con los conceptos que usted utiliza al evaluar el desempeño de un alumno?
3. En la Ficha C (Caso Límite), ¿cómo interpreta que el sistema señale simultáneamente que la continua ayuda pero el examen perjudica? ¿Le parece una explicación intuitiva o confusa?

### Bloque 2: Fidelidad y Confianza Percibida
4. Considerando la información académica de la Fase 1 en el Caso A, ¿coincide su juicio pedagógico con la probabilidad del 97% y el nivel crítico emitido por el modelo?
5. Si el sistema únicamente le dijera *"Riesgo Alto: 97%"* sin mostrar las razones (caja negra), ¿tomaría la misma decisión de intervención que al ver el desglose de los factores?
6. ¿Qué nivel de confianza le inspira saber que dos métodos matemáticos distintos (SHAP y LIME) concuerdan en casi el 78% de las direcciones de los factores explicativos?

### Bloque 3: Utilidad para la Intervención Pedagógica (Accionabilidad)
7. Al saber que en el Caso A el estudiante faltó a la continua y sacó 05 en el examen, ¿qué acción concreta de tutoría activaría usted como docente? (Ej. derivación psicológica, asesoría de conceptos básicos, revisión de inasistencia).
8. ¿Considera que el momento de la Fase 1 (semana 5-6) le da tiempo suficiente para intervenir antes de que el estudiante desapruebe el curso?
9. ¿Qué información adicional le gustaría ver en la pantalla para tomar una decisión más informada?

---

## 5. Matriz de Registro y Plantilla de Análisis Cualitativo

| Ítem / Dimensión | Escala Likert (1: Muy en desacuerdo - 5: Totalmente de acuerdo) | Observaciones Cualitativas y Citas Textuales del Docente |
| :--- | :---: | :--- |
| **D1. Claridad Visual:** Los gráficos y colores comunican intuitivamente el riesgo. | `[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]` | |
| **D2. Comprensibilidad:** Entiendo por qué el sistema asignó esa probabilidad. | `[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]` | |
| **D3. Utilidad Diagnóstica:** La explicación identifica la causa raíz del problema. | `[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]` | |
| **D4. Oportunidad Temporal:** Recibir esta alerta tras la Fase 1 es oportuno. | `[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]` | |
| **D5. Confianza:** Confío más en una alerta explicada que en un porcentaje aislado. | `[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]` | |
| **D6. Disposición de Uso:** Usaría esta herramienta en mis cursos ordinarios. | `[ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]` | |
