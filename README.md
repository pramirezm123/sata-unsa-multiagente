# Sistema de Alerta Temprana Académica con Sistemas Multiagente, Machine Learning e IA Explicable (SATA-UNSA)

**Tesis de Grado en Ingeniería de Sistemas**  
**Universidad Nacional de San Agustín de Arequipa (UNSA)**  
**Autor:** Paolo Sebastián Ramírez Melendres  
**Asesora:** Dr(a). Eveling Gloria Castro Gutierrez  

---

## 📌 Descripción del Proyecto

El **Sistema de Alerta Temprana Académica (SATA)** es una arquitectura de software inteligente orientada a la **predicción temprana y explicable del riesgo de reprobación académica** en asignaturas universitarias de educación superior.

El sistema supera el tradicional "techo de precisión" de los modelos puramente históricos mediante una **estrategia predictiva en cascada basada en Checkpoints intra-semestrales**:
- **CP0 (Semana 0 - Matrícula):** Predicción basada en antecedentes académicos y perfil de dificultad del docente asignado ($AUC=0.870$, Recall calibrado $\ge 80\%$, obtenido $85.9\%$).
- **CP1 (Semana 6 - Cierre Fase 1):** Insumo de Evaluación Continua 1 (`EC1`) y Examen Parcial 1 (`EP1`). **Reduce las falsas alarmas en $43.36\%$**, elevando la precisión al $27.7\%$ ($AUC=0.931$).
- **CP2 (Semana 12 - Cierre Fase 2):** Insumo acumulado de Fase 1 y 2. **Elimina el $71.28\%$ de las falsas alarmas**, alcanzando una precisión del $42.2\%$ ($AUC=0.954$).
- **CP3 (Semana 16 - Cierre Fase 3):** Evaluación previa a actas finales y examen sustitutorio ($AUC=0.995$, precisión $82.1\%$).

---

## 🤖 Arquitectura Multiagente (SMA)

El sistema está estructurado bajo una **topología jerárquica y desacoplada** de agentes autónomos comunicados mediante un bus de mensajería asíncrono inspirado en el estándar FIPA-ACL (a costo cero y ejecución 100% local):

```
       [ Usuario: Docente / Estudiante / Autoridad ]
                            │
                            ▼
                  ┌───────────────────┐
                  │ Agente Coordinador│
                  └─────────┬─────────┘
                            │
      ┌─────────────────────┼─────────────────────┐
      ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Agente de   │     │  Agente de   │     │   Agente     │
│ Recolección  │────▶│Preprocesam.  │────▶│  Predictor   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                            ┌────────────────────┴───────────────────┐
                            ▼                                        ▼
                     ┌──────────────┐                         ┌──────────────┐
                     │  Agente XAI  │                         │  Agente de   │
                     │ (SHAP / LIME)│                         │Recomendación │
                     └──────┬───────┘                         └──────┬───────┘
                            │                                        │
                            └────────────────────┬───────────────────┘
                                                 │
                                                 ▼
                                        ┌───────────────────┐
                                        │ Agente de Alertas │
                                        │    (Dashboard)    │
                                        └───────────────────┘
```

### Roles de los Agentes:
1. **Agente Coordinador (`CoordinatorAgent`):** Orquesta el ciclo de vida y la secuencia de análisis.
2. **Agente de Recolección (`IngestionAgent`):** Recibe y valida la entrada de datos del estudiante o docente.
3. **Agente de Preprocesamiento (`PreprocessingAgent`):** Valida calificaciones, imputa según reglas oficiales y calcula las variables intra-semestrales exactas (puntos ganados, nota mínima pendiente, tendencias).
4. **Agente Predictor (`PredictorAgent`):** Ejecuta la inferencia en cascada con el ensamble Random Forest del checkpoint activo y aplica el umbral calibrado.
5. **Agente de Explicabilidad (`XaiAgent`):** Descompone la predicción mediante valores SHAP locales, identificando las causas raíz que empujan al riesgo o a la aprobación.
6. **Agente Recomendador (`RecommendationAgent`):** Mapea los factores explicativos a estrategias pedagógicas y metas académicas concretas.
7. **Agente de Alertas (`AlertAgent`):** Clasifica el nivel de riesgo en 4 estados operativos (**Bajo, Medio, Alto y Crítico**) y genera el reporte visual para el usuario.

---

## 🚀 Instalación y Ejecución Local

### 1. Requisitos Previos
- Python 3.10, 3.11 o 3.12 instalado.
- Git instalado.

### 2. Clonar el Repositorio
```bash
git clone https://github.com/pramirezm123/sata-unsa-multiagente.git
cd sata-unsa-multiagente
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Iniciar la Aplicación Multiagente
```bash
streamlit run app.py
```
La aplicación web se abrirá automáticamente en `http://localhost:8501`.

---

## 🛡️ Privacidad y Consideraciones Éticas

En cumplimiento de las normas de ética y confidencialidad universitaria:
- El repositorio de código no contiene registros personales, nombres de estudiantes ni datos confidenciales.
- Los modelos predictivos y prototipos interactivos operan con valores anonimizados mediante códigos hash criptográficos y datos agregados.
