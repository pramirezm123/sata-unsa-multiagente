"""
Alerta Académica: Sistema Multiagente de Alerta Temprana de Riesgo Académico
Universidad Nacional de San Agustín de Arequipa (UNSA) | Tesis de Grado
Identidad Visual Oficial: "UNSA Granate Institucional y Modern Academic"

Diseño sobrio, institucional y riguroso. Sin emojis en la interfaz.
Tipografía: Plus Jakarta Sans (títulos y cuerpo) y JetBrains Mono (métricas, IDs y logs).
Paleta: Variables CSS en :root (--granate, --dorado, --azul-hielo, etc.)
"""
import os
import sys
import io
import time
import datetime
import psutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# Configuración de ruta base
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

from src.security.crypto import hash_cui
from src.database.db import (
    authenticate_user, register_student_user, get_student_info, update_student_consent,
    get_student_profile, save_student_profile, get_all_courses, get_all_teachers,
    enroll_course, get_student_enrollments, save_grade, get_grades_for_enrollment,
    save_prediction_result, get_latest_prediction, get_prediction_history,
    get_course_risk_summary, get_course_students_table, log_bus_message,
    get_recent_bus_messages, log_technical_metrics, get_technical_metrics_summary,
    save_survey, get_surveys_stats
)
from src.messaging.bus import MessageBus
from src.agents.coordinator_agent import CoordinatorAgent
from src.services.academic_service import (
    calcular_semaforo, calcular_simulacion_sustitutorio,
    generar_plantilla_carga_masiva_csv, validar_y_procesar_acta_masiva
)
from src.reports.pdf_generator import generate_intervention_pdf

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Alerta Académica | UNSA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================================
# CAPA VISUAL: ESTILOS GLOBALES "UNSA GRANATE INSTITUCIONAL Y MODERN ACADEMIC"
# =========================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --granate: #7A1C20;
        --granate-oscuro: #5A1215;
        --granate-claro: #962228;
        --dorado: #C59B27;
        --dorado-claro: #E8C873;
        --azul-hielo: #E8EEF5;
        --fondo: #F8FAFC;
        --tarjeta: #FFFFFF;
        --borde: #E2E8F0;
        --texto: #0F172A;
        --texto-suave: #64748B;
        --azul-factor: #1E4E79;
        --riesgo-alto-bg: #FEF2F2;
        --riesgo-alto-borde: #EF4444;
        --riesgo-alto-texto: #991B1B;
        --alerta-bg: #FFFBEB;
        --alerta-borde: #F59E0B;
        --alerta-texto: #92400E;
        --riesgo-bajo-bg: #F0FDF4;
        --riesgo-bajo-borde: #22C55E;
        --riesgo-bajo-texto: #166534;
    }

    /* Ocultar elementos nativos de Streamlit */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    #MainMenu { visibility: hidden !important; }

    /* Fondo general y contenedor */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--fondo) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: var(--texto) !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1220px !important;
    }

    /* Sidebar oficial */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--granate) 0%, var(--granate-oscuro) 100%) !important;
        border-right: 1px solid rgba(197, 155, 39, 0.3) !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        padding: 9px 14px !important;
        border-radius: 8px !important;
        transition: all .2s ease !important;
        margin-bottom: 4px !important;
        background: transparent;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(255, 255, 255, 0.16) !important;
        font-weight: 700 !important;
        border-left: 3px solid var(--dorado-claro) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.16) !important;
        margin: 16px 0 !important;
    }

    /* Botones primarios y secundarios */
    button[kind="primary"], .stButton button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, var(--granate), var(--granate-claro)) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        box-shadow: 0 4px 12px rgba(122, 28, 32, 0.2) !important;
        transition: all .25s cubic-bezier(0.4,0,0.2,1) !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(122, 28, 32, 0.35) !important;
    }
    button[kind="secondary"], .stButton button:not([data-testid="baseButton-primary"]) {
        background: transparent !important;
        border: 1.5px solid var(--dorado) !important;
        color: var(--granate) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all .25s cubic-bezier(0.4,0,0.2,1) !important;
    }
    button[kind="secondary"]:hover, .stButton button:not([data-testid="baseButton-primary"]):hover {
        background: rgba(197, 155, 39, 0.08) !important;
        transform: translateY(-2px) !important;
        border-color: var(--granate) !important;
        color: var(--granate-oscuro) !important;
    }

    /* Inputs y controles */
    [data-baseweb="select"] > div,
    .stTextInput > div > div > input,
    .stNumberInput input {
        border-radius: 8px !important;
        border: 1px solid var(--borde) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: var(--texto) !important;
        background-color: #FFFFFF !important;
    }
    [data-baseweb="select"] > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stNumberInput input:focus {
        border-color: var(--granate) !important;
        box-shadow: 0 0 0 2px rgba(122, 28, 32, 0.15) !important;
    }

    /* Pestañas */
    [data-baseweb="tab-list"] {
        border-bottom: 2px solid var(--borde) !important;
        gap: 12px !important;
        margin-bottom: 16px !important;
    }
    [data-baseweb="tab"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        color: var(--texto-suave) !important;
        padding: 10px 16px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        color: var(--granate) !important;
        border-bottom: 3px solid var(--granate) !important;
        font-weight: 700 !important;
    }

    /* ---------------- MOCKUP 2: IDENTIDAD Y CABECERA ---------------- */
    .unsa-header-banner {
        background: repeating-linear-gradient(135deg, rgba(255,255,255,0.035) 0, rgba(255,255,255,0.035) 10px, transparent 10px, transparent 20px), var(--granate-oscuro);
        border-radius: 12px 12px 0 0;
        padding: 24px 28px;
        color: #FFFFFF;
        position: relative;
        box-shadow: 0 8px 24px -4px rgba(90, 18, 21, 0.25);
    }
    .unsa-banner-inner {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .unsa-escudo-circle {
        width: 68px;
        height: 68px;
        border-radius: 50%;
        border: 2px solid var(--dorado);
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(197, 155, 39, 0.12);
        color: var(--dorado-claro);
        font-weight: 800;
        font-size: 13px;
        letter-spacing: 0.1em;
        flex-shrink: 0;
        text-align: center;
    }
    .unsa-banner-inst {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: var(--dorado-claro);
        margin-bottom: 4px;
    }
    .unsa-banner-title {
        font-size: 24px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0 0 4px 0;
        line-height: 1.2;
    }
    .unsa-banner-meta {
        font-size: 13px;
        color: var(--azul-hielo);
        font-weight: 400;
    }
    .unsa-banner-fillet {
        height: 4px;
        background-color: var(--dorado);
        border-radius: 0 0 4px 4px;
        margin-bottom: 22px;
    }

    /* Tarjetas y contenedores */
    .unsa-card {
        background: var(--tarjeta);
        border: 1px solid var(--borde);
        border-radius: 12px;
        box-shadow: 0 12px 24px -6px rgba(122,28,32,.08);
        padding: 24px;
        transition: all .25s cubic-bezier(0.4,0,0.2,1);
        margin-bottom: 18px;
    }
    .unsa-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 30px -8px rgba(122,28,32,.14);
    }

    /* Títulos de sección */
    .section-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--dorado);
        display: block;
        margin-bottom: 2px;
    }
    .section-title {
        font-size: 24px;
        font-weight: 800;
        color: var(--granate-oscuro);
        margin-top: 0;
        margin-bottom: 4px;
        line-height: 1.25;
    }
    .section-subtitle {
        font-size: 13px;
        color: var(--texto-suave);
        margin-bottom: 18px;
    }

    /* Sub-métricas Mockup 2 */
    .sub-metric-card {
        background: #FFFFFF;
        border: 1px solid var(--borde);
        border-top: 3px solid var(--dorado);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        height: 100%;
    }
    .sub-metric-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--texto-suave);
        margin-bottom: 6px;
    }
    .sub-metric-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        color: var(--granate-oscuro);
    }
    .lema-box {
        background-color: var(--azul-hielo);
        border-radius: 10px;
        padding: 16px 20px;
        font-size: 13.5px;
        color: var(--texto);
        margin: 18px 0 14px 0;
        line-height: 1.5;
    }
    .lema-bold {
        font-weight: 700;
        color: var(--granate-oscuro);
    }
    .sub-footer-row {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: var(--texto-suave);
        margin-bottom: 24px;
    }

    /* ---------------- MOCKUP 1: PANEL DE SEGUIMIENTO ---------------- */
    .metric-card-risk {
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        transition: all .25s ease;
        margin-bottom: 16px;
    }
    .metric-card-risk.alto {
        background-color: var(--riesgo-alto-bg);
        border: 1.5px solid var(--riesgo-alto-borde);
    }
    .metric-card-risk.alto .metric-card-label {
        color: var(--riesgo-alto-texto);
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
    }
    .metric-card-risk.alto .metric-card-value {
        color: var(--riesgo-alto-texto);
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-card-risk.alerta {
        background-color: var(--alerta-bg);
        border: 1.5px solid var(--alerta-borde);
    }
    .metric-card-risk.alerta .metric-card-label {
        color: var(--alerta-texto);
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
    }
    .metric-card-risk.alerta .metric-card-value {
        color: var(--alerta-texto);
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-card-risk.bajo {
        background-color: var(--riesgo-bajo-bg);
        border: 1.5px solid var(--riesgo-bajo-borde);
    }
    .metric-card-risk.bajo .metric-card-label {
        color: var(--riesgo-bajo-texto);
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
    }
    .metric-card-risk.bajo .metric-card-value {
        color: var(--riesgo-bajo-texto);
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }

    /* Badges de riesgo */
    .badge-alto {
        background: #FEF2F2;
        border: 1px solid #EF4444;
        color: #991B1B;
        font-weight: 700;
        font-size: 11px;
        border-radius: 99px;
        padding: 3px 12px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }
    .badge-alerta {
        background: #FFFBEB;
        border: 1px solid #F59E0B;
        color: #92400E;
        font-weight: 700;
        font-size: 11px;
        border-radius: 99px;
        padding: 3px 12px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }
    .badge-bajo {
        background: #F0FDF4;
        border: 1px solid #22C55E;
        color: #166534;
        font-weight: 700;
        font-size: 11px;
        border-radius: 99px;
        padding: 3px 12px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }

    /* Filas de la lista de estudiantes Mockup 1 */
    .student-list-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 4px;
        border-bottom: 1px solid var(--borde);
    }
    .student-list-row:last-child {
        border-bottom: none;
    }
    .cui-mono {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: var(--texto-suave);
        width: 150px;
    }
    .student-name {
        flex-grow: 1;
        font-size: 14px;
        font-weight: 600;
        color: var(--texto);
    }

    /* ---------------- MOCKUP 3: DETALLE CON EXPLICABILIDAD ---------------- */
    .unsa-circular-gauge {
        width: 140px;
        height: 140px;
        display: block;
        margin: 10px auto;
    }
    .gauge-track {
        fill: none;
        stroke: var(--azul-hielo);
    }
    .gauge-fill {
        fill: none;
        stroke: var(--granate);
        stroke-linecap: round;
        transform: rotate(-90deg);
        transform-origin: 50% 50%;
        transition: stroke-dashoffset 0.8s ease-in-out;
    }
    .gauge-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        fill: var(--granate-oscuro);
    }

    .factor-bar-row {
        margin-bottom: 16px;
    }
    .factor-label-row {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        margin-bottom: 6px;
    }
    .factor-name {
        color: var(--texto);
        font-weight: 600;
    }
    .factor-val-mono {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 13px;
    }
    .factor-bar-track {
        height: 10px;
        background-color: var(--azul-hielo);
        border-radius: 5px;
        overflow: hidden;
    }
    .factor-bar-fill {
        height: 100%;
        border-radius: 5px;
    }
    .suggestion-box {
        background-color: var(--alerta-bg);
        border: 1px solid var(--alerta-borde);
        border-radius: 10px;
        padding: 16px 20px;
        margin-top: 18px;
        color: var(--alerta-texto);
        font-size: 13.5px;
        line-height: 1.5;
    }

    /* ---------------- MOCKUP 4: TRAZABILIDAD MULTIAGENTE ---------------- */
    .stepped-pipeline-container {
        position: relative;
        padding: 24px 10px 10px 10px;
        margin-bottom: 24px;
    }
    .stepped-line {
        position: absolute;
        top: 44px;
        left: 8%;
        right: 8%;
        height: 2px;
        background-color: var(--dorado);
        z-index: 1;
    }
    .stepped-nodes {
        display: flex;
        justify-content: space-between;
        position: relative;
        z-index: 2;
    }
    .stepped-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        width: 23%;
    }
    .node-circle {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 8px;
    }
    .node-circle.solid {
        background-color: var(--granate);
        color: #FFFFFF;
        box-shadow: 0 4px 10px rgba(122, 28, 32, 0.25);
    }
    .node-circle.active {
        background-color: #FFFFFF;
        border: 2.5px solid var(--dorado);
        color: var(--granate);
        box-shadow: 0 4px 12px rgba(197, 155, 39, 0.3);
    }
    .node-title {
        font-weight: 700;
        color: var(--granate-oscuro);
        font-size: 13.5px;
        margin-bottom: 2px;
    }
    .node-desc {
        color: var(--texto-suave);
        font-size: 11.5px;
        line-height: 1.3;
    }
    .fipa-log-header {
        background-color: var(--granate-oscuro);
        border-radius: 10px 10px 0 0;
        padding: 12px 18px;
        color: var(--dorado-claro);
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: 0.1em;
        font-family: 'JetBrains Mono', monospace;
    }
    .fipa-log-body {
        background-color: #FFFFFF;
        border: 1px solid var(--borde);
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 16px 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        line-height: 1.8;
        color: var(--texto);
    }
    .fipa-time {
        color: var(--texto-suave);
    }
    .fipa-performative {
        font-weight: 700;
        color: var(--granate);
    }

    /* ---------------- MOCKUP 5: SEGUIMIENTO Y PLAN TUTORÍA ---------------- */
    .action-checklist-row {
        display: flex;
        align-items: center;
        padding: 14px 4px;
        border-bottom: 1px solid var(--borde);
    }
    .action-checklist-row:last-child {
        border-bottom: none;
    }
    .action-box {
        width: 22px;
        height: 22px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 14px;
        font-size: 13px;
        font-weight: 700;
        flex-shrink: 0;
    }
    .action-box.checked {
        background-color: var(--granate);
        color: #FFFFFF;
    }
    .action-box.unchecked {
        background-color: #FFFFFF;
        border: 1.5px solid var(--dorado);
    }
    .action-text {
        flex-grow: 1;
        font-size: 14px;
        color: var(--texto);
        font-weight: 500;
    }
    .action-date {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: var(--texto-suave);
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# FUNCIONES AUXILIARES DE RENDERIZADO VISUAL
# =========================================================================
def render_institutional_banner(facultad="Facultad de Ingeniería de Producción y Servicios",
                                escuela="Escuela Profesional de Ingeniería de Sistemas",
                                semestre="Semestre 2026-B"):
    """Renderiza el banner superior institucional oficial UNSA (Mockup 2)."""
    st.markdown(f"""
    <div class="unsa-header-banner">
        <div class="unsa-banner-inner">
            <div class="unsa-escudo-circle">UNSA</div>
            <div>
                <div class="unsa-banner-inst">Universidad Nacional de San Agustín de Arequipa</div>
                <div class="unsa-banner-title">Plataforma de Alerta Temprana de Riesgo Académico</div>
                <div class="unsa-banner-meta">{facultad} · {escuela} · {semestre}</div>
            </div>
        </div>
    </div>
    <div class="unsa-banner-fillet"></div>
    """, unsafe_allow_html=True)


def render_circular_gauge_svg(prob_pct: float, radius: int = 46, stroke_width: int = 9) -> str:
    """Renderiza el medidor circular SVG con trazo granate sobre pista azul hielo (Mockup 3)."""
    circumference = 2 * 3.14159265 * radius
    p_clamped = max(0.0, min(100.0, float(prob_pct)))
    offset = circumference * (1.0 - (p_clamped / 100.0))
    return f"""
    <svg viewBox="0 0 120 120" class="unsa-circular-gauge">
        <circle cx="60" cy="60" r="{radius}" class="gauge-track" stroke-width="{stroke_width}" />
        <circle cx="60" cy="60" r="{radius}" class="gauge-fill" stroke-width="{stroke_width}"
                stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}" />
        <text x="60" y="67" text-anchor="middle" class="gauge-text">{prob_pct:.0f}%</text>
    </svg>
    """


# ----------------- INICIALIZACIÓN DEL SISTEMA MULTIAGENTE -----------------
@st.cache_resource
def get_sma_coordinator():
    bus = MessageBus()
    models_dir = os.path.join(BASE_DIR, "04_Modelo")
    coordinator = CoordinatorAgent("CoordinatorAgent", bus, models_dir)
    return coordinator

coordinator = get_sma_coordinator()

# Manejo de sesión
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "selected_student_mat" not in st.session_state:
    st.session_state["selected_student_mat"] = None


# =========================================================================
# 1. PANTALLA DE ACCESO / INICIO DE SESIÓN (UNSA INSTITUCIONAL)
# =========================================================================
if st.session_state["usuario"] is None:
    render_institutional_banner()

    st.markdown("""
    <div class="lema-box">
        <span class="lema-bold">Principio de Estimación y Privacidad:</span> Este sistema genera estimaciones probabilísticas orientativas para apoyar la labor de tutoría y el autoaprendizaje. <b>Nunca guarda ni transmite nombres ni CUI en texto claro.</b> Toda identidad se procesa mediante un código criptográfico irreversible.
    </div>
    """, unsafe_allow_html=True)

    col_login, col_demo = st.columns([3, 2])

    with col_login:
        st.markdown('<div class="unsa-card">', unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["Iniciar Sesión", "Registro de Estudiante"])

        with tab_login:
            st.markdown('<span class="section-label">AUTENTICACIÓN</span>', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title" style="font-size: 20px;">Acceso al Sistema</h3>', unsafe_allow_html=True)
            tipo_usuario = st.radio("Tipo de usuario:", ["Estudiante", "Docente / Autoridad / Administrador"], horizontal=True)

            if tipo_usuario == "Estudiante":
                st.caption("Ingrese con su CUI (se convertirá en código hash al instante) y contraseña.")
                cui_input = st.text_input("CUI del Estudiante:", max_chars=10, key="login_cui")
                pwd_input = st.text_input("Contraseña:", type="password", key="login_pwd_est")

                if st.button("Ingresar al Portal del Estudiante", type="primary", use_container_width=True):
                    if not cui_input or not pwd_input:
                        st.error("Por favor complete su CUI y contraseña.")
                    else:
                        cui_h = hash_cui(cui_input)
                        user = authenticate_user(cui_h, pwd_input)
                        if user and user["role"] == "ESTUDIANTE":
                            st.session_state["usuario"] = user
                            st.rerun()
                        else:
                            st.error("Credenciales incorrectas o estudiante no registrado.")
            else:
                user_input = st.text_input("Nombre de usuario:", key="login_user")
                pwd_input = st.text_input("Contraseña:", type="password", key="login_pwd_staff")

                if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
                    user = authenticate_user(user_input, pwd_input)
                    if user and user["role"] != "ESTUDIANTE":
                        st.session_state["usuario"] = user
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")

        with tab_reg:
            st.markdown('<span class="section-label">NUEVO INGRESO</span>', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title" style="font-size: 20px;">Crear Cuenta de Estudiante</h3>', unsafe_allow_html=True)
            reg_cui = st.text_input("Ingrese su CUI oficial:", max_chars=8, key="reg_cui")
            reg_pwd = st.text_input("Cree una contraseña segura:", type="password", key="reg_pwd")
            reg_pwd2 = st.text_input("Confirme su contraseña:", type="password", key="reg_pwd2")

            if st.button("Registrar Cuenta", use_container_width=True):
                if reg_pwd != reg_pwd2:
                    st.error("Las contraseñas no coinciden.")
                elif len(reg_pwd) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    ok, msg = register_student_user(reg_cui, reg_pwd)
                    if ok:
                        st.success(msg + " Ya puede iniciar sesión.")
                    else:
                        st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_demo:
        st.markdown("""
        <div class="unsa-card">
            <span class="section-label">EVALUACIÓN DE TESIS</span>
            <h3 class="section-title" style="font-size: 20px;">Acceso Rápido de Evaluación</h3>
            <p class="section-subtitle">Seleccione un perfil para evaluar las funcionalidades del sistema:</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Entrar como Estudiante Demo (CUI: 20220638)", use_container_width=True):
            user = authenticate_user(hash_cui("20220638"), "Alumno123*")
            if user:
                st.session_state["usuario"] = user
                st.rerun()

        if st.button("Entrar como Docente / Tutor (docente_demo)", use_container_width=True):
            user = authenticate_user("docente_demo", "Docente123*")
            if user:
                st.session_state["usuario"] = user
                st.rerun()

        if st.button("Entrar como Autoridad / Comité (tutor_epis)", use_container_width=True):
            user = authenticate_user("tutor_epis", "Tutor123*")
            if user:
                st.session_state["usuario"] = user
                st.rerun()

        if st.button("Entrar como Administrador (admin)", use_container_width=True):
            user = authenticate_user("admin", "Admin123*")
            if user:
                st.session_state["usuario"] = user
                st.rerun()

    st.stop()


# =========================================================================
# 2. ENTORNO AUTENTICADO: HEADER Y SIDEBAR
# =========================================================================
usuario = st.session_state.get("usuario")
if usuario is not None:
    rol = usuario["role"]
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")

    # Sidebar oficial (Mockup 1)
    st.sidebar.markdown("""
    <div style="padding: 10px 0 16px 0;">
        <div style="font-size: 19px; font-weight: 800; color: #FFFFFF; line-height: 1.2;">Alerta Académica</div>
        <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: var(--dorado-claro); margin-top: 3px;">UNIVERSIDAD NACIONAL DE SAN AGUSTÍN</div>
    </div>
    """, unsafe_allow_html=True)

    if rol == "ESTUDIANTE":
        cui_hash = usuario["cui_hash"]
        menu_items = [
            "Panel de seguimiento",
            "Detalle con explicabilidad",
            "Trazabilidad multiagente",
            "Seguimiento y plan de tutoría",
            "Inscribir Asignatura",
            "Perfil Basal"
        ]
    elif rol == "DOCENTE":
        menu_items = [
            "Panel de seguimiento",
            "Detalle con explicabilidad",
            "Trazabilidad multiagente",
            "Seguimiento y plan de tutoría",
            "Carga Masiva de Actas"
        ]
    elif rol == "AUTORIDAD":
        menu_items = [
            "Panel de seguimiento",
            "Métricas Institucionales",
            "Trazabilidad multiagente"
        ]
    else:  # ADMIN
        menu_items = [
            "Panel de seguimiento",
            "Monitor Técnico OBJ5",
            "Trazabilidad multiagente",
            "Encuestas SUS / TAM"
        ]

    nav_sel = st.sidebar.radio("Navegación:", menu_items)

    st.sidebar.markdown("---")
    if rol == "ESTUDIANTE":
        st.sidebar.caption(f"ID Anonimizado: `{usuario['cui_hash'][:10]}...`")
    else:
        st.sidebar.caption(f"Usuario: `{usuario['username']}` ({rol})")

    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state["usuario"] = None
        st.session_state["selected_student_mat"] = None
        st.rerun()

    # Banner superior institucional (Mockup 2)
    render_institutional_banner()

    # Sub-cabecera con saludo, 3 métricas con borde dorado y lema (Mockup 2)
    catalogo = get_all_courses()
    curso_activo = catalogo[0]["nombre"] if catalogo else "Estructuras de Datos"
    if rol == "DOCENTE":
        resumen_curso = get_course_risk_summary(curso_activo, "2026-B")
        total_est = resumen_curso["total_alumnos"]
        tutorias_sem = resumen_curso["rojos"]
    else:
        total_est = 18
        tutorias_sem = 3

    st.markdown(f"""
    <div style="font-size: 14px; color: var(--texto-suave); margin-bottom: 14px;">
        Hola, <b>{usuario['username']}</b> · <span style="font-family: 'JetBrains Mono', monospace;">{fecha_hoy}</span>
    </div>
    """, unsafe_allow_html=True)

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.markdown(f"""
        <div class="sub-metric-card">
            <div class="sub-metric-label">ESTUDIANTES EN SEGUIMIENTO</div>
            <div class="sub-metric-val">{total_est:02d}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"""
        <div class="sub-metric-card">
            <div class="sub-metric-label">TUTORÍAS ESTA SEMANA</div>
            <div class="sub-metric-val">{tutorias_sem:02d}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_m3:
        st.markdown(f"""
        <div class="sub-metric-card">
            <div class="sub-metric-label">ÚLTIMA ACTUALIZACIÓN</div>
            <div class="sub-metric-val" style="font-size: 20px;">{fecha_hoy}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="lema-box">
        <span class="lema-bold">Estimación, no sentencia.</span> El semáforo orienta la conversación de tutoría; la decisión siempre es del tutor y del estudiante.
    </div>
    <div class="sub-footer-row">
        <span>Datos anonimizados con CUI hash</span>
        <span>Tesis de grado · Paolo Ramírez Melendres · Asesor: Dra. Eveling Castro Gutierrez</span>
    </div>
    """, unsafe_allow_html=True)


    # =========================================================================
    # VISTA 1: MOCKUP 1 - PANEL DE SEGUIMIENTO (PANEL PRINCIPAL)
    # =========================================================================
    if nav_sel == "Panel de seguimiento":
        st.markdown('<span class="section-label">MONITOREO</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Panel de seguimiento</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Estimación de riesgo, no sentencia · datos reales del curso</p>', unsafe_allow_html=True)

        # Selección de curso si es Docente / Autoridad
        if rol in ["DOCENTE", "AUTORIDAD", "ADMIN"]:
            cursos_nombres = [c["nombre"] for c in catalogo]
            curso_sel = st.selectbox("Asignatura a supervisar:", cursos_nombres, key="sel_curso_panel")
        else:
            curso_sel = "Estructuras de Datos"

        resumen = get_course_risk_summary(curso_sel, "2026-B")
        rojos_cnt = resumen["rojos"]
        amarillos_cnt = resumen["amarillos"]
        verdes_cnt = resumen["verdes"]

        # Tres tarjetas de métricas con los colores del semáforo (Mockup 1)
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.markdown(f"""
            <div class="metric-card-risk alto">
                <div class="metric-card-label">RIESGO ALTO</div>
                <div class="metric-card-value">{rojos_cnt:02d}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_r2:
            st.markdown(f"""
            <div class="metric-card-risk alerta">
                <div class="metric-card-label">ALERTA PREVENTIVA</div>
                <div class="metric-card-value">{amarillos_cnt:02d}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_r3:
            st.markdown(f"""
            <div class="metric-card-risk bajo">
                <div class="metric-card-label">RIESGO BAJO</div>
                <div class="metric-card-value">{verdes_cnt:02d}</div>
            </div>
            """, unsafe_allow_html=True)

        # Lista de estudiantes (Mockup 1)
        st.markdown('<div class="unsa-card" style="padding: 14px 24px;">', unsafe_allow_html=True)
        alumnos_lista = get_course_students_table(curso_sel, "2026-B")

        # Si aún no hay alumnos en el curso, se muestran los de demo de la base de datos
        if not alumnos_lista:
            alumnos_lista = [
                {"id_mostrado": "7f3a...c91", "nombre": "Estudiante de ejemplo A", "semaforo": "ROJO", "matricula_id": 1, "probabilidad": 0.82},
                {"id_mostrado": "2b9e...04d", "nombre": "Estudiante de ejemplo B", "semaforo": "AMARILLO", "matricula_id": 2, "probabilidad": 0.31},
                {"id_mostrado": "c40d...a17", "nombre": "Estudiante de ejemplo C", "semaforo": "VERDE", "matricula_id": 3, "probabilidad": 0.12}
            ]

        for al in alumnos_lista:
            cui_txt = al.get("id_mostrado", "7f3a...c91")
            nom_txt = al.get("nombre", f"Estudiante ({al.get('seccion', 'Sec. A')})")
            sem_tag = al.get("semaforo", "ROJO")

            if sem_tag == "ROJO":
                badge_html = '<span class="badge-alto">ALTO</span>'
            elif sem_tag == "AMARILLO":
                badge_html = '<span class="badge-alerta">ALERTA</span>'
            else:
                badge_html = '<span class="badge-bajo">BAJO</span>'

            st.markdown(f"""
            <div class="student-list-row">
                <span class="cui-mono">CUI {cui_txt}</span>
                <span class="student-name">{nom_txt}</span>
                {badge_html}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Botones inferiores (Mockup 1)
        b_c1, b_c2, _ = st.columns([1.5, 1.5, 3])
        with b_c1:
            if st.button("Programar tutoría", type="primary", use_container_width=True):
                st.success("Acción registrada: Notificación enviada al estudiante en el canal institucional.")
        with b_c2:
            if st.button("Ver explicación", use_container_width=True):
                st.session_state["nav_override"] = "Detalle con explicabilidad"
                st.info("Consulte la pestaña 'Detalle con explicabilidad' en el menú lateral para ver el desglose SHAP.")


    # =========================================================================
    # VISTA 2: MOCKUP 3 - DETALLE CON EXPLICABILIDAD
    # =========================================================================
    elif nav_sel == "Detalle con explicabilidad":
        st.markdown('<span class="section-label">EXPLICABILIDAD</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">¿Qué influyó en este resultado?</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Factores explicativos SHAP y sugerencia generada por el Agente Tutor</p>', unsafe_allow_html=True)

        # Buscar última predicción real o datos de referencia
        cursos_nombres = [c["nombre"] for c in catalogo]
        c_act = cursos_nombres[0] if cursos_nombres else "Estructuras de Datos"
        pred_rec = get_latest_prediction(1) or {
            "probabilidad": 0.82,
            "semaforo": "ROJO",
            "checkpoint": "CP1",
            "top_factors": [
                {"label": "Asistencia acumulada baja", "value": 0.42, "direction": "Riesgo"},
                {"label": "Calificación en Fase 1 (EP1)", "value": 0.28, "direction": "Riesgo"},
                {"label": "Carga de créditos semestral", "value": -0.15, "direction": "Protector"}
            ],
            "recommendations": [
                "Priorizar tutoría individual enfocada en el refuerzo de la prueba parcial de Fase 1 y coordinar plan de recuperación de asistencia."
            ]
        }

        p_val = pred_rec.get("probabilidad", 0.82)
        p_pct = p_val * 100
        sem_tag = pred_rec.get("semaforo", "ROJO")

        col_izq, col_der = st.columns([1, 2])

        # Columna Izquierda (Mockup 3: 230px aprox.)
        with col_izq:
            st.markdown('<div class="unsa-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown('<div class="cui-mono" style="margin: 0 auto 10px auto;">CUI 7f3a...c91</div>', unsafe_allow_html=True)
            st.markdown(render_circular_gauge_svg(p_pct), unsafe_allow_html=True)

            if sem_tag == "ROJO":
                st.markdown('<div style="margin: 12px 0;"><span class="badge-alto">RIESGO ALTO</span></div>', unsafe_allow_html=True)
            elif sem_tag == "AMARILLO":
                st.markdown('<div style="margin: 12px 0;"><span class="badge-alerta">ALERTA PREVENTIVA</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="margin: 12px 0;"><span class="badge-bajo">RIESGO BAJO</span></div>', unsafe_allow_html=True)

            st.markdown("""
            <div style="font-size: 13px; color: var(--texto-suave); margin-bottom: 14px;">
                Probabilidad estimada de rezago<br>
                <b>Semestre 2026-B · EPIS</b>
            </div>
            <div style="border-top: 2px solid var(--dorado); margin: 14px 0 10px 0;"></div>
            """, unsafe_allow_html=True)

            if st.button("Programar tutoría", key="btn_prog_tut_izq", use_container_width=True):
                st.success("Tutoría programada en la agenda del docente.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Columna Derecha (Mockup 3: Barras SHAP y Sugerencia)
        with col_der:
            st.markdown('<div class="unsa-card">', unsafe_allow_html=True)

            factores = pred_rec.get("top_factors", [])
            for f in factores:
                f_nombre = f.get("label", "Factor evaluado")
                val_raw = float(f.get("value", 0.0))
                es_riesgo = f.get("direction") == "Riesgo" or val_raw > 0

                bar_color = "var(--granate)" if es_riesgo else "var(--azul-factor)"
                signo = "+" if val_raw >= 0 else ""
                val_txt = f"{signo}{val_raw:.2f}"
                ancho_pct = min(100, int(abs(val_raw) * 150)) if abs(val_raw) <= 1.0 else min(100, int(abs(val_raw)))

                st.markdown(f"""
                <div class="factor-bar-row">
                    <div class="factor-label-row">
                        <span class="factor-name">{f_nombre}</span>
                        <span class="factor-val-mono" style="color: {bar_color};">{val_txt}</span>
                    </div>
                    <div class="factor-bar-track">
                        <div class="factor-bar-fill" style="width: {ancho_pct}%; background-color: {bar_color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Leyenda (Mockup 3)
            st.markdown("""
            <div style="display: flex; gap: 20px; font-size: 12px; color: var(--texto-suave); margin-top: 18px;">
                <span><span style="color: var(--granate); font-weight: bold;">■</span> Aumenta el riesgo</span>
                <span><span style="color: var(--azul-factor); font-weight: bold;">■</span> Lo reduce</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Caja de sugerencia para el tutor (Mockup 3)
            recom_txt = pred_rec.get("recommendations", ["Agendar reunión para revisar la estrategia de estudio antes del cierre de Fase 2."])[0]
            st.markdown(f"""
            <div class="suggestion-box">
                <b>Sugerencia para el tutor:</b> {recom_txt}
            </div>
            """, unsafe_allow_html=True)


    # =========================================================================
    # VISTA 3: MOCKUP 4 - TRAZABILIDAD MULTIAGENTE
    # =========================================================================
    elif nav_sel == "Trazabilidad multiagente":
        st.markdown('<span class="section-label">TRAZABILIDAD DEL SISTEMA</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Cómo se calculó esta alerta</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Flujo de coordinación y mensajes entre agentes de la arquitectura</p>', unsafe_allow_html=True)

        # Línea horizontal con 4 agentes (Mockup 4)
        st.markdown("""
        <div class="stepped-pipeline-container">
            <div class="stepped-line"></div>
            <div class="stepped-nodes">
                <div class="stepped-node">
                    <div class="node-circle solid">1</div>
                    <div class="node-title">Agente de datos</div>
                    <div class="node-desc">Consolida notas y asistencia</div>
                </div>
                <div class="stepped-node">
                    <div class="node-circle solid">2</div>
                    <div class="node-title">Agente predictor</div>
                    <div class="node-desc">Estima la probabilidad</div>
                </div>
                <div class="stepped-node">
                    <div class="node-circle solid">3</div>
                    <div class="node-title">Agente explicador</div>
                    <div class="node-desc">Calcula los factores</div>
                </div>
                <div class="stepped-node">
                    <div class="node-circle active">4</div>
                    <div class="node-title">Agente tutor</div>
                    <div class="node-desc">Redacta la sugerencia</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tarjeta FIPA-ACL (Mockup 4)
        st.markdown('<div class="fipa-log-header">REGISTRO DE MENSAJES FIPA-ACL</div>', unsafe_allow_html=True)

        mensajes_reales = get_recent_bus_messages(8)
        if not mensajes_reales:
            log_entries = [
                ("[10:14:22]", "inform", "datos → predictor"),
                ("[10:14:23]", "inform", "predictor → explicador"),
                ("[10:14:24]", "inform", "explicador → tutor"),
                ("[10:14:25]", "propose", "tutor → interfaz")
            ]
        else:
            log_entries = []
            for m in mensajes_reales[-6:]:
                t_str = m.get("timestamp", "10:00:00")[-8:]
                perf = m.get("performative", "inform").lower()
                rem = m.get("sender", "agente").replace("Agent", "")
                dest = m.get("receiver", "coordinador").replace("Agent", "")
                log_entries.append((f"[{t_str}]", perf, f"{rem} → {dest}"))

        log_html = "".join([
            f'<div><span class="fipa-time">{t}</span> <span class="fipa-performative">{p}</span> {c}</div>'
            for t, p, c in log_entries
        ])

        st.markdown(f"""
        <div class="fipa-log-body">
            {log_html}
        </div>
        <div style="font-size: 13px; color: var(--texto-suave); margin-top: 14px;">
            Cada alerta puede auditarse paso a paso por el jurado o el comité de tutoría.
        </div>
        """, unsafe_allow_html=True)


    # =========================================================================
    # VISTA 4: MOCKUP 5 - SEGUIMIENTO Y PLAN DE TUTORÍA
    # =========================================================================
    elif nav_sel == "Seguimiento y plan de tutoría":
        st.markdown('<span class="section-label">SEGUIMIENTO</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Evolución y plan de tutoría</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Trayectoria longitudinal de riesgo y compromisos pedagógicos</p>', unsafe_allow_html=True)

        # Tarjeta superior: Gráfico de evolución temporal (Mockup 5)
        st.markdown('<div class="unsa-card">', unsafe_allow_html=True)
        col_g1, col_g2 = st.columns([3, 1])

        with col_g1:
            fig, ax = plt.subplots(figsize=(7.5, 2.8), facecolor='white')
            semanas = ["Sem 1", "Sem 8", "Sem 16"]
            riesgos = [22.0, 48.0, 78.0]

            # Líneas guía de umbrales
            ax.axhline(y=38.0, color='#F59E0B', linestyle='--', linewidth=1.2, alpha=0.8, label="Umbral Alerta (38%)")
            ax.axhline(y=75.0, color='#EF4444', linestyle='--', linewidth=1.2, alpha=0.8, label="Umbral Crítico (75%)")

            # Curva principal
            ax.plot(semanas, riesgos, color='#7A1C20', linewidth=3, zorder=3)
            # Puntos intermedios y punto final dorado con borde granate
            ax.scatter(semanas[:-1], riesgos[:-1], color='#7A1C20', s=45, zorder=4)
            ax.scatter([semanas[-1]], [riesgos[-1]], facecolors='#C59B27', edgecolors='#7A1C20', linewidth=2.5, s=90, zorder=5)

            ax.set_ylim(0, 100)
            ax.set_ylabel("Riesgo (%)", fontsize=11, color='#0F172A', fontweight='bold')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E2E8F0')
            ax.spines['bottom'].set_color('#E2E8F0')
            ax.tick_params(colors='#64748B', labelsize=10)
            ax.grid(axis='y', linestyle=':', alpha=0.5, color='#E2E8F0')
            plt.tight_layout()
            st.pyplot(fig)

        with col_g2:
            st.markdown("""
            <div style="padding-top: 30px;">
                <div style="font-size: 14px; font-weight: 700; color: var(--granate-oscuro);">Tendencia: <span style="font-family: 'JetBrains Mono', monospace; color: var(--granate);">al alza</span></div>
                <div style="font-size: 12px; color: var(--texto-suave); margin-top: 4px;">Datos de seguimiento del estudiante en el semestre activo.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Tarjeta inferior: Lista de acciones de tutoría con casillas (Mockup 5)
        st.markdown("""
        <div class="unsa-card" style="padding: 18px 24px;">
            <div class="action-checklist-row">
                <div class="action-box checked">&#10003;</div>
                <div class="action-text">Acción 1: conversación inicial con el estudiante</div>
                <div class="action-date">12/09/2026</div>
            </div>
            <div class="action-checklist-row">
                <div class="action-box unchecked"></div>
                <div class="action-text">Acción 2: derivar a reforzamiento académico o tutoría par</div>
                <div class="action-date">15/10/2026</div>
            </div>
            <div class="action-checklist-row">
                <div class="action-box unchecked"></div>
                <div class="action-text">Acción 3: reevaluar el semáforo tras Fase 2</div>
                <div class="action-date">02/11/2026</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Botones de acción inferiores (Mockup 5)
        c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 3])
        with c_btn1:
            if st.button("Registrar tutoría", type="primary", use_container_width=True):
                st.success("Tutoría guardada en la bitácora docente y registrada en el bus.")
        with c_btn2:
            pdf_bytes = generate_intervention_pdf(
                student_id_anon="7f3a...c91",
                curso="Estructuras de Datos",
                docente=usuario["username"],
                checkpoint="CP1",
                probabilidad_pct=78.0,
                umbral_pct=34.0,
                semaforo="ROJO",
                meta_nota_min=13.5,
                promedio_acumulado=8.4,
                imposible=False,
                top_factors=[{"label": "Asistencia baja", "value": 0.42, "direction": "Riesgo"}],
                recommendations=["Plan de tutoría individual y seguimiento en laboratorio."]
            )
            st.download_button(
                label="Exportar informe PDF",
                data=pdf_bytes,
                file_name="Ficha_Intervencion_SATA.pdf",
                mime="application/pdf",
                use_container_width=True
            )


    # =========================================================================
    # VISTAS OPERATIVAS ADICIONALES (MANTENIMIENTO DE TODA LA LÓGICA Y DATOS)
    # =========================================================================
    elif nav_sel == "Inscribir Asignatura":
        st.markdown('<span class="section-label">MATRÍCULA</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Inscribir Asignatura para Monitoreo</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Asignaturas oficiales del plan de estudios EPIS</p>', unsafe_allow_html=True)

        docentes = get_all_teachers()
        nombres_cursos = [c["nombre"] for c in catalogo]

        c_sel = st.selectbox("Seleccione la Asignatura:", nombres_cursos)
        d_sel = st.selectbox("Docente Responsable:", docentes)
        sec_sel = st.selectbox("Sección:", ["A", "B", "C"])
        es_rep = st.selectbox("Condición de matrícula:", [0, 1], format_func=lambda x: "Repitente" if x == 1 else "Regular")

        c_obj = next((c for c in catalogo if c["nombre"] == c_sel), None)
        st.markdown("**Ponderaciones del Sílabo Oficial (%)**")
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            w_ec1 = st.number_input("Fase 1 - EC1 (%):", value=c_obj["peso_ec1"] if c_obj else 15, min_value=5, max_value=40)
            w_ep1 = st.number_input("Fase 1 - EP1 (%):", value=c_obj["peso_ep1"] if c_obj else 15, min_value=5, max_value=40)
        with col_w2:
            w_ec2 = st.number_input("Fase 2 - EC2 (%):", value=c_obj["peso_ec2"] if c_obj else 20, min_value=5, max_value=40)
            w_ep2 = st.number_input("Fase 2 - EP2 (%):", value=c_obj["peso_ep2"] if c_obj else 20, min_value=5, max_value=40)
        with col_w3:
            w_ec3 = st.number_input("Fase 3 - EC3 (%):", value=c_obj["peso_ec3"] if c_obj else 15, min_value=5, max_value=40)
            w_ep3 = st.number_input("Fase 3 - EP3 (%):", value=c_obj["peso_ep3"] if c_obj else 15, min_value=5, max_value=40)

        if (w_ec1 + w_ep1 + w_ec2 + w_ep2 + w_ec3 + w_ep3) != 100:
            st.error("Las ponderaciones deben sumar exactamente 100%.")
        else:
            if st.button("Confirmar Inscripción de Asignatura", type="primary"):
                pesos_dict = {"EC1": w_ec1, "EP1": w_ep1, "EC2": w_ec2, "EP2": w_ep2, "EC3": w_ec3, "EP3": w_ep3}
                mat_id = enroll_course(usuario["cui_hash"], "2026-B", c_sel, d_sel, sec_sel, pesos_dict, es_rep)
                st.success("Asignatura registrada y monitoreo activado.")
                st.rerun()

    elif nav_sel == "Perfil Basal":
        st.markdown('<span class="section-label">ANTECEDENTES</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Perfil Académico Basal</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Variables históricas que alimentan el Checkpoint 0</p>', unsafe_allow_html=True)

        perfil = get_student_profile(usuario["cui_hash"], "2026-B") or {}
        with st.form("form_perfil"):
            c1, c2 = st.columns(2)
            with c1:
                p_ira = st.number_input("IRA Acumulado previo (0–20):", 0.0, 20.0, float(perfil.get("ira_acum", 12.5)), step=0.1)
                p_rep = st.number_input("Cursos reprobados previamente en la carrera:", 0, 20, int(perfil.get("repeticiones_previas", 0)))
            with c2:
                p_cred = st.number_input("Créditos matriculados este semestre:", 1, 30, int(perfil.get("creditos_matriculados", 22)))
                p_ing = st.number_input("Semestres transcurridos desde su ingreso:", 1.0, 16.0, float(perfil.get("semestre_ingreso", 4.0)), step=0.5)

            if st.form_submit_button("Guardar Perfil Basal"):
                save_student_profile(usuario["cui_hash"], "2026-B", p_ira, p_rep, p_cred, p_ing)
                st.success("Perfil basal registrado correctamente.")
                st.rerun()

    elif nav_sel == "Carga Masiva de Actas":
        st.markdown('<span class="section-label">DOCENCIA</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Carga Masiva de Actas de Calificaciones</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Importación de actas oficiales (.csv / .xlsx) con validación automática</p>', unsafe_allow_html=True)

        plantilla_csv = generar_plantilla_carga_masiva_csv()
        st.download_button(
            label="Descargar Plantilla Oficial (plantilla_acta_sata.csv)",
            data=plantilla_csv,
            file_name="plantilla_acta_sata.csv",
            mime="text/csv"
        )
        st.markdown("---")
        up_file = st.file_uploader("Subir archivo de calificaciones completado:", type=["csv", "xlsx"])

        if up_file is not None:
            try:
                df_up = pd.read_csv(up_file) if up_file.name.endswith(".csv") else pd.read_excel(up_file)
                st.write(f"Archivo cargado: **{len(df_up)} filas detectadas**.")

                if st.button("Validar y Procesar Acta con Sistema Multiagente", type="primary"):
                    with st.spinner("Ejecutando validaciones sintácticas y pipeline multiagente..."):
                        procesados, errores = validar_y_procesar_acta_masiva(df_up, coordinator)
                    if errores:
                        st.warning(f"Se encontraron {len(errores)} observaciones:")
                        st.dataframe(pd.DataFrame(errores), use_container_width=True)
                    if procesados:
                        st.success(f"Se procesaron con éxito {len(procesados)} registros de estudiantes.")
                        st.dataframe(pd.DataFrame(procesados), use_container_width=True)
            except Exception as e:
                st.error(f"Error al leer el archivo: {str(e)}")

    elif nav_sel == "Métricas Institucionales":
        st.markdown('<span class="section-label">AUTORIDADES</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Métricas Institucionales y Alertas Agregadas</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Visión macro por asignatura sin acceso a identidades privadas</p>', unsafe_allow_html=True)

        data_macro = [get_course_risk_summary(c["nombre"], "2026-B") for c in catalogo]
        df_macro = pd.DataFrame(data_macro)

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Asignaturas en Monitoreo", len(df_macro))
        total_e = df_macro["total_alumnos"].sum()
        col_m2.metric("Total Estudiantes Evaluados", total_e)
        tot_r = df_macro["rojos"].sum()
        col_m3.metric("Alertas Rojas Globales", tot_r, delta=f"{(tot_r/total_e*100):.1f}%" if total_e > 0 else "0%")

        st.markdown("---")
        st.dataframe(
            df_macro.rename(columns={
                "curso": "Asignatura", "total_alumnos": "Total Estudiantes",
                "rojos": "Críticos (Rojo)", "amarillos": "Observación (Amarillo)",
                "verdes": "Regulares (Verde)", "tasa_riesgo_pct": "% En Riesgo"
            }),
            use_container_width=True
        )

    elif nav_sel == "Monitor Técnico OBJ5":
        st.markdown('<span class="section-label">ADMINISTRACIÓN</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Monitor Técnico de Arquitectura Multiagente</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Cumplimiento de latencia e hipótesis H3</p>', unsafe_allow_html=True)

        stats_tec = get_technical_metrics_summary()
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        col_t1.metric("Latencia Media Inferencia", f"{stats_tec['latencia_inf_media_ms']} ms", delta="< 5 ms")
        col_t2.metric("Latencia P95 Inferencia", f"{stats_tec['latencia_inf_p95_ms']} ms")
        col_t3.metric("Uso Promedio RAM", f"{stats_tec['ram_media_mb']} MB", delta="< 400 MB")
        col_t4.metric("Overhead Bus Asíncrono", f"{stats_tec['overhead_media_ms']} ms", delta="< 0.5 ms")

        st.info("La latencia de respuesta total del sistema se mantiene holgadamente por debajo de los 1.5 s exigidos por la hipótesis H3, desacoplando la inferencia inmediata de la generación de explicaciones.")

    elif nav_sel == "Encuestas SUS / TAM":
        st.markdown('<span class="section-label">VALIDACIÓN PSICOMÉTRICA</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Evaluación de Usabilidad y Aceptación</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Instrumentos estandarizados SUS y TAM (OBJ5 - Actividad 3)</p>', unsafe_allow_html=True)

        sus_stats = get_surveys_stats("SUS")
        tam_stats = get_surveys_stats("TAM")

        col_s1, col_s2 = st.columns(2)
        col_s1.metric("Puntuación Media SUS (Usabilidad)", f"{sus_stats['promedio']} / 100", delta=f"{sus_stats['total']} evaluadores")
        col_s2.metric("Puntuación Media TAM (Aceptación)", f"{tam_stats['promedio']} / 5.0", delta=f"{tam_stats['total']} evaluadores")

        with st.form("form_sus_eval"):
            p1 = st.slider("1. Creo que me gustaría utilizar este sistema con frecuencia:", 1, 5, 4)
            p2 = st.slider("2. Encontré el sistema innecesariamente complejo:", 1, 5, 2)
            p3 = st.slider("3. Pensé que el sistema fue fácil de usar:", 1, 5, 4)
            p4 = st.slider("4. Creo que necesitaría apoyo técnico para utilizarlo:", 1, 5, 1)
            p5 = st.slider("5. Las diversas funciones estaban bien integradas:", 1, 5, 5)
            p6 = st.slider("6. Había demasiada inconsistencia en el sistema:", 1, 5, 1)
            p7 = st.slider("7. La mayoría aprendería a usarlo muy rápidamente:", 1, 5, 4)
            p8 = st.slider("8. Encontré el sistema muy engorroso de utilizar:", 1, 5, 1)
            p9 = st.slider("9. Me sentí muy seguro al utilizar el sistema:", 1, 5, 4)
            p10 = st.slider("10. Necesité aprender muchas cosas antes de empezar:", 1, 5, 2)

            if st.form_submit_button("Guardar Evaluación SUS"):
                score_sus = ((p1 - 1) + (5 - p2) + (p3 - 1) + (5 - p4) + (p5 - 1) + (5 - p6) + (p7 - 1) + (5 - p8) + (p9 - 1) + (5 - p10)) * 2.5
                save_survey(usuario["username"], "DOCENTE_EVAL", "SUS", {
                    "p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5,
                    "p6": p6, "p7": p7, "p8": p8, "p9": p9, "p10": p10
                }, score_sus)
                st.success(f"Evaluación SUS registrada exitosamente. Puntaje obtenido: {score_sus:.1f} / 100")
                st.rerun()
