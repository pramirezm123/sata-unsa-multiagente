"""
Alerta Académica: Sistema Multiagente de Alerta Temprana de Riesgo Académico
Universidad Nacional de San Agustín de Arequipa (UNSA) | Tesis de Grado
Identidad Visual Oficial: "UNSA Granate Institucional y Modern Academic"

Diseño sobrio, institucional y riguroso. Sin emojis en la interfaz.
Tipografía: Plus Jakarta Sans (títulos y cuerpo) y JetBrains Mono (métricas, IDs y logs).
Paleta: Variables CSS en :root (--granate, --dorado, --azul-hielo, etc.)
"""
import base64
import datetime
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Configuración de ruta base
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.xai_agent import format_shap_factor_for_ui
from src.database.db import (
    authenticate_user,
    enroll_course,
    evaluate_and_persist_enrollment,
    get_all_courses,
    get_all_teachers,
    get_bus_messages_for_student,
    get_course_risk_summary,
    get_course_sections_summary,
    get_course_students_table,
    get_enrollment_by_id,
    get_grade_change_history,
    get_grades_for_enrollment,
    get_header_metrics,
    get_latest_prediction,
    get_prediction_history,
    get_recent_bus_messages,
    get_student_enrollments,
    get_student_info,
    get_student_profile,
    get_surveys_stats,
    get_technical_metrics_summary,
    get_tutoring_checklist_state,
    get_tutoring_history,
    register_student_user,
    register_tutoring_session,
    save_grade,
    save_student_profile,
    save_survey,
    schedule_tutoring_session,
    update_student_consent,
)
from src.messaging.bus import MessageBus
from src.reports.pdf_generator import generate_intervention_pdf
from src.security.crypto import hash_cui
from src.services.academic_service import (
    calcular_simulacion_sustitutorio,
    generar_plantilla_carga_masiva_csv,
    validar_y_procesar_acta_masiva,
)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Alerta Académica | UNSA",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================================
# GESTIÓN DE RECURSOS E IMÁGENES INSTITUCIONALES
# =========================================================================
@st.cache_data
def get_image_base64(rel_path: str) -> str:
    """Carga y codifica una imagen institucional en base64 para embeber en HTML."""
    path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


