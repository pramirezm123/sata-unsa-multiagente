"""
Sistema de Alerta Temprana Académica (SATA-UNSA)
Dashboard Interactivo basado en Sistemas Multiagente, ML y XAI.

Ejecución:
    streamlit run app.py
"""
import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Agregar raíz al path para importar src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.messaging.bus import MessageBus
from src.agents.coordinator_agent import CoordinatorAgent

# Configuración de página
st.set_page_config(
    page_title="SATA-UNSA | Alerta Temprana Multiagente",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar bus y coordinador en session_state
@st.cache_resource
def get_coordinator():
    bus = MessageBus()
    models_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "04_Modelo")
    coordinator = CoordinatorAgent("CoordinatorAgent", bus, models_dir)
    return coordinator

coordinator = get_coordinator()

# Estilos visuales
st.markdown("""
<style>
    .main-title {
        font-size: 28px;
        font-weight: 700;
        color: #1F497D;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 15px;
        color: #555555;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1F497D;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎓 Sistema de Alerta Temprana Académica (SATA-UNSA)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Arquitectura Multiagente con Machine Learning e Inteligencia Artificial Explicable (XAI) | Escuela Profesional de Ingeniería de Sistemas</div>', unsafe_allow_html=True)

# ----------------- SIDEBAR: PARÁMETROS Y PERFILES -----------------
st.sidebar.header("⚙️ Configuración del Estudiante")

preset = st.sidebar.selectbox(
    "Seleccionar Perfil de Demostración:",
    [
        "Ingreso Manual / Personalizado",
        "Caso 1: Alto Riesgo (Análisis de Algoritmos)",
        "Caso 2: Bajo Riesgo (Teoría de la Computación)",
        "Caso 3: Caso Límite (Seguridad Informática)"
    ]
)

# Valores por defecto según preset
if preset == "Caso 1: Alto Riesgo (Análisis de Algoritmos)":
    def_asig = "ANALISIS Y DISENO DE ALGORITMOS"
    def_ira = 10.50
    def_tasa = 0.65
    def_reprob = 2
    def_carga = 6
    def_repeticion = 1
    def_ec1 = 0.0
    def_ep1 = 5.0
    def_ec2 = None
    def_ep2 = None
    def_ec3 = None
    def_ep3 = None
elif preset == "Caso 2: Bajo Riesgo (Teoría de la Computación)":
    def_asig = "TEORIA DE LA COMPUTACION"
    def_ira = 16.32
    def_tasa = 1.00
    def_reprob = 0
    def_carga = 6
    def_repeticion = 0
    def_ec1 = 19.0
    def_ep1 = 18.0
    def_ec2 = None
    def_ep2 = None
    def_ec3 = None
    def_ep3 = None
elif preset == "Caso 3: Caso Límite (Seguridad Informática)":
    def_asig = "SEGURIDAD INFORMATICA"
    def_ira = 12.39
    def_tasa = 0.85
    def_reprob = 1
    def_carga = 6
    def_repeticion = 0
    def_ec1 = 15.0
    def_ep1 = 4.0
    def_ec2 = None
    def_ep2 = None
    def_ec3 = None
    def_ep3 = None
else:
    def_asig = "BASE DE DATOS"
    def_ira = 13.00
    def_tasa = 0.90
    def_reprob = 0
    def_carga = 6
    def_repeticion = 0
    def_ec1 = 12.0
    def_ep1 = 10.0
    def_ec2 = None
    def_ep2 = None
    def_ec3 = None
    def_ep3 = None

st.sidebar.subheader("1. Antecedentes Históricos (CP0)")
asignatura = st.sidebar.text_input("Asignatura:", value=def_asig)
cui = st.sidebar.text_input("CUI (Anonimizado):", value="20220000")
ira_acum = st.sidebar.slider("IRA Acumulado previo (0–20):", 0.0, 20.0, float(def_ira), 0.1)
tasa_aprob = st.sidebar.slider("Tasa histórica de aprobación:", 0.0, 1.0, float(def_tasa), 0.05)
reprob_previas = st.sidebar.number_input("Cursos reprobados previamente:", 0, 15, int(def_reprob))
carga = st.sidebar.number_input("Cursos matriculados en el ciclo:", 1, 10, int(def_carga))
es_repeticion = st.sidebar.selectbox("¿Es repetición de asignatura?", [0, 1], index=int(def_repeticion), format_func=lambda x: "Sí" if x == 1 else "No")

# ----------------- PANEL PRINCIPAL: INGRESO DE NOTAS POR FASES -----------------
st.subheader("📝 Registro de Calificaciones Intra-Semestrales")
st.write("A medida que avanza el ciclo académico, registre las notas de cada fase para que el sistema actualice el nivel de riesgo en cascada.")

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.markdown("### 🔹 Fase 1 (Semanas 1–6)")
    ec1_in = st.text_input("Eval. Continua 1 (EC1):", value="" if def_ec1 is None else str(def_ec1))
    ep1_in = st.text_input("Examen Parcial 1 (EP1):", value="" if def_ep1 is None else str(def_ep1))
    peso_ec1 = st.number_input("Peso EC1 (%):", value=15, min_value=5, max_value=50)
    peso_ep1 = st.number_input("Peso EP1 (%):", value=15, min_value=5, max_value=50)

with col_f2:
    st.markdown("### 🔹 Fase 2 (Semanas 7–12)")
    ec2_in = st.text_input("Eval. Continua 2 (EC2):", value="" if def_ec2 is None else str(def_ec2))
    ep2_in = st.text_input("Examen Parcial 2 (EP2):", value="" if def_ep2 is None else str(def_ep2))
    peso_ec2 = st.number_input("Peso EC2 (%):", value=20, min_value=5, max_value=50)
    peso_ep2 = st.number_input("Peso EP2 (%):", value=20, min_value=5, max_value=50)

with col_f3:
    st.markdown("### 🔹 Fase 3 (Semanas 13–17)")
    ec3_in = st.text_input("Eval. Continua 3 (EC3):", value="" if def_ec3 is None else str(def_ec3))
    ep3_in = st.text_input("Examen Parcial 3 (EP3):", value="" if def_ep3 is None else str(def_ep3))
    peso_ec3 = st.number_input("Peso EC3 (%):", value=15, min_value=5, max_value=50)
    peso_ep3 = st.number_input("Peso EP3 (%):", value=15, min_value=5, max_value=50)

btn_eval = st.button("🚀 Evaluar Riesgo Académico con Arquitectura Multiagente", type="primary", use_container_width=True)

# ----------------- PROCESAMIENTO MULTIAGENTE -----------------
if btn_eval:
    raw_payload = {
        "CUI": cui,
        "ASIGNATURA": asignatura,
        "ASIGNATURA_NORM": asignatura.upper(),
        "IRA_ACUM": ira_acum,
        "TASA_APROB_ACUM": tasa_aprob,
        "REPROBACIONES_PREVIAS": reprob_previas,
        "CARGA_ACADEMICA": carga,
        "ES_REPETICION": es_repeticion,
        "SEMESTRES_DESDE_INGRESO": 4.0,
        "DIFICULTAD_CURSO_HIST": 0.12,
        "DIFICULTAD_DOCENTE_HIST": 0.08,
        "DIFICULTAD_CURSO_DOCENTE_HIST": 0.10,
        "EC1": float(ec1_in) if ec1_in.strip() != "" else None,
        "EP1": float(ep1_in) if ep1_in.strip() != "" else None,
        "EC2": float(ec2_in) if ec2_in.strip() != "" else None,
        "EP2": float(ep2_in) if ep2_in.strip() != "" else None,
        "EC3": float(ec3_in) if ec3_in.strip() != "" else None,
        "EP3": float(ep3_in) if ep3_in.strip() != "" else None,
        "PESO_EC1": peso_ec1, "PESO_EP1": peso_ep1,
        "PESO_EC2": peso_ec2, "PESO_EP2": peso_ep2,
        "PESO_EC3": peso_ec3, "PESO_EP3": peso_ep3,
    }

    with st.spinner("Orquestando agentes (Recolección ➔ Preprocesamiento ➔ Predictor ➔ XAI ➔ Recomendación)..."):
        resultado = coordinator.analyze_student_risk(raw_payload)

    if resultado["status"] == "ERROR":
        st.error("Errores encontrados durante la ingestión: " + ", ".join(resultado["errors"]))
    else:
        alert = resultado["alert"]
        pred = resultado["prediction"]
        prep = resultado["preprocessing"]
        xai = resultado["xai"]
        rec = resultado["recommendation"]

        st.markdown("---")
        # Banner de resultado
        st.markdown(
            f"""
            <div style="background-color: {alert['color']}; padding: 18px; border-radius: 10px; color: white; margin-bottom: 20px;">
                <h2 style="margin: 0; color: white;">{alert['badge']}</h2>
                <p style="margin: 5px 0 0 0; font-size: 16px;">
                    <b>Probabilidad Estimada de Reprobación:</b> {alert['probability_pct']}% &nbsp;|&nbsp; 
                    <b>Umbral de Decisión Calibrado:</b> {alert['threshold_pct']}% &nbsp;|&nbsp;
                    <b>Checkpoint Activo:</b> {alert['checkpoint']}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Métricas de estado
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Checkpoint Activo", alert["checkpoint"], help="CP0: Solo Historial | CP1: +Fase 1 | CP2: +Fase 2 | CP3: +Fase 3")
        m2.metric("Probabilidad de Riesgo", f"{alert['probability_pct']}%", delta=f"{alert['probability_pct'] - alert['threshold_pct']:.1f}% vs umbral", delta_color="inverse")
        
        red_fa = {"CP0": "0.0%", "CP1": "-43.4%", "CP2": "-71.3%", "CP3": "-95.2%"}.get(alert["checkpoint"], "0.0%")
        m3.metric("Reducción Falsas Alarmas", red_fa, help="Reducción respecto al modelo que solo usa historial previo")

        if alert["meta_nota_min"] is not None:
            delta_meta = "⚠️ Imposible en ordinario" if alert["meta_nota_min"] > 20 else f"Meta: {alert['meta_nota_min']}"
            m4.metric("Nota Mínima Requerida", f"{alert['meta_nota_min']:.1f} / 20", delta=delta_meta, delta_color="inverse" if alert["meta_nota_min"] > 14 else "normal")
        else:
            m4.metric("Promedio Ponderado Final", f"{alert['promedio_acumulado']:.2f} / 20")

        # Pestañas de detalle
        tab_xai, tab_rec, tab_agents = st.tabs(["🔍 Explicabilidad XAI (SHAP)", "💡 Recomendaciones Pedagógicas", "🤖 Bitácora de Agentes (SMA)"])

        with tab_xai:
            st.subheader("Factores Clave que Explican la Predicción")
            st.write("El Agente XAI descompone el resultado matemático para mostrar qué factores empujan hacia el riesgo (rojo) o hacia la protección (verde):")
            
            factors = alert.get("top_factors", [])
            if factors:
                df_factors = pd.DataFrame(factors)
                
                # Gráfico horizontal
                fig, ax = plt.subplots(figsize=(9, 4.5))
                colors = ["#D32F2F" if d == "Riesgo" else "#388E3C" for d in df_factors["direction"]]
                y_pos = np.arange(len(df_factors))
                
                ax.barh(y_pos, df_factors["impact"], color=colors, align='center')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(df_factors["label"])
                ax.invert_yaxis()
                ax.set_xlabel("Impacto SHAP en la Probabilidad de Reprobación")
                ax.axvline(0, color='black', linewidth=0.8, linestyle='--')
                plt.tight_layout()
                st.pyplot(fig)

                st.dataframe(
                    df_factors[["label", "value", "direction", "impact"]].rename(
                        columns={"label": "Factor Explicativo", "value": "Valor Observado", "direction": "Efecto", "impact": "Magnitud SHAP"}
                    ),
                    use_container_width=True
                )

        with tab_rec:
            st.subheader("Acciones de Intervención Recomendadas por el Sistema")
            st.write("El Agente Recomendador analiza las causas raíz y genera intervenciones institucionales priorizadas:")
            recs = alert.get("recommendations", [])
            for r_text in recs:
                st.info(r_text)

        with tab_agents:
            st.subheader("Trazabilidad y Mensajería Multiagente (FIPA-ACL)")
            st.write("Bitácora de mensajes intercambiados a través del bus desacoplado durante la ejecución de esta consulta:")
            hist_df = pd.DataFrame(resultado.get("history", []))
            if not hist_df.empty:
                st.dataframe(hist_df, use_container_width=True)
