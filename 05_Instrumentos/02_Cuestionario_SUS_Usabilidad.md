# CUESTIONARIO DE USABILIDAD DEL SISTEMA (SUS - SYSTEM USABILITY SCALE)
**Evaluación de la Plataforma SATA-UNSA**  
**Proyecto de Tesis:** Sistema de Alerta Temprana Académica con Arquitectura Multiagente y XAI  
**Investigador:** Paolo Sebastián Ramírez Melendres (UNSA - Escuela Profesional de Ingeniería de Sistemas)  
**Objetivo Específico 5 (OBJ5 - Actividad 3):** Validación empírica de usabilidad con docentes y tutores.

---

## 1. Instrucciones para el Evaluador
El cuestionario SUS (Brooke, 1996) es un estándar psicométrico internacional compuesto por 10 ítems balanceados que miden la efectividad, eficiencia y satisfacción general con un sistema informático.  
Por favor, responda a cada una de las afirmaciones marcando con una **X** la opción que mejor refleje su opinión tras interactuar con la plataforma interactiva SATA-UNSA. No piense demasiado en cada ítem; su primera reacción suele ser la más certera.

**Escala Likert:**
- **1:** Totalmente en desacuerdo (TD)
- **2:** En desacuerdo (D)
- **3:** Neutral / Ni de acuerdo ni en desacuerdo (N)
- **4:** De acuerdo (A)
- **5:** Totalmente de acuerdo (TA)

---

## 2. Caracterización del Participante (Confidencial y Anonimizado)
- **Código de Participante:** DOC-_____
- **Categoría Docente:** [ ] Ordinario (Principal/Asociado/Auxiliar)  [ ] Contratado  [ ] Jefe de Práctica / Tutor
- **Años de Experiencia Docente Universitaria:** [ ] < 3 años  [ ] 3 - 5 años  [ ] 6 - 10 años  [ ] > 10 años
- **¿Cumple funciones de tutoría universitaria institucional?:** [ ] Sí  [ ] No
- **Nivel de familiaridad previa con herramientas de analítica académica o IA:**  
  [ ] Nulo  [ ] Básico  [ ] Intermedio  [ ] Avanzado

---

## 3. Matriz de Evaluación SUS (10 Ítems Estándar)

| N° | Afirmación | 1 (TD) | 2 (D) | 3 (N) | 4 (A) | 5 (TA) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **1** | Creo que me gustaría utilizar este sistema con frecuencia en el semestre académico. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **2** | Encontré el sistema innecesariamente complejo. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **3** | Pensé que el sistema fue fácil de usar e interactuar. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **4** | Creo que necesitaría el apoyo de un técnico o experto informático para poder utilizar este sistema. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **5** | Encontré que las diversas funciones y agentes del sistema estaban bien integradas. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **6** | Pensé que había demasiada inconsistencia en este sistema. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **7** | Imagino que la mayoría de los docentes y tutores aprenderían a usar este sistema muy rápidamente. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **8** | Encontré el sistema muy engorroso o frustrante de utilizar. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **9** | Me sentí muy seguro y confiado al utilizar el sistema para revisar las alertas de riesgo. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **10**| Necesité aprender muchas cosas antes de poder empezar a interactuar fluidamente con el sistema. | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 4. Metodología de Puntuación e Interpretación Científica

Para obtener el puntaje global de usabilidad $SUS \in [0, 100]$:
1. Para las preguntas impares (1, 3, 5, 7, 9 - formulación positiva):  
   $$\text{Aporte}_i = X_i - 1$$
2. Para las preguntas pares (2, 4, 6, 8, 10 - formulación negativa):  
   $$\text{Aporte}_i = 5 - X_i$$
3. Se suman las 10 contribuciones individuales y se multiplica el total por 2.5:  
   $$Score_{SUS} = \left( \sum_{i=1}^{10} \text{Aporte}_i \right) \times 2.5$$

### Escala de Aceptabilidad (Sauro & Lewis, Bangor et al.):
- **$< 51.0$ puntos:** Usabilidad inaceptable (Riesgo grave de rechazo tecnológico).
- **$51.0 - 67.9$ puntos:** Usabilidad marginal / Aceptable con reservas.
- **$68.0 - 79.9$ puntos:** **Buena usabilidad (Aceptable, umbral estándar de la industria).**
- **$80.0 - 84.9$ puntos:** **Excelente usabilidad (Promotor activo).**
- **$\ge 85.0$ puntos:** Mejor del promedio (Grado 'A+' internacional).

*Criterio de éxito de la tesis:* Promedio muestral de docentes $Score_{SUS} \ge 70.0$ puntos.