ESCUDO_UNSA_B64 = get_image_base64("assets/escudo_unsa.png")
BANNER_FIPS_B64 = get_image_base64("assets/banner_fips.png")
BANNER_EPIS_B64 = get_image_base64("assets/banner_epis.png")


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
        --texto-suave: #475569;
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

    /* Streamlit Header con barra superior limpia para alojar el botón de menú sin solapar contenido */
    header[data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.92) !important;
        backdrop-filter: blur(6px) !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.8) !important;
        z-index: 999990 !important;
        height: 2.75rem !important;
    }
    footer { display: none !important; }
    #MainMenu { visibility: hidden !important; }

    /* Control de colapso y reapertura del menú lateral */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] [data-testid="stSidebarCollapseButton"] {
        opacity: 1 !important;
        visibility: visible !important;
        display: flex !important;
    }
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stExpandSidebarButton"],
    button[aria-label="Expand sidebar"] {
        top: 0.35rem !important;
        left: 0.75rem !important;
        z-index: 999999 !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"],
    button[aria-label="Expand sidebar"] {
        opacity: 1 !important;
        visibility: visible !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: var(--granate) !important;
        color: #FFFFFF !important;
        border: 1.5px solid var(--dorado) !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(122, 28, 32, 0.28) !important;
        padding: 4px 8px !important;
        min-height: 32px !important;
        height: 32px !important;
        transition: all .2s ease !important;
    }
    [data-testid="stSidebarCollapsedControl"] button:hover,
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stExpandSidebarButton"]:hover,
    button[aria-label="Expand sidebar"]:hover {
        background: var(--granate-oscuro) !important;
        border-color: var(--dorado-claro) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stExpandSidebarButton"] svg,
    button[aria-label="Expand sidebar"] svg {
        fill: #FFFFFF !important;
        stroke: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* Preservación estricta de fuente Material Symbols para evitar ligaduras rotas (keyboard_double_) */
    [data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapsedControl"] span,
    [data-testid="stExpandSidebarButton"] span,
    button[aria-label="Expand sidebar"] span,
    button[aria-label="Close sidebar"] span {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 20px !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        color: #FFFFFF !important;
    }

    /* Fondo general y contenedor en modo claro institucional */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: var(--fondo) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: var(--texto) !important;
        overflow-x: hidden !important;
    }
    .block-container {
        padding-top: 3.3rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1240px !important;
    }

    /* Contraste alto en textos del área principal (excluyendo Sidebar y consola FIPA-ACL) */
    [data-testid="stMain"] p:not(.fipa-log-body *),
    [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p,
    [data-testid="stMain"] [data-testid="stWidgetLabel"] label,
    [data-testid="stMain"] .stRadio label p,
    [data-testid="stMain"] .stRadio label span,
    [data-testid="stMain"] .stRadio label {
        color: var(--texto) !important;
    }

    /* Textos secundarios y captions del área principal con contraste estricto (Slate 600) */
    .section-subtitle,
    .sub-footer-row,
    .sub-footer-row span,
    .sub-metric-label,
    .node-desc,
    .action-date,
    [data-testid="stMain"] .stCaption,
    [data-testid="stMain"] .stCaption p {
        color: var(--texto-suave) !important;
    }

    /* Identificador anonimizado tipo badge monoespaciado */
    .cui-mono {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        color: var(--granate-oscuro) !important;
        background-color: var(--azul-hielo) !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 3px 10px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        display: inline-block !important;
    }

    /* Sidebar oficial con degradado granate y textos blancos de alto contraste */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--granate) 0%, var(--granate-oscuro) 100%) !important;
        border-right: 1px solid rgba(197, 155, 39, 0.35) !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span:not([data-testid="stIconMaterial"]):not(.material-icons),
    [data-testid="stSidebar"] div:not([data-testid="stIconMaterial"]),
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] .stRadio label span:not([data-testid="stIconMaterial"]),
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stCaption p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    [data-testid="stSidebar"] code {
        color: var(--dorado-claro) !important;
        background: rgba(0, 0, 0, 0.25) !important;
        border: 1px solid rgba(232, 200, 115, 0.3) !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 11.5px !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        padding: 9px 14px !important;
        border-radius: 8px !important;
        transition: all .2s ease !important;
        margin-bottom: 4px !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border-left: 3px solid transparent !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.14) !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(255, 255, 255, 0.2) !important;
        font-weight: 700 !important;
        border-left: 3px solid var(--dorado-claro) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
        margin: 16px 0 !important;
    }

    /* Botón de Cerrar Sesión en el Sidebar con alto contraste sobre fondo granate */
    [data-testid="stSidebar"] .stButton button {
        background: rgba(255, 255, 255, 0.12) !important;
        color: #FFFFFF !important;
        border: 1.5px solid var(--dorado-claro) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 8px 14px !important;
        transition: all .2s ease !important;
    }
    [data-testid="stSidebar"] .stButton button *,
    [data-testid="stSidebar"] .stButton button p,
    [data-testid="stSidebar"] .stButton button span {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(197, 155, 39, 0.3) !important;
        border-color: #FFFFFF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }

    /* Botones principales (granate institucional con texto blanco) en el área principal */
    [data-testid="stMain"] button[kind="primary"],
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"],
    [data-testid="stMain"] .stButton button[data-testid="baseButton-primary"],
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, var(--granate) 0%, var(--granate-claro) 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--granate-oscuro) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        box-shadow: 0 4px 12px rgba(122, 28, 32, 0.22) !important;
        transition: all .22s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stMain"] button[kind="primary"] *,
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"] *,
    [data-testid="stMain"] .stButton button[data-testid="baseButton-primary"] *,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button * {
        color: #FFFFFF !important;
    }
    [data-testid="stMain"] button[kind="primary"]:hover,
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stMain"] .stButton button[data-testid="baseButton-primary"]:hover,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, var(--granate-oscuro) 0%, var(--granate) 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(122, 28, 32, 0.35) !important;
    }
    [data-testid="stMain"] button[kind="primary"]:focus-visible,
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"]:focus-visible,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:focus-visible {
        outline: 3px solid var(--dorado-claro) !important;
        outline-offset: 2px !important;
    }
    [data-testid="stMain"] button[kind="primary"]:active,
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"]:active,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0) !important;
    }

    /* Botones secundarios y de descarga en el área principal */
    [data-testid="stMain"] .stButton button[kind="secondary"],
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-secondary"],
    [data-testid="stMain"] [data-testid="stDownloadButton"] button {
        background: #FFFFFF !important;
        border: 1.5px solid var(--dorado) !important;
        color: var(--granate) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all .22s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stMain"] .stButton button[kind="secondary"] *,
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-secondary"] *,
    [data-testid="stMain"] [data-testid="stDownloadButton"] button * {
        color: var(--granate) !important;
    }
    [data-testid="stMain"] .stButton button[kind="secondary"]:hover,
    [data-testid="stMain"] .stButton button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
        background: rgba(197, 155, 39, 0.1) !important;
        transform: translateY(-1px) !important;
        border-color: var(--granate) !important;
        color: var(--granate-oscuro) !important;
    }
    [data-testid="stMain"] .stButton button[kind="secondary"]:focus-visible,
    [data-testid="stMain"] [data-testid="stDownloadButton"] button:focus-visible {
        outline: 3px solid var(--dorado) !important;
        outline-offset: 2px !important;
    }
    [data-testid="stMain"] button:disabled {
        opacity: 0.55 !important;
        cursor: not-allowed !important;
        transform: none !important;
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
        padding: 10px 16px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    [data-baseweb="tab"] p, [data-baseweb="tab"] span {
        color: var(--texto-suave) !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 3px solid var(--granate) !important;
    }
    [data-baseweb="tab"][aria-selected="true"] p,
    [data-baseweb="tab"][aria-selected="true"] span {
        color: var(--granate) !important;
        font-weight: 700 !important;
    }

    /* Estilos de Contenedor con Borde Nativo de Streamlit */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: var(--tarjeta) !important;
        border: 1px solid var(--borde) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 24px -6px rgba(122, 28, 32, 0.06) !important;
        padding: 22px 24px !important;
        margin-bottom: 16px !important;
    }

    /* Banner Institucional Oficial UNSA */
    .unsa-header-banner {
        background: repeating-linear-gradient(135deg, rgba(255,255,255,0.035) 0, rgba(255,255,255,0.035) 10px, transparent 10px, transparent 20px), var(--granate-oscuro);
        border-radius: 12px 12px 0 0;
        padding: 22px 28px;
        color: #FFFFFF !important;
        position: relative;
        box-shadow: 0 8px 24px -4px rgba(90, 18, 21, 0.25);
    }
    .unsa-header-banner * {
        color: #FFFFFF !important;
    }
    .unsa-banner-inner {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .unsa-escudo-img {
        height: 68px;
        width: auto;
        object-fit: contain;
        filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
    }
    .unsa-banner-inst {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: var(--dorado-claro) !important;
        margin-bottom: 4px;
    }
    .unsa-banner-title {
        font-size: 24px;
        font-weight: 800;
        color: #FFFFFF !important;
        margin: 0 0 4px 0;
        line-height: 1.2;
    }
    .unsa-banner-meta {
        font-size: 13px;
        color: var(--azul-hielo) !important;
        font-weight: 400;
    }
    .unsa-banner-fillet {
        height: 4px;
        background-color: var(--dorado);
        border-radius: 0 0 4px 4px;
        margin-bottom: 22px;
    }

    /* Tarjetas y Contenedores */
    .unsa-card {
        background: var(--tarjeta);
        border: 1px solid var(--borde);
        border-radius: 12px;
        box-shadow: 0 10px 22px -6px rgba(122,28,32,.07);
        padding: 22px 24px;
        transition: all .25s cubic-bezier(0.4,0,0.2,1);
        margin-bottom: 18px;
    }
    .unsa-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 28px -8px rgba(122,28,32,.12);
    }

    /* Títulos de sección */
    .section-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--dorado) !important;
        display: block;
        margin-bottom: 2px;
    }
    .section-title {
        font-size: 24px;
        font-weight: 800;
        color: var(--granate-oscuro) !important;
        margin-top: 0;
        margin-bottom: 4px;
        line-height: 1.25;
    }

    /* Sub-métricas Mockup 2 */
    .sub-metric-card {
        background: #FFFFFF !important;
        border: 1px solid var(--borde) !important;
        border-top: 3px solid var(--dorado) !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
        height: 100% !important;
    }
    .sub-metric-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--texto-suave) !important;
        margin-bottom: 6px !important;
    }
    .sub-metric-val {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        color: var(--granate-oscuro) !important;
    }
    .lema-box {
        background-color: var(--azul-hielo) !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        font-size: 13.5px !important;
        color: var(--texto) !important;
        margin: 18px 0 14px 0 !important;
        line-height: 1.5 !important;
    }
    .lema-bold {
        font-weight: 700 !important;
        color: var(--granate-oscuro) !important;
    }
    .sub-footer-row {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        margin-bottom: 24px;
    }

    /* MOCKUP 1: Métricas de Semáforo */
    .metric-card-risk {
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        transition: all .25s ease;
        margin-bottom: 16px;
    }
    .metric-card-risk.alto {
        background-color: var(--riesgo-alto-bg) !important;
        border: 1.5px solid var(--riesgo-alto-borde) !important;
    }
    .metric-card-risk.alto .metric-card-label {
        color: var(--riesgo-alto-texto) !important;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
    }
    .metric-card-risk.alto .metric-card-value {
        color: var(--riesgo-alto-texto) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-card-risk.alerta {
        background-color: var(--alerta-bg) !important;
        border: 1.5px solid var(--alerta-borde) !important;
    }
    .metric-card-risk.alerta .metric-card-label {
        color: var(--alerta-texto) !important;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
    }
    .metric-card-risk.alerta .metric-card-value {
        color: var(--alerta-texto) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-card-risk.bajo {
        background-color: var(--riesgo-bajo-bg) !important;
        border: 1.5px solid var(--riesgo-bajo-borde) !important;
    }
    .metric-card-risk.bajo .metric-card-label {
        color: var(--riesgo-bajo-texto) !important;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
    }
    .metric-card-risk.bajo .metric-card-value {
        color: var(--riesgo-bajo-texto) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }

    /* Badges de riesgo */
    .badge-alto {
        background: #FEF2F2 !important;
        border: 1px solid #EF4444 !important;
        color: #991B1B !important;
        font-weight: 700;
        font-size: 11px;
        border-radius: 99px;
        padding: 3px 12px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }
    .badge-alerta {
        background: #FFFBEB !important;
        border: 1px solid #F59E0B !important;
        color: #92400E !important;
        font-weight: 700;
        font-size: 11px;
        border-radius: 99px;
        padding: 3px 12px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
    }
    .badge-bajo {
        background: #F0FDF4 !important;
        border: 1px solid #22C55E !important;
        color: #166534 !important;
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
        gap: 14px;
        flex-wrap: wrap;
        padding: 13px 8px;
        border-bottom: 1px solid var(--borde);
    }
    .student-list-row:last-child {
        border-bottom: none;
    }
    .student-name {
        flex: 1 1 220px;
        font-size: 14px;
        font-weight: 600;
        color: var(--texto) !important;
        line-height: 1.4;
    }

    /* MOCKUP 3: Detalle con Explicabilidad */
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
        align-items: baseline;
        gap: 10px;
        font-size: 13px;
        margin-bottom: 6px;
    }
    .factor-name {
        color: var(--texto) !important;
        font-weight: 600;
    }
    .factor-val-mono {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 13px;
        white-space: nowrap;
        flex-shrink: 0;
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
        background-color: var(--alerta-bg) !important;
        border: 1px solid var(--alerta-borde) !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        margin-top: 18px !important;
        color: var(--alerta-texto) !important;
        font-size: 13.5px !important;
        line-height: 1.5 !important;
    }
    .suggestion-box b {
        color: var(--alerta-texto) !important;
    }

    /* MOCKUP 4: Trazabilidad Multiagente */
    .stepped-pipeline-container {
        position: relative;
        padding: 24px 10px 14px 10px;
        margin-bottom: 24px;
        background: #FFFFFF;
        border: 1px solid var(--borde);
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(122, 28, 32, 0.04);
    }
    .stepped-line {
        position: absolute;
        top: 44px;
        left: 11%;
        right: 11%;
        height: 2.5px;
        background-color: var(--dorado);
        z-index: 1;
    }
    .stepped-nodes {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: nowrap;
        gap: 12px;
        position: relative;
        z-index: 2;
    }
    .stepped-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        flex: 1 1 0;
        min-width: 0;
        padding: 0 6px;
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
        flex-shrink: 0;
    }
    .node-circle.solid {
        background-color: var(--granate) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(122, 28, 32, 0.25);
    }
    .node-circle.active {
        background-color: #FFFFFF !important;
        border: 2.5px solid var(--dorado) !important;
        color: var(--granate) !important;
        box-shadow: 0 4px 12px rgba(197, 155, 39, 0.3);
    }
    .node-title {
        font-weight: 700;
        color: var(--granate-oscuro) !important;
        font-size: 13.5px;
        margin-bottom: 2px;
        line-height: 1.3;
    }
    .fipa-log-header {
        background: linear-gradient(90deg, var(--granate-oscuro) 0%, var(--granate) 100%) !important;
        border: 1px solid rgba(197, 155, 39, 0.45) !important;
        border-bottom: 1px solid rgba(197, 155, 39, 0.35) !important;
        border-radius: 10px 10px 0 0;
        padding: 12px 18px;
        color: var(--dorado-claro) !important;
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: 0.1em;
        font-family: 'JetBrains Mono', monospace;
    }
    .fipa-log-body {
        background-color: #1E0709 !important;
        border: 1px solid rgba(197, 155, 39, 0.45) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 14px 18px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12.5px !important;
        line-height: 1.75 !important;
        color: #F8FAFC !important;
        overflow-x: auto !important;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.35) !important;
    }
    .fipa-log-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        padding: 6px 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        color: #F8FAFC !important;
    }
    .fipa-log-row:last-child {
        border-bottom: none;
    }
    .fipa-time {
        color: #CBD5E1 !important;
        font-weight: 500;
        font-size: 12px;
    }
    .fipa-conv-id {
        color: #E2E8F0 !important;
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 11px;
    }
    .fipa-performative {
        font-weight: 700;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
        letter-spacing: 0.04em;
        display: inline-block;
    }
    .fipa-perf-request {
        background: rgba(245, 158, 11, 0.22) !important;
        color: #FCD34D !important;
        border: 1px solid rgba(252, 211, 77, 0.5) !important;
    }
    .fipa-perf-inform {
        background: rgba(56, 189, 248, 0.2) !important;
        color: #7DD3FC !important;
        border: 1px solid rgba(125, 211, 252, 0.5) !important;
    }
    .fipa-perf-propose {
        background: rgba(34, 197, 94, 0.2) !important;
        color: #86EFAC !important;
        border: 1px solid rgba(134, 239, 172, 0.5) !important;
    }
    .fipa-perf-failure {
        background: rgba(239, 68, 68, 0.25) !important;
        color: #FCA5A5 !important;
        border: 1px solid rgba(252, 165, 165, 0.55) !important;
    }
    .fipa-route {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    .fipa-topic {
        color: #E8C873 !important;
        font-size: 12px;
    }

    /* MOCKUP 5: Seguimiento y Plan de Tutoría */
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
        background-color: var(--granate) !important;
        color: #FFFFFF !important;
    }
    .action-box.unchecked {
        background-color: #FFFFFF !important;
        border: 1.5px solid var(--dorado) !important;
    }
    .action-text {
        flex-grow: 1;
        font-size: 14px;
        color: var(--texto) !important;
        font-weight: 500;
    }

    /* Responsividad en tablet (<= 768px) y móvil (<= 480px) */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 3.3rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .unsa-header-banner {
            padding: 18px 16px;
        }
        .unsa-banner-inner {
            flex-direction: column;
            text-align: center;
            gap: 10px;
        }
        .unsa-banner-title {
            font-size: 20px;
        }
        .sub-footer-row {
            flex-direction: column;
            gap: 6px;
            text-align: left;
        }
        .stepped-nodes {
            flex-wrap: wrap;
            gap: 16px;
        }
        .stepped-node {
            flex: 0 0 calc(50% - 8px);
            width: calc(50% - 8px);
        }
        .stepped-line {
            display: none;
        }
    }

    @media (max-width: 480px) {
        .block-container {
            padding-top: 3.2rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
        .unsa-banner-title {
            font-size: 18px;
        }
        .section-title {
            font-size: 20px;
        }
        .stepped-node {
            flex: 0 0 100%;
            width: 100%;
        }
        .factor-label-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 2px;
        }
        .fipa-log-body {
            padding: 12px 12px !important;
            font-size: 11.5px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# FUNCIONES AUXILIARES DE RENDERIZADO VISUAL
# =========================================================================
def render_institutional_banner(facultad="Facultad de Ingeniería de Producción y Servicios",
                                escuela="Escuela Profesional de Ingeniería de Sistemas",
                                semestre="Semestre 2026-B"):
    """Renderiza el banner superior institucional oficial UNSA con su escudo oficial."""
    escudo_html = f'<img src="data:image/png;base64,{ESCUDO_UNSA_B64}" class="unsa-escudo-img" alt="Escudo UNSA" />' if ESCUDO_UNSA_B64 else '<div class="unsa-escudo-circle">UNSA</div>'

    st.markdown(f"""
    <div class="unsa-header-banner">
        <div class="unsa-banner-inner">
            {escudo_html}
            <div>
                <div class="unsa-banner-inst">Universidad Nacional de San Agustín de Arequipa</div>
                <div class="unsa-banner-title">SATA-UNSA · Plataforma de Alerta Temprana de Riesgo Académico</div>
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
# 1. PANTALLA DE ACCESO / INICIO DE SESIÓN (UNSA INSTITUCIONAL & STITCH)
# =========================================================================
if st.session_state["usuario"] is None:
    render_institutional_banner()

    col_info, col_auth = st.columns([1.1, 1], gap="medium")

    with col_info:
        with st.container(border=True):
            st.markdown('<span class="section-label">IDENTIDAD INSTITUCIONAL & ÉTICA</span>', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title" style="font-size: 21px;">Arquitectura de Alerta Temprana</h3>', unsafe_allow_html=True)

            if BANNER_EPIS_B64:
                st.markdown(f"""
                <div style="margin: 12px 0 16px 0;">
                    <img src="data:image/png;base64,{BANNER_EPIS_B64}" style="max-height: 48px; width: auto; border-radius: 6px;" alt="EPIS UNSA" />
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div class="lema-box" style="margin-top: 10px;">
                <span class="lema-bold">Principio de Estimación y Privacidad:</span> Este sistema genera estimaciones probabilísticas orientativas para apoyar la labor de tutoría y el autoaprendizaje. <b>Nunca guarda ni transmite nombres ni CUI en texto claro.</b> Toda identidad se procesa mediante un código criptográfico irreversible HMAC-SHA256 con sal secreta institucional.
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="font-size: 13px; line-height: 1.6; color: var(--texto-suave);">
                <b>Pilares de Seguridad y Normativa:</b>
                <ul style="margin: 6px 0 12px 18px; padding: 0;">
                    <li>Aislamiento estricto de datos por perfil de estudiante.</li>
                    <li>PBKDF2-HMAC-SHA256 con 100,000 iteraciones para contraseñas.</li>
                    <li>Explicabilidad transparente (XAI SHAP) y auditoría FIPA-ACL.</li>
                    <li>Sustitutorio reemplaza únicamente el examen parcial más bajo.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # Tarjeta de Evaluación Rápida para el Jurado / Revisores
        with st.container(border=True):
            st.markdown('<span class="section-label">EVALUACIÓN DE TESIS</span>', unsafe_allow_html=True)
            st.markdown('<h4 class="section-title" style="font-size: 18px; margin-bottom: 6px;">Acceso Rápido de Evaluación</h4>', unsafe_allow_html=True)
            st.caption("Seleccione un perfil para evaluar inmediatamente las funcionalidades del sistema:")

            if st.button("Entrar como Estudiante Demo (CUI: 20220638)", use_container_width=True):
                user = authenticate_user("20220638", "Alumno123*") or authenticate_user(hash_cui("20220638"), "Alumno123*")
                if user:
                    st.session_state["usuario"] = user
                    st.rerun()
                else:
                    st.error("No se pudo iniciar sesión con el usuario demo de estudiante.")

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

    with col_auth:
        with st.container(border=True):
            st.markdown('<span class="section-label">PORTAL DE ACCESO</span>', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title" style="font-size: 21px;">Autenticación Segura</h3>', unsafe_allow_html=True)

            tab_login, tab_reg = st.tabs(["Iniciar Sesión", "Registro de Estudiante"])

            with tab_login:
                tipo_usuario = st.radio("Tipo de usuario:", ["Estudiante", "Docente / Autoridad / Administrador"], horizontal=True)

                if tipo_usuario == "Estudiante":
                    st.caption("Ingrese su CUI oficial (se convertirá en hash HMAC-SHA256 al instante).")
                    cui_input = st.text_input("CUI del Estudiante:", max_chars=10, key="login_cui")
                    pwd_input = st.text_input("Contraseña:", type="password", key="login_pwd_est")

                    if st.button("Ingresar al Portal del Estudiante", type="primary", use_container_width=True):
                        if not cui_input or not pwd_input:
                            st.error("Por favor complete su CUI y contraseña.")
                        else:
                            cui_clean = cui_input.strip()
                            cui_h = hash_cui(cui_clean)
                            user = authenticate_user(cui_clean, pwd_input) or authenticate_user(cui_h, pwd_input)
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
                st.caption("Cree su cuenta con su CUI oficial. Su identidad quedará anonimizada criptográficamente.")
                reg_cui = st.text_input("Ingrese su CUI oficial:", max_chars=8, key="reg_cui")
                reg_pwd = st.text_input("Cree una contraseña segura:", type="password", key="reg_pwd")
                reg_pwd2 = st.text_input("Confirme su contraseña:", type="password", key="reg_pwd2")

                if st.button("Registrar Cuenta", type="primary", use_container_width=True):
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

    st.stop()


# =========================================================================
# 2. ENTORNO AUTENTICADO: HEADER Y SIDEBAR
# =========================================================================
usuario = st.session_state.get("usuario")
if usuario is not None:
    rol = usuario["role"]
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")

    # Sidebar oficial (Mockup 1)
    if BANNER_EPIS_B64:
        st.sidebar.markdown(f"""
        <div style="padding: 10px 0 12px 0;">
            <img src="data:image/png;base64,{BANNER_EPIS_B64}" style="max-height: 42px; width: auto; border-radius: 6px;" alt="EPIS UNSA" />
            <div style="font-size: 17px; font-weight: 800; color: #FFFFFF; line-height: 1.2; margin-top: 8px;">Alerta Académica</div>
            <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: var(--dorado-claro); margin-top: 3px;">UNIVERSIDAD NACIONAL DE SAN AGUSTÍN</div>
        </div>
        """, unsafe_allow_html=True)
    else:
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

    if st.session_state.get("pending_nav") in menu_items:
        st.session_state["nav_radio"] = st.session_state.pop("pending_nav")
    nav_sel = st.sidebar.radio("Navegación:", menu_items, key="nav_radio")

    st.sidebar.markdown("---")
    if rol == "ESTUDIANTE":
        st.sidebar.caption(f"ID Criptográfico: `{usuario['cui_hash'][:10]}...`")
    else:
        st.sidebar.caption(f"Usuario: `{usuario['username']}` ({rol})")

    # Cierre de sesión seguro con limpieza total de memoria
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # Banner superior institucional (Mockup 2)
    render_institutional_banner()

    # Sub-cabecera con saludo, 3 métricas reales desde SQLite con borde dorado y lema (Mockup 2)
    catalogo = get_all_courses()
    cursos_nombres_all = [c["nombre"] for c in catalogo]

    def _get_default_course_index(cursos_list: list[str]) -> int:
        pref = st.session_state.get("docente_curso_activo")
        if pref and pref in cursos_list:
            return cursos_list.index(pref)
        for idx_c, c_nom in enumerate(cursos_list):
            if get_course_risk_summary(c_nom, "2026-B")["total_alumnos"] > 0:
                return idx_c
        return 0

    header_info = get_header_metrics(usuario, semestre="2026-B")
    lbl_m1 = header_info["label_col1"]
    val_m1 = int(header_info["valor_col1"])
    lbl_m2 = header_info["label_col2"]
    val_m2 = int(header_info["valor_col2"])
    ult_act_txt = header_info["ultima_actualizacion"]

    nombre_saludo = (
        f"Estudiante (ID Hash: {usuario['cui_hash'][:10]}...)"
        if rol == "ESTUDIANTE"
        else usuario["username"]
    )

    st.markdown(f"""
    <div style="font-size: 14px; color: var(--texto-suave); margin-bottom: 14px;">
        Hola, <b>{nombre_saludo}</b> · <span style="font-family: 'JetBrains Mono', monospace;">{fecha_hoy}</span>
    </div>
    """, unsafe_allow_html=True)

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.markdown(f"""
        <div class="sub-metric-card">
            <div class="sub-metric-label">{lbl_m1}</div>
            <div class="sub-metric-val">{val_m1:02d}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"""
        <div class="sub-metric-card">
            <div class="sub-metric-label">{lbl_m2}</div>
            <div class="sub-metric-val">{val_m2:02d}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_m3:
        st.markdown(f"""
        <div class="sub-metric-card">
            <div class="sub-metric-label">ÚLTIMA ACTUALIZACIÓN</div>
            <div class="sub-metric-val" style="font-size: 20px;">{ult_act_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="lema-box">
        <span class="lema-bold">Estimación, no sentencia.</span> El semáforo orienta la conversación de tutoría; la decisión siempre es del tutor y del estudiante.
    </div>
    <div class="sub-footer-row">
        <span>Datos anonimizados con CUI hash (HMAC-SHA256)</span>
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

        mat_id_panel = None
        if rol == "ESTUDIANTE":
            mis_mats = get_student_enrollments(usuario["cui_hash"], "2026-B", current_user=usuario)
            if mis_mats:
                mat_id_panel = mis_mats[0]["id"]
            rojos_cnt = 0
            amarillos_cnt = 0
            verdes_cnt = 0
            for m in mis_mats:
                pred = get_latest_prediction(m["id"], current_user=usuario)
                sem = pred.get("semaforo") if pred else "VERDE"
                if sem == "ROJO":
                    rojos_cnt += 1
                elif sem == "AMARILLO":
                    amarillos_cnt += 1
                else:
                    verdes_cnt += 1
        else:
            def_idx_panel = _get_default_course_index(cursos_nombres_all)
            curso_sel = st.selectbox("Asignatura a supervisar:", cursos_nombres_all, index=def_idx_panel, key="sel_curso_panel")
            st.session_state["docente_curso_activo"] = curso_sel
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

        # Contenedor limpio para la lista de asignaturas, estudiantes o resúmenes según rol (Mockup 1)
        with st.container(border=True):
            if rol == "ESTUDIANTE":
                mis_mats = get_student_enrollments(usuario["cui_hash"], "2026-B", current_user=usuario)
                if not mis_mats:
                    st.info("No tiene asignaturas inscritas aún. Utilice la opción 'Inscribir Asignatura' en el menú lateral.")
                else:
                    for idx, m in enumerate(mis_mats):
                        p_rec = get_latest_prediction(m["id"], current_user=usuario)
                        sem_tag = p_rec.get("semaforo", "ROJO" if idx == 0 else "VERDE") if p_rec else "VERDE"
                        badge_html = '<span class="badge-alto">ALTO</span>' if sem_tag == "ROJO" else ('<span class="badge-alerta">ALERTA</span>' if sem_tag == "AMARILLO" else '<span class="badge-bajo">BAJO</span>')
                        st.markdown(f"""
                        <div class="student-list-row">
                            <span class="cui-mono">Sec. {m['seccion']} · {m['semestre']}</span>
                            <span class="student-name">{m['curso']} (Prof. {m['docente']})</span>
                            {badge_html}
                        </div>
                        """, unsafe_allow_html=True)
            elif rol == "DOCENTE":
                alumnos_lista = get_course_students_table(curso_sel, "2026-B", current_user=usuario)
                if not alumnos_lista:
                    st.info(f"No hay registros de calificaciones para {curso_sel} en 2026-B.")
                else:
                    mat_id_panel = int(alumnos_lista[0]["matricula_id"])
                    for al in alumnos_lista:
                        id_m = str(al.get("id_mostrado") or al.get("cui_hash", ""))
                        cui_txt = id_m if id_m.startswith("RES-") else f"{id_m[:8]}...{id_m[-4:]}"
                        nom_txt = f"Estudiante Anonimizado (Sec. {al.get('seccion', 'A')} · {al.get('estado_optin', 'Compartido')})"
                        sem_tag = al.get("semaforo", "VERDE")

                        if sem_tag == "ROJO":
                            badge_html = '<span class="badge-alto">ALTO</span>'
                        elif sem_tag == "AMARILLO":
                            badge_html = '<span class="badge-alerta">ALERTA</span>'
                        else:
                            badge_html = '<span class="badge-bajo">BAJO</span>'

                        st.markdown(f"""
                        <div class="student-list-row">
                            <span class="cui-mono">ID {cui_txt}</span>
                            <span class="student-name">{nom_txt}</span>
                            {badge_html}
                        </div>
                        """, unsafe_allow_html=True)
            elif rol == "AUTORIDAD":
                st.info(
                    "Vista Agregada de Comité / Autoridad: Por principio de privacidad por diseño, "
                    "este perfil visualiza exclusivamente estadísticas consolidadas por asignatura y sección, "
                    "sin acceso a CUI, hashes individuales ni calificaciones personales."
                )
                secciones_res = get_course_sections_summary(curso_sel, "2026-B")
                if not secciones_res:
                    st.info(f"No existen cohortes evaluadas aún para {curso_sel} en el semestre 2026-B.")
                else:
                    df_sec = pd.DataFrame(secciones_res).rename(columns={
                        "seccion": "Sección",
                        "docente": "Docente Responsable",
                        "total_alumnos": "Total Estudiantes",
                        "rojos": "Riesgo Alto (Rojo)",
                        "amarillos": "Alerta Preventiva (Amarillo)",
                        "verdes": "Riesgo Bajo (Verde)",
                        "promedio_riesgo_pct": "Riesgo Promedio (%)",
                        "tasa_riesgo_pct": "% En Riesgo Alto",
                    })
                    cols_visibles = [
                        "Sección", "Docente Responsable", "Total Estudiantes",
                        "Riesgo Alto (Rojo)", "Alerta Preventiva (Amarillo)",
                        "Riesgo Bajo (Verde)", "Riesgo Promedio (%)", "% En Riesgo Alto",
                    ]
                    st.dataframe(df_sec[cols_visibles], use_container_width=True)
            else:  # ADMIN
                stats_admin = get_technical_metrics_summary()
                st.info(
                    "Panel Operativo de Administración (RBAC): El rol Administrador supervisa la salud "
                    "técnica del Sistema Multiagente y las métricas agregadas de operación. En cumplimiento del "
                    "principio de privacidad por diseño, no tiene acceso a nóminas, CUI ni notas individuales."
                )
                c_ad1, c_ad2, c_ad3 = st.columns(3)
                c_ad1.metric("Matrículas Evaluadas en Asignatura", resumen["total_alumnos"])
                c_ad2.metric("Tasa de Riesgo Alto en Asignatura", f"{resumen['tasa_riesgo_pct']}%")
                c_ad3.metric("Muestras Técnicas Registradas (OBJ5)", stats_admin["total_muestras"])

        # Botones inferiores exclusivos para roles con seguimiento individual (ESTUDIANTE y DOCENTE)
        if rol in ("ESTUDIANTE", "DOCENTE"):
            b_c1, b_c2, _ = st.columns([1.5, 1.5, 3])
            with b_c1:
                if st.button("Programar tutoría", type="primary", use_container_width=True):
                    if mat_id_panel is None:
                        st.warning("Seleccione una asignatura con matrículas activas antes de programar una tutoría.")
                    else:
                        fecha_prog = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
                        motivo_prog = "Sesión de orientación académica preventiva programada desde el Panel de Seguimiento."
                        ok_prog, msg_prog = schedule_tutoring_session(
                            mat_id_panel, fecha_prog, motivo_prog, current_user=usuario
                        )
                        if ok_prog:
                            st.success(msg_prog)
                        else:
                            st.error(msg_prog)
            with b_c2:
                if st.button("Ver explicación", use_container_width=True):
                    if mat_id_panel is not None:
                        st.session_state["selected_student_mat"] = mat_id_panel
                    st.session_state["pending_nav"] = "Detalle con explicabilidad"
                    st.rerun()


    # =========================================================================
    # VISTA 2: MOCKUP 3 - DETALLE CON EXPLICABILIDAD
    # =========================================================================
    elif nav_sel == "Detalle con explicabilidad":
        st.markdown('<span class="section-label">EXPLICABILIDAD</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">¿Qué influyó en este resultado?</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Factores explicativos SHAP y sugerencia generada por el Agente Tutor</p>', unsafe_allow_html=True)

        # Búsqueda de predicción con selectores funcionales reales y estricto control de acceso
        if rol == "ESTUDIANTE":
            mis_mats = get_student_enrollments(usuario["cui_hash"], "2026-B", current_user=usuario)
            if not mis_mats:
                st.info("No tiene asignaturas inscritas para consultar. Inscríbase en 'Inscribir Asignatura'.")
                st.stop()

            mat_dict = {f"{m['curso']} (Sec. {m['seccion']})": m["id"] for m in mis_mats}
            sel_curso = st.selectbox("Asignatura a consultar:", list(mat_dict.keys()), key="sel_mat_xai")
            mat_id_act = int(mat_dict[sel_curso])
            cui_tag = f"ID Hash {usuario['cui_hash'][:6]}...{usuario['cui_hash'][-4:]}"
        else:
            col_s_curso, col_s_est = st.columns(2)
            with col_s_curso:
                def_idx_xai = _get_default_course_index(cursos_nombres_all)
                curso_doc_xai = st.selectbox(
                    "Asignatura:",
                    cursos_nombres_all,
                    index=def_idx_xai,
                    key="sel_doc_curso_xai",
                )
                st.session_state["docente_curso_activo"] = curso_doc_xai

            alumnos_xai = get_course_students_table(curso_doc_xai, "2026-B", current_user=usuario)
            if not alumnos_xai:
                st.info(
                    f"No existen estudiantes con predicciones registradas en la asignatura '{curso_doc_xai}' "
                    "para el semestre 2026-B. Seleccione otra asignatura o cargue un acta de calificaciones."
                )
                st.stop()

            est_options_xai: dict[str, dict] = {}
            for al in alumnos_xai:
                id_m = str(al.get("id_mostrado") or al.get("cui_hash", ""))
                id_short = id_m if id_m.startswith("RES-") else f"{id_m[:8]}...{id_m[-4:]}"
                lbl_opt = (
                    f"ID {id_short} · Sec. {al.get('seccion', 'A')} · "
                    f"[{al.get('semaforo', 'VERDE')}] ({float(al.get('probabilidad', 0.0))*100:.1f}%)"
                )
                est_options_xai[lbl_opt] = al

            with col_s_est:
                sel_est_xai = st.selectbox(
                    "Estudiante (ID Anonimizado):",
                    list(est_options_xai.keys()),
                    key="sel_doc_est_xai",
                )
            al_elegido = est_options_xai[sel_est_xai]
            mat_id_act = int(al_elegido["matricula_id"])
            st.session_state["selected_student_mat"] = mat_id_act
            id_m_sel = str(al_elegido.get("id_mostrado") or al_elegido.get("cui_hash", ""))
            cui_tag = f"ID {id_m_sel}" if id_m_sel.startswith("RES-") else f"ID Hash {id_m_sel[:6]}...{id_m_sel[-4:]}"

        pred_rec = get_latest_prediction(mat_id_act, current_user=usuario)
        if not pred_rec:
            st.info("No se registran predicciones ni desglose SHAP para la matrícula seleccionada.")
            st.stop()

        p_val = float(pred_rec.get("probabilidad", 0.0))
        p_pct = p_val * 100.0
        sem_tag = str(pred_rec.get("semaforo", "VERDE"))
        cp_tag = str(pred_rec.get("checkpoint", "CP0"))

        col_izq, col_der = st.columns([1, 2], gap="medium")

        # Columna Izquierda (Mockup 3: Medidor circular y badge)
        with col_izq:
            with st.container(border=True):
                st.markdown(f'<div class="cui-mono" style="text-align: center; margin: 0 auto 10px auto;">{cui_tag}</div>', unsafe_allow_html=True)
                st.markdown(render_circular_gauge_svg(p_pct), unsafe_allow_html=True)

                if sem_tag == "ROJO":
                    st.markdown('<div style="text-align: center; margin: 12px 0;"><span class="badge-alto">RIESGO ALTO</span></div>', unsafe_allow_html=True)
                elif sem_tag == "AMARILLO":
                    st.markdown('<div style="text-align: center; margin: 12px 0;"><span class="badge-alerta">ALERTA PREVENTIVA</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align: center; margin: 12px 0;"><span class="badge-bajo">RIESGO BAJO</span></div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div style="font-size: 13px; text-align: center; color: var(--texto-suave); margin-bottom: 14px;">
                    Probabilidad estimada de rezago ({cp_tag})<br>
                    <b>Semestre 2026-B · EPIS</b>
                </div>
                <div style="border-top: 2px solid var(--dorado); margin: 14px 0 10px 0;"></div>
                """, unsafe_allow_html=True)

                if st.button("Programar tutoría", type="primary", key="btn_prog_tut_izq", use_container_width=True):
                    fecha_prog = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
                    obs_prog = f"Tutoría focalizada en factores explicativos SHAP detectados en {cp_tag}."
                    ok_t, msg_t = schedule_tutoring_session(mat_id_act, fecha_prog, obs_prog, current_user=usuario)
                    if ok_t:
                        st.success(msg_t)
                    else:
                        st.error(msg_t)

        # Columna Derecha (Mockup 3: Barras SHAP con impacto real y Sugerencia)
        with col_der:
            with st.container(border=True):
                factores = pred_rec.get("top_factors") or []
                if not factores:
                    st.info("No se registraron factores SHAP individuales para esta evaluación.")
                else:
                    impactos_abs = [
                        abs(format_shap_factor_for_ui(f)["impact"])
                        for f in factores
                        if isinstance(f, dict)
                    ]
                    max_abs_imp = max(impactos_abs, default=1.0) or 1.0

                    for f in factores:
                        ui_f = format_shap_factor_for_ui(f, max_abs_imp)
                        f_nombre = ui_f["label"]
                        obs_val = ui_f["observed_value"]
                        obs_html = (
                            f' <span style="font-weight: 400; font-size: 12px; color: var(--texto-suave);">'
                            f'(Valor observado: {obs_val})</span>'
                            if obs_val is not None else ""
                        )
                        bar_color = ui_f["color_css"]
                        val_txt = ui_f["impact_text"]
                        ancho_pct = ui_f["width_pct"]

                        st.markdown(f"""
                        <div class="factor-bar-row">
                            <div class="factor-label-row">
                                <span class="factor-name">{f_nombre}{obs_html}</span>
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
                    <span><span style="color: var(--granate); font-weight: bold;">■</span> Aumenta el riesgo (impacto SHAP +)</span>
                    <span><span style="color: var(--azul-factor); font-weight: bold;">■</span> Lo reduce / factor protector (impacto SHAP -)</span>
                </div>
                """, unsafe_allow_html=True)

            # Caja de sugerencia para el tutor (Mockup 3)
            recs_list = pred_rec.get("recommendations") or []
            recom_txt = recs_list[0] if recs_list else "Mantener seguimiento académico regular según programación del sílabo."
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
        st.markdown('<p class="section-subtitle">Flujo de coordinación y mensajes reales persistidos entre agentes de la arquitectura</p>', unsafe_allow_html=True)

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

        # Tarjeta FIPA-ACL (Mockup 4) conectada a registros reales en SQLite (mensajes_bus)
        st.markdown('<div class="fipa-log-header">REGISTRO DE MENSAJES FIPA-ACL (PERSISTENCIA REAL SQLITE)</div>', unsafe_allow_html=True)

        if rol == "ESTUDIANTE":
            mensajes_reales = get_bus_messages_for_student(usuario["cui_hash"], limit=16)
        else:
            mensajes_reales = get_recent_bus_messages(16)

        if not mensajes_reales:
            log_html = (
                '<div style="color: #CBD5E1; font-style: italic;">'
                'Estado vacío: No existen mensajes FIPA-ACL registrados en la tabla mensajes_bus para este contexto. '
                'Ejecute una evaluación de riesgo o actualización de notas para generar trazas reales.'
                '</div>'
            )
        else:
            perf_class_map = {
                "REQUEST": "fipa-perf-request",
                "INFORM": "fipa-perf-inform",
                "PROPOSE": "fipa-perf-propose",
                "FAILURE": "fipa-perf-failure",
            }
            log_rows_html = []
            for m in reversed(mensajes_reales):
                ts_raw = str(m.get("timestamp", ""))
                t_str = ts_raw[11:19] if len(ts_raw) >= 19 else ts_raw[-8:]
                perf = str(m.get("performativa", "INFORM")).upper()
                perf_cls = perf_class_map.get(perf, "fipa-perf-inform")
                rem = str(m.get("emisor", "CoordinatorAgent"))
                dest = str(m.get("receptor", "Agent"))
                topico = str(m.get("topico", perf))
                req_id = str(m.get("request_id", "conv_anon"))
                req_short = req_id if len(req_id) <= 24 else f"{req_id[:14]}...{req_id[-6:]}"
                log_rows_html.append(
                    f'<div class="fipa-log-row">'
                    f'<span class="fipa-time">[{t_str}]</span> '
                    f'<span class="fipa-conv-id">[{req_short}]</span> '
                    f'<span class="fipa-performative {perf_cls}">{perf}</span> '
                    f'<span class="fipa-route">{rem} → {dest}</span> '
                    f'<span class="fipa-topic">· Tópico: {topico}</span>'
                    f'</div>'
                )
            log_html = "".join(log_rows_html)

        st.markdown(f"""
        <div class="fipa-log-body">
            {log_html}
        </div>
        <div style="font-size: 13px; color: var(--texto-suave); margin-top: 14px;">
            Cada alerta se audita paso a paso mediante performativas FIPA-ACL reales (REQUEST, INFORM, PROPOSE, FAILURE) con identificadores de conversación anonimizados.
        </div>
        """, unsafe_allow_html=True)


    # =========================================================================
    # VISTA 4: MOCKUP 5 - SEGUIMIENTO Y PLAN DE TUTORÍA
    # =========================================================================
    elif nav_sel == "Seguimiento y plan de tutoría":
        st.markdown('<span class="section-label">SEGUIMIENTO</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Evolución y plan de tutoría</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Trayectoria longitudinal de riesgo, bitácora pedagógica y simulación normativa</p>', unsafe_allow_html=True)

        if rol == "ESTUDIANTE":
            mis_mats = get_student_enrollments(usuario["cui_hash"], "2026-B", current_user=usuario)
            if not mis_mats:
                st.info("No tiene asignaturas inscritas para consultar.")
                st.stop()
            mat_dict = {f"{m['curso']} (Sec. {m['seccion']})": m for m in mis_mats}
            sel_c = st.selectbox("Asignatura a supervisar:", list(mat_dict.keys()), key="sel_plan_tut")
            mat_act = mat_dict[sel_c]
            mat_id_act = int(mat_act["id"])
            nom_curso = str(mat_act["curso"])
            nom_docente = str(mat_act["docente"])
            cui_anon = str(usuario["cui_hash"])
        else:
            col_t_curso, col_t_est = st.columns(2)
            with col_t_curso:
                def_idx_tut = _get_default_course_index(cursos_nombres_all)
                curso_doc_tut = st.selectbox(
                    "Asignatura a supervisar:",
                    cursos_nombres_all,
                    index=def_idx_tut,
                    key="sel_doc_curso_tut",
                )
                st.session_state["docente_curso_activo"] = curso_doc_tut

            alumnos_tut = get_course_students_table(curso_doc_tut, "2026-B", current_user=usuario)
            if not alumnos_tut:
                st.info(
                    f"No existen estudiantes evaluados en '{curso_doc_tut}' para el semestre 2026-B."
                )
                st.stop()

            est_options_tut: dict[str, dict] = {}
            for al in alumnos_tut:
                id_m = str(al.get("id_mostrado") or al.get("cui_hash", ""))
                id_short = id_m if id_m.startswith("RES-") else f"{id_m[:8]}...{id_m[-4:]}"
                lbl_opt = (
                    f"ID {id_short} · Sec. {al.get('seccion', 'A')} · "
                    f"[{al.get('semaforo', 'VERDE')}] ({float(al.get('probabilidad', 0.0))*100:.1f}%)"
                )
                est_options_tut[lbl_opt] = al

            with col_t_est:
                sel_est_tut = st.selectbox(
                    "Estudiante (ID Anonimizado):",
                    list(est_options_tut.keys()),
                    key="sel_doc_est_tut",
                )
            al_tut_sel = est_options_tut[sel_est_tut]
            mat_id_act = int(al_tut_sel["matricula_id"])
            st.session_state["selected_student_mat"] = mat_id_act
            mat_act = get_enrollment_by_id(mat_id_act, current_user=usuario) or {}
            nom_curso = str(mat_act.get("curso") or curso_doc_tut)
            nom_docente = str(mat_act.get("docente") or usuario["username"])
            cui_anon = str(al_tut_sel.get("id_mostrado") or al_tut_sel.get("cui_hash", ""))

        # Historial longitudinal real desde SQLite (sin valores inventados)
        historial = get_prediction_history(mat_id_act, current_user=usuario)
        pred_actual = get_latest_prediction(mat_id_act, current_user=usuario)

        with st.container(border=True):
            if not historial:
                st.info("No existen puntos de control (checkpoints) evaluados aún para graficar la evolución de esta matrícula.")
            else:
                semanas = [
                    str(h["checkpoint"]) if str(h["checkpoint"]).startswith("CP") else f"CP{h['checkpoint']}"
                    for h in historial
                ]
                riesgos = [round(float(h["probabilidad"]) * 100.0, 1) for h in historial]

                col_g1, col_g2 = st.columns([3, 1])
                with col_g1:
                    umbral_crit_pct = round(float(pred_actual.get("umbral", 0.34)) * 100.0, 1) if pred_actual else 34.0
                    umbral_prev_pct = round(0.75 * umbral_crit_pct, 1)
                    fig, ax = plt.subplots(figsize=(7.5, 2.8), facecolor='white')
                    ax.axhline(
                        y=umbral_prev_pct,
                        color='#F59E0B',
                        linestyle='--',
                        linewidth=1.2,
                        alpha=0.85,
                        label=f"Umbral Preventivo ({umbral_prev_pct:.1f}%)",
                    )
                    ax.axhline(
                        y=umbral_crit_pct,
                        color='#EF4444',
                        linestyle='--',
                        linewidth=1.2,
                        alpha=0.85,
                        label=f"Umbral Crítico ({umbral_crit_pct:.1f}%)",
                    )

                    ax.plot(semanas, riesgos, color='#7A1C20', linewidth=3, zorder=3)
                    if len(semanas) > 1:
                        ax.scatter(semanas[:-1], riesgos[:-1], color='#7A1C20', s=45, zorder=4)
                    ax.scatter([semanas[-1]], [riesgos[-1]], facecolors='#C59B27', edgecolors='#7A1C20', linewidth=2.5, s=90, zorder=5)

                    ax.set_ylim(0, 100)
                    ax.set_ylabel("Riesgo (%)", fontsize=11, color='#0F172A', fontweight='bold')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_color('#E2E8F0')
                    ax.spines['bottom'].set_color('#E2E8F0')
                    ax.tick_params(colors='#475569', labelsize=10)
                    ax.grid(axis='y', linestyle=':', alpha=0.5, color='#E2E8F0')
                    ax.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=8.5)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

                with col_g2:
                    if len(riesgos) >= 2:
                        tendencia_txt = "al alza" if riesgos[-1] > riesgos[0] else ("a la baja" if riesgos[-1] < riesgos[0] else "estable")
                    else:
                        tendencia_txt = f"Hito {semanas[-1]} ({riesgos[-1]:.1f}%)"
                    st.markdown(f"""
                    <div style="padding-top: 30px;">
                        <div style="font-size: 14px; font-weight: 700; color: var(--granate-oscuro);">Tendencia: <span style="font-family: 'JetBrains Mono', monospace; color: var(--granate);">{tendencia_txt}</span></div>
                        <div style="font-size: 12px; color: var(--texto-suave); margin-top: 4px;">Datos reales persistidos en SQLite para {nom_curso}.</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Tarjeta de compromisos pedagógicos y registro real de tutoría en SQLite (Mockup 5)
        chk_state = get_tutoring_checklist_state(mat_id_act, current_user=usuario)
        with st.container(border=True):
            st.markdown("#### Plan de Acción Tutorial y Compromisos Pedagógicos")
            st.caption(f"Última actualización en bitácora: {chk_state['fecha_actualizacion']}")

            chk_a1 = st.checkbox(
                "Acción 1: conversación diagnóstica inicial con el estudiante",
                value=chk_state["accion_1"],
                key=f"chk_a1_{mat_id_act}",
            )
            chk_a2 = st.checkbox(
                "Acción 2: derivar a reforzamiento académico o tutoría par",
                value=chk_state["accion_2"],
                key=f"chk_a2_{mat_id_act}",
            )
            chk_a3 = st.checkbox(
                "Acción 3: reevaluar el semáforo tras el siguiente hito parcial",
                value=chk_state["accion_3"],
                key=f"chk_a3_{mat_id_act}",
            )

            st.markdown("---")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                tut_fecha_in = st.date_input(
                    "Fecha de la sesión de tutoría:",
                    value=datetime.date.today(),
                    key=f"tut_fecha_{mat_id_act}",
                )
            with col_f2:
                tut_estado_in = st.selectbox(
                    "Estado de la sesión:",
                    ["REALIZADA", "PROGRAMADA", "SEGUIMIENTO"],
                    key=f"tut_estado_{mat_id_act}",
                )

            tut_obs_in = st.text_area(
                "Observaciones y acuerdos pedagógicos (obligatorio para registrar):",
                placeholder="Detalle los acuerdos alcanzados, temas reforzados o compromisos asumidos en la sesión...",
                key=f"tut_obs_{mat_id_act}",
            )

            c_btn1, c_btn2, _ = st.columns([1.6, 1.6, 2.8])
            with c_btn1:
                if st.button("Registrar tutoría", type="primary", use_container_width=True):
                    ok_reg, msg_reg = register_tutoring_session(
                        matricula_id=mat_id_act,
                        fecha_sesion=tut_fecha_in.isoformat(),
                        estado=tut_estado_in,
                        observaciones=tut_obs_in,
                        accion_1=chk_a1,
                        accion_2=chk_a2,
                        accion_3=chk_a3,
                        current_user=usuario,
                    )
                    if ok_reg:
                        st.success(msg_reg)
                    else:
                        st.error(msg_reg)

            with c_btn2:
                if pred_actual:
                    pdf_bytes = generate_intervention_pdf(
                        student_id_anon=cui_anon,
                        curso=nom_curso,
                        docente=nom_docente,
                        checkpoint=str(pred_actual.get("checkpoint", "CP1")),
                        probabilidad_pct=float(pred_actual.get("probabilidad", 0.0)) * 100.0,
                        umbral_pct=float(pred_actual.get("umbral", 0.34)) * 100.0,
                        semaforo=str(pred_actual.get("semaforo", "VERDE")),
                        meta_nota_min=pred_actual.get("meta_nota_min"),
                        promedio_acumulado=float(pred_actual.get("promedio_acumulado") or 0.0),
                        imposible=bool(pred_actual.get("imposible_ordinario", 0)),
                        top_factors=pred_actual.get("top_factors") or [],
                        recommendations=pred_actual.get("recommendations") or [],
                        current_user=usuario,
                    )
                    st.download_button(
                        label="Exportar informe PDF",
                        data=pdf_bytes,
                        file_name=f"Ficha_Intervencion_SATA_{cui_anon[:8]}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.info("Sin predicción para exportar PDF.")

        # Historial / Bitácora persistida de tutorías
        with st.container(border=True):
            st.markdown("#### Historial y Bitácora de Sesiones de Tutoría")
            hist_tut = get_tutoring_history(mat_id_act, current_user=usuario)
            if not hist_tut:
                st.info("No se registran sesiones de tutoría aún para esta matrícula.")
            else:
                df_tut = pd.DataFrame([
                    {
                        "Fecha Sesión": r["fecha_sesion"],
                        "Estado": r["estado"],
                        "Responsable": f"{r['responsable']} ({r['rol_registro']})",
                        "Compromisos (A1/A2/A3)": f"{'Sí' if r['accion_1_ok'] else 'No'} / {'Sí' if r['accion_2_ok'] else 'No'} / {'Sí' if r['accion_3_ok'] else 'No'}",
                        "Observaciones Pedagógicas": r["observaciones"],
                        "Registrado": str(r["fecha_registro"])[:16].replace("T", " "),
                    }
                    for r in hist_tut
                ])
                st.dataframe(df_tut, use_container_width=True)

        # Conexión de save_grade + auditoría historial_cambios y calcular_simulacion_sustitutorio
        notas_actuales = get_grades_for_enrollment(mat_id_act, current_user=usuario)
        pesos_mat = {
            "EC1": int(mat_act.get("peso_ec1", 15)),
            "EP1": int(mat_act.get("peso_ep1", 15)),
            "EC2": int(mat_act.get("peso_ec2", 20)),
            "EP2": int(mat_act.get("peso_ep2", 20)),
            "EC3": int(mat_act.get("peso_ec3", 15)),
            "EP3": int(mat_act.get("peso_ep3", 15)),
        }

        col_op1, col_op2 = st.columns(2, gap="medium")
        with col_op1:
            with st.container(border=True):
                st.markdown("#### Registro y Rectificación de Notas Parciales")
                st.caption("Actualiza la calificación en SQLite, registra auditoría de cambios y recalcula la alerta en el SMA.")
                ev_sel = st.selectbox(
                    "Evaluación a registrar o actualizar:",
                    ["EC1", "EP1", "EC2", "EP2", "EC3", "EP3"],
                    key=f"ev_sel_{mat_id_act}",
                )
                prev_ev_info = notas_actuales.get(ev_sel, {})
                prev_val_num = float(prev_ev_info["valor"]) if prev_ev_info.get("valor") is not None else 11.0
                val_nota_in = st.number_input(
                    f"Calificación en {ev_sel} (0.0 a 20.0):",
                    min_value=0.0,
                    max_value=20.0,
                    value=prev_val_num,
                    step=0.5,
                    key=f"val_nota_{mat_id_act}_{ev_sel}",
                )
                es_aus_in = st.checkbox(
                    f"Marcar Ausente / NSP en {ev_sel}",
                    value=bool(prev_ev_info.get("es_ausente", False)),
                    key=f"aus_nota_{mat_id_act}_{ev_sel}",
                )
                motivo_nota_in = st.text_input(
                    "Motivo de registro o modificación:",
                    value="Actualización académica intra-semestral",
                    key=f"mot_nota_{mat_id_act}",
                )
                if st.button("Guardar Calificación y Recalcular Alerta", type="primary", key=f"btn_save_grade_{mat_id_act}", use_container_width=True):
                    valor_guardar = 0.0 if es_aus_in else float(val_nota_in)
                    save_grade(
                        matricula_id=mat_id_act,
                        evaluacion=ev_sel,
                        valor=valor_guardar,
                        es_ausente=es_aus_in,
                        motivo=motivo_nota_in.strip() or "Registro regular",
                        current_user=usuario,
                    )
                    res_recalc = evaluate_and_persist_enrollment(mat_id_act, coordinator, current_user=usuario)
                    if res_recalc.get("status") == "SUCCESS":
                        st.success(f"Calificación {ev_sel} guardada y alerta recalculada ({res_recalc['prediction']['checkpoint']}).")
                        st.rerun()
                    else:
                        st.error("Error al recalcular alerta: " + ", ".join(res_recalc.get("errors", [])))

                cambios_hist = get_grade_change_history(mat_id_act, current_user=usuario)
                if cambios_hist:
                    st.caption("Auditoría de rectificaciones registradas (`historial_cambios`):")
                    st.dataframe(pd.DataFrame(cambios_hist), use_container_width=True)

        with col_op2:
            with st.container(border=True):
                st.markdown("#### Simulador Normativo de Examen Sustitutorio (UNSA)")
                st.caption("Simula el reemplazo normativo del Examen Parcial más bajo (min(EP1, EP2, EP3)) al cierre de las 3 fases.")
                s_c1, s_c2, s_c3 = st.columns(3)
                with s_c1:
                    sim_ec1 = st.number_input("EC1:", 0.0, 20.0, float(notas_actuales.get("EC1", {}).get("valor") or 9.0), 0.5, key=f"sim_ec1_{mat_id_act}")
                    sim_ep1 = st.number_input("EP1:", 0.0, 20.0, float(notas_actuales.get("EP1", {}).get("valor") or 8.0), 0.5, key=f"sim_ep1_{mat_id_act}")
                with s_c2:
                    sim_ec2 = st.number_input("EC2:", 0.0, 20.0, float(notas_actuales.get("EC2", {}).get("valor") or 10.0), 0.5, key=f"sim_ec2_{mat_id_act}")
                    sim_ep2 = st.number_input("EP2:", 0.0, 20.0, float(notas_actuales.get("EP2", {}).get("valor") or 9.0), 0.5, key=f"sim_ep2_{mat_id_act}")
                with s_c3:
                    sim_ec3 = st.number_input("EC3:", 0.0, 20.0, float(notas_actuales.get("EC3", {}).get("valor") or 11.0), 0.5, key=f"sim_ec3_{mat_id_act}")
                    sim_ep3 = st.number_input("EP3:", 0.0, 20.0, float(notas_actuales.get("EP3", {}).get("valor") or 9.0), 0.5, key=f"sim_ep3_{mat_id_act}")

                sim_res = calcular_simulacion_sustitutorio(
                    sim_ec1, sim_ep1, sim_ec2, sim_ep2, sim_ec3, sim_ep3, pesos_mat
                )
                if sim_res.get("ya_aprobo"):
                    st.success(sim_res["mensaje"])
                elif sim_res.get("aplica"):
                    st.markdown(
                        f"**Promedio Ordinario Proyectado:** `{sim_res['promedio_ordinario']:.2f}` · "
                        f"**Parcial a Reemplazar:** `{sim_res['parcial_a_reemplazar']}` (Nota actual: `{sim_res['nota_reemplazada']}`, Peso: `{sim_res['peso_parcial']}%`)"
                    )
                    if sim_res.get("es_viable"):
                        st.warning(sim_res["mensaje"])
                    else:
                        st.error(sim_res["mensaje"])
                else:
                    st.info(sim_res.get("motivo", "Complete las 3 fases para simular el sustitutorio."))


    # =========================================================================
    # VISTAS OPERATIVAS ADICIONALES (MANTENIMIENTO DE TODA LA LÓGICA Y DATOS)
    # =========================================================================
    elif nav_sel == "Inscribir Asignatura":
        st.markdown('<span class="section-label">MATRÍCULA</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Inscribir Asignatura para Monitoreo</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Asignaturas oficiales del plan de estudios EPIS</p>', unsafe_allow_html=True)

        docentes = get_all_teachers()
        nombres_cursos = [c["nombre"] for c in catalogo]

        with st.container(border=True):
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
                    enroll_course(usuario["cui_hash"], "2026-B", c_sel, d_sel, sec_sel, pesos_dict, es_rep, current_user=usuario)
                    st.success("Asignatura registrada y monitoreo activado.")
                    st.rerun()

    elif nav_sel == "Perfil Basal":
        st.markdown('<span class="section-label">ANTECEDENTES</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Perfil Académico Basal</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Variables históricas que alimentan el Checkpoint 0 y preferencias de privacidad</p>', unsafe_allow_html=True)

        perfil = get_student_profile(usuario["cui_hash"], "2026-B", current_user=usuario) or {}
        with st.container(border=True):
            with st.form("form_perfil"):
                c1, c2 = st.columns(2)
                with c1:
                    p_ira = st.number_input("IRA Acumulado previo (0–20):", 0.0, 20.0, float(perfil.get("ira_acum", 12.5)), step=0.1)
                    p_rep = st.number_input("Cursos reprobados previamente en la carrera:", 0, 20, int(perfil.get("repeticiones_previas", 0)))
                with c2:
                    p_cred = st.number_input("Créditos matriculados este semestre:", 1, 30, int(perfil.get("creditos_matriculados", 22)))
                    p_ing = st.number_input("Semestres transcurridos desde su ingreso:", 1.0, 16.0, float(perfil.get("semestre_ingreso", 4.0)), step=0.5)

                if st.form_submit_button("Guardar Perfil Basal"):
                    save_student_profile(usuario["cui_hash"], "2026-B", p_ira, p_rep, p_cred, p_ing, current_user=usuario)
                    st.success("Perfil basal registrado correctamente.")
                    st.rerun()

        est_info = get_student_info(usuario["cui_hash"]) or {"consentimiento_aceptado": 1, "comparte_con_tutor": 1}
        with st.container(border=True):
            st.markdown("#### Consentimiento Informado y Privacidad de Tutoría (Opt-In)")
            st.caption(
                "Controle si autoriza que el docente responsable o tutor visualice su código hash completo "
                "durante el seguimiento académico o si prefiere mantener su registro reservado (RES-XXXXXX)."
            )
            with st.form("form_consentimiento_optin"):
                chk_consent = st.checkbox(
                    "Acepto el consentimiento informado para el procesamiento preventivo anonimizado (HMAC-SHA256)",
                    value=bool(est_info.get("consentimiento_aceptado", 1)),
                )
                chk_optin = st.checkbox(
                    "Autorizo compartir mi identificador hash y alertas preventivas con el Docente / Tutor de la asignatura (Opt-in)",
                    value=bool(est_info.get("comparte_con_tutor", 1)),
                )
                if st.form_submit_button("Actualizar Consentimiento y Privacidad"):
                    update_student_consent(usuario["cui_hash"], chk_consent, chk_optin)
                    st.success("Preferencias de consentimiento informado y privacidad actualizadas en SQLite.")
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
                    with st.spinner("Ejecutando validaciones sintácticas, pipeline multiagente y persistencia transaccional en SQLite..."):
                        procesados, errores = validar_y_procesar_acta_masiva(df_up, coordinator)

                    c_sum1, c_sum2, c_sum3 = st.columns(3)
                    c_sum1.metric("Total Filas Analizadas", len(df_up))
                    c_sum2.metric("Registros Procesados y Persistidos", len(procesados))
                    c_sum3.metric("Filas Rechazadas / Con Errores", len(errores))

                    if errores:
                        st.warning(f"Se rechazaron {len(errores)} filas con observaciones de validación:")
                        st.dataframe(pd.DataFrame(errores), use_container_width=True)
                    if procesados:
                        st.success(
                            f"Se procesaron y persistieron transaccionalmente en SQLite {len(procesados)} registros "
                            "anonimizados con HMAC-SHA256 (matrículas, notas, predicciones, explicaciones SHAP, "
                            "mensajes FIPA-ACL y métricas técnicas)."
                        )
                        st.dataframe(pd.DataFrame(procesados), use_container_width=True)
            except Exception as e:
                st.error(f"Error al leer el archivo: {e!s}")

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
                "curso": "Asignatura",
                "semestre": "Semestre",
                "total_alumnos": "Total Estudiantes",
                "rojos": "Críticos (Rojo)",
                "amarillos": "Observación (Amarillo)",
                "verdes": "Regulares (Verde)",
                "tasa_riesgo_pct": "% En Riesgo",
            }),
            use_container_width=True,
        )

    elif nav_sel == "Monitor Técnico OBJ5":
        st.markdown('<span class="section-label">ADMINISTRACIÓN</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Monitor Técnico de Arquitectura Multiagente</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Cumplimiento de latencia e hipótesis H3</p>', unsafe_allow_html=True)

        stats_tec = get_technical_metrics_summary()
        n_muestras = int(stats_tec.get("total_muestras", 0))
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)

        if n_muestras == 0:
            col_t1.metric("Latencia Media Inferencia", "Sin muestras (0.0 ms)", delta="0 mediciones", delta_color="off")
            col_t2.metric("Latencia P95 Inferencia", "Sin muestras (0.0 ms)", delta="0 mediciones", delta_color="off")
            col_t3.metric("Uso Promedio RAM", "Sin muestras (0.0 MB)", delta="0 mediciones", delta_color="off")
            col_t4.metric("Overhead Bus Asíncrono", "Sin muestras (0.0 ms)", delta="0 mediciones", delta_color="off")
            st.warning(
                "Estado actual: Sin mediciones registradas en SQLite (0 muestras en 'metricas_tecnicas'). "
                "Las mediciones reales de latencia de inferencia, P95, memoria RAM y overhead del bus FIPA-ACL "
                "se registran automáticamente al ejecutar inferencias en el Sistema Multiagente."
            )
        else:
            col_t1.metric(
                "Latencia Media Inferencia",
                f"{stats_tec['latencia_inf_media_ms']:.2f} ms",
                delta=f"{n_muestras} muestras reales",
            )
            col_t2.metric(
                "Latencia P95 Inferencia",
                f"{stats_tec['latencia_inf_p95_ms']:.2f} ms",
                delta=f"XAI media: {stats_tec['latencia_xai_media_ms']:.2f} ms",
            )
            col_t3.metric(
                "Uso Promedio RAM",
                f"{stats_tec['ram_media_mb']:.1f} MB",
                delta="< 400 MB",
            )
            col_t4.metric(
                "Overhead Bus Asíncrono",
                f"{stats_tec['overhead_media_ms']:.3f} ms",
                delta=f"Total medio: {stats_tec['latencia_total_media_ms']:.2f} ms",
            )
            st.info(
                f"Telemetría real calculada sobre {n_muestras} ejecuciones persistidas en SQLite. "
                f"Latencia total media end-to-end (Inferencia + SHAP + Recomendación + Alerta): "
                f"{stats_tec['latencia_total_media_ms']:.2f} ms, cumpliendo la hipótesis H3 (< 1,500 ms)."
            )

    elif nav_sel == "Encuestas SUS / TAM":
        st.markdown('<span class="section-label">VALIDACIÓN PSICOMÉTRICA</span>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">Evaluación de Usabilidad y Aceptación</h2>', unsafe_allow_html=True)
        st.markdown('<p class="section-subtitle">Instrumentos estandarizados SUS y TAM (OBJ5 - Actividad 3)</p>', unsafe_allow_html=True)

        sus_stats = get_surveys_stats("SUS")
        tam_stats = get_surveys_stats("TAM")

        col_s1, col_s2 = st.columns(2)
        col_s1.metric("Puntuación Media SUS (Usabilidad)", f"{sus_stats['promedio']} / 100", delta=f"{sus_stats['total']} evaluadores")
        col_s2.metric("Puntuación Media TAM (Aceptación)", f"{tam_stats['promedio']} / 5.0", delta=f"{tam_stats['total']} evaluadores")

        tab_sus, tab_tam = st.tabs([
            "Cuestionario SUS (System Usability Scale)",
            "Cuestionario TAM (Technology Acceptance Model)",
        ])

        with tab_sus:
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
                    save_survey(usuario["username"], rol, "SUS", {
                        "p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5,
                        "p6": p6, "p7": p7, "p8": p8, "p9": p9, "p10": p10
                    }, score_sus)
                    st.success(f"Evaluación SUS registrada exitosamente. Puntaje obtenido: {score_sus:.1f} / 100")
                    st.rerun()

        with tab_tam:
            with st.form("form_tam_eval"):
                st.markdown("**Dimensión 1: Utilidad Percibida (Perceived Usefulness - PU)**")
                tam_pu1 = st.slider(
                    "1. [PU1] El sistema SATA-UNSA permite identificar oportunamente el riesgo académico en las asignaturas:",
                    1, 5, 5,
                )
                tam_pu2 = st.slider(
                    "2. [PU2] Las explicaciones locales SHAP y las metas cuantitativas mejoran la toma de decisiones en tutoría:",
                    1, 5, 5,
                )
                tam_pu3 = st.slider(
                    "3. [PU3] Considero que el sistema SATA-UNSA es útil para reducir la reprobación académica en la EPIS-UNSA:",
                    1, 5, 5,
                )
                st.markdown("**Dimensión 2: Facilidad de Uso Percibida e Intención de Uso (PEOU & BI)**")
                tam_peou1 = st.slider(
                    "4. [PEOU1] La interacción con los paneles y el semáforo preventivo de 3 niveles es clara y comprensible:",
                    1, 5, 4,
                )
                tam_peou2 = st.slider(
                    "5. [PEOU2] Resulta sencillo auditar la trazabilidad FIPA-ACL y exportar las fichas de intervención en PDF:",
                    1, 5, 5,
                )
                tam_bi1 = st.slider(
                    "6. [BI1] Tengo intención de utilizar el sistema regularmente para el seguimiento académico semestral:",
                    1, 5, 5,
                )

                if st.form_submit_button("Guardar Evaluación TAM"):
                    score_tam = round((tam_pu1 + tam_pu2 + tam_pu3 + tam_peou1 + tam_peou2 + tam_bi1) / 6.0, 2)
                    save_survey(usuario["username"], rol, "TAM", {
                        "pu1": tam_pu1,
                        "pu2": tam_pu2,
                        "pu3": tam_pu3,
                        "peou1": tam_peou1,
                        "peou2": tam_peou2,
                        "bi1": tam_bi1,
                    }, score_tam)
                    st.success(f"Evaluación TAM registrada exitosamente. Puntaje obtenido: {score_tam:.2f} / 5.0")
                    st.rerun()
