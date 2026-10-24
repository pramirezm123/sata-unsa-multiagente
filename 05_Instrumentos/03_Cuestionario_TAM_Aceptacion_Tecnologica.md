# CUESTIONARIO DE ACEPTACIÓN TECNOLÓGICA (TAM - TECHNOLOGY ACCEPTANCE MODEL)
**Evaluación de Adopción Docente del Sistema SATA-UNSA**  
**Proyecto de Tesis:** Sistema de Alerta Temprana Académica con Arquitectura Multiagente y XAI  
**Investigador:** Paolo Sebastián Ramírez Melendres (UNSA - Escuela Profesional de Ingeniería de Sistemas)  
**Objetivo Específico 5 (OBJ5 - Actividad 3):** Validación empírica de aceptación con docentes y tutores.

---

## 1. Fundamentación Teórica
El Modelo de Aceptación Tecnológica (TAM - Davis, 1989; Venkatesh & Davis, 2000) postula que la adopción efectiva de un sistema informático depende fundamentalmente de dos constructos primarios: la **Utilidad Percibida (PU)** y la **Facilidad de Uso Percibida (PEOU)**.  
Para este estudio de tesis, se incorporan dos dimensiones complementarias requeridas por la naturaleza del sistema: **Confianza en la Explicabilidad (XAI Trust)** y la **Intención de Uso en la Práctica Docente (ITU)**.

---

## 2. Escala de Medición
Cada ítem se califica en una escala Likert de 5 puntos:
1. **Totalmente en desacuerdo (TD)**
2. **En desacuerdo (D)**
3. **Indiferente / Neutral (N)**
4. **De acuerdo (A)**
5. **Totalmente de acuerdo (TA)**

---

## 3. Dimensiones e Ítems del Instrumento

### Dimensión 1: Utilidad Percibida (PU - Perceived Usefulness)
*Mide en qué grado el docente percibe que el sistema mejorará la oportuna identificación de estudiantes en riesgo de reprobación y optimizará su labor tutorial.*

| Código | Ítem | 1 | 2 | 3 | 4 | 5 |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **PU1** | El uso de SATA-UNSA me permitiría identificar estudiantes en riesgo académico con mayor anticipación que mis métodos tradicionales. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PU2** | Disponer de predicciones actualizadas tras cada fase (CP1, CP2, CP3) me ayuda a monitorear la evolución real de mis alumnos. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PU3** | La reducción de falsas alarmas que brinda el sistema (gracias a notas parciales) evita que gaste tiempo en estudiantes que no requieren apoyo. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PU4** | Las recomendaciones automáticas me orientan sobre qué tipo de refuerzo pedagógico o tutorial necesita cada estudiante. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PU5** | Considero que SATA-UNSA es una herramienta útil y de alto valor para la gestión académica del departamento. | [ ] | [ ] | [ ] | [ ] | [ ] |

---

### Dimensión 2: Facilidad de Uso Percibida (PEOU - Perceived Ease of Use)
*Mide en qué medida el docente considera que interactuar con el sistema está libre de esfuerzo cognitivo excesivo.*

| Código | Ítem | 1 | 2 | 3 | 4 | 5 |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **PEOU1**| Aprender a operar e interpretar el dashboard del sistema fue sencillo y directo. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PEOU2**| Considero que la presentación de la información por semáforo de riesgo (Verde, Amarillo, Rojo) es clara y comprensible. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PEOU3**| No me toma un esfuerzo mental indebido entender qué significa la probabilidad de riesgo y la nota mínima proyectada. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **PEOU4**| La navegación entre las pestañas del sistema (Alertas, Casos Clínicos, Multiagente) es intuitiva. | [ ] | [ ] | [ ] | [ ] | [ ] |

---

### Dimensión 3: Confianza y Calidad de la Explicabilidad (XAI Trust & Transparency)
*Mide la credibilidad, coherencia y transparencia que percibe el docente frente a las atribuciones de SHAP y LIME.*

| Código | Ítem | 1 | 2 | 3 | 4 | 5 |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **XAI1** | El desglose de factores (gráfico de cascada SHAP) me permite comprender **por qué** el sistema clasificó al estudiante en alto o bajo riesgo. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **XAI2** | Los factores de riesgo identificados por la IA coinciden con mi criterio pedagógico y mi experiencia como docente en aula. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **XAI3** | Entender las razones detrás de la predicción me genera confianza para fundamentar una intervención tutorial con el estudiante. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **XAI4** | Considero que un sistema con explicaciones (caja transparente) es mucho más confiable que un modelo que solo arroja un porcentaje sin justificación. | [ ] | [ ] | [ ] | [ ] | [ ] |

---

### Dimensión 4: Intención de Uso (ITU - Intention to Use)
*Mide la predisposición actitudinal del docente a utilizar el sistema de forma regular si se implementa en la UNSA.*

| Código | Ítem | 1 | 2 | 3 | 4 | 5 |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **ITU1** | Si el sistema estuviera disponible oficialmente en la UNSA, tengo la intención de consultarlo activamente durante el semestre. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **ITU2** | Recomendaría el uso de SATA-UNSA a otros colegas docentes y directores de escuela. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **ITU3** | Utilizaría los reportes de explicabilidad generados para coordinar intervenciones con el comité de tutoría de la escuela. | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 4. Preguntas Cualitativas Abiertas

1. **¿Qué aspecto de la información proporcionada por el sistema considera más valioso para su labor docente?:**  
   ___________________________________________________________________________________________________  
   ___________________________________________________________________________________________________  

2. **¿Qué factor o dato adicional considera que el modelo debería incluir para entender mejor el riesgo de un alumno?:**  
   ___________________________________________________________________________________________________  
   ___________________________________________________________________________________________________  

3. **Comentarios y sugerencias de mejora:**  
   ___________________________________________________________________________________________________  
   ___________________________________________________________________________________________________  

---

## 5. Análisis Psicométrico Planificado
- **Consistencia Interna:** Alfa de Cronbach ($\alpha$) por cada constructo (Criterio de fiabilidad: $\alpha \ge 0.70$).
- **Estadísticos Descriptivos:** Media ($\mu$) y desviación estándar ($\sigma$) por dimensión.
- **Prueba de Hipótesis:** Prueba no paramétrica de rangos con signo de Wilcoxon frente a la hipótesis nula de neutralidad ($\mu_0 = 3.0$) con nivel de significancia $\alpha = 0.05$.
