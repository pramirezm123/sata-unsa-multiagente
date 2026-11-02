"""
Generador de Ficha de Intervención Tutorial y Alerta Temprana en PDF (fpdf2).
Cumple con:
- Cero nombres y Cero CUI (estrictamente anonimizado por hash ID).
- Tipografía segura en Latin-1 / UTF-8 sin caracteres que rompan la compilación.
- Formato institucional oficial UNSA - EPIS para tutores y docentes.
"""
from datetime import datetime
from typing import Any

from fpdf import FPDF


def sanitize_text(text: str) -> str:
    """Reemplaza caracteres especiales o matemáticos que puedan fallar en fuentes base."""
    if text is None:
        return ""
    replacements = {
        "≥": ">=",
        "≤": "<=",
        "≠": "!=",
        "–": "-",
        "—": "-",
        "•": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "\U0001F534": "[ALTO RIESGO]",
        "\U0001F7E1": "[RIESGO MEDIO]",
        "\U0001F7E2": "[BAJO RIESGO]",
        "\u26A0": "[ALERTA]"
    }
    s = str(text)
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


class SataReportPDF(FPDF):
    def header(self):
        # Encabezado institucional
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(31, 78, 121) # Azul institucional
        self.cell(0, 5, sanitize_text("UNIVERSIDAD NACIONAL DE SAN AGUSTIN DE AREQUIPA"), new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 4, sanitize_text("Facultad de Ingenieria de Produccion y Servicios | Escuela Profesional de Ingenieria de Sistemas"), new_x="LMARGIN", new_y="NEXT", align="C")
        self.cell(0, 4, sanitize_text("SATA-UNSA: Sistema de Alerta Temprana con Sistemas Multiagente y XAI"), new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(2)
        self.set_draw_color(31, 78, 121)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        # Pie de página con advertencia ética y numeración
        self.set_y(-20)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(120, 120, 120)
        warning_msg = (
            "CONFIDENCIALIDAD: Este documento contiene informacion academica anonimizada protegida. "
            "El resultado emitido constituye una estimacion predictiva probabilistica y no representa una sentencia academica definitiva."
        )
        self.multi_cell(0, 3.2, sanitize_text(warning_msg), align="C")
        self.set_y(-8)
        self.cell(0, 4, f"Pagina {self.page_no()}", align="R")


def generate_intervention_pdf(
    student_id_anon: str,
    curso: str,
    docente: str,
    checkpoint: str,
    probabilidad_pct: float,
    umbral_pct: float,
    semaforo: str,
    meta_nota_min: float | None,
    promedio_acumulado: float,
    imposible: bool,
    top_factors: list[dict[str, Any]],
    recommendations: list[str]
) -> bytes:
    """Genera el binario PDF de la ficha de intervención tutorial."""
    pdf = SataReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    # Título del reporte
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 7, sanitize_text("FICHA DE INTERVENCION TUTORIAL Y ALERTA TEMPRANA"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, sanitize_text(f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Version del Sistema: SATA-UNSA v1.0"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # 1. Resumen de Diagnóstico (Caja de Alerta)
    color_map = {
        "ROJO": (211, 47, 47),
        "AMARILLO": (245, 127, 23),
        "VERDE": (56, 142, 60)
    }
    r_col, g_col, b_col = color_map.get(semaforo.upper(), (100, 100, 100))

    pdf.set_fill_color(r_col, g_col, b_col)
    pdf.rect(10, pdf.get_y(), 190, 14, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, pdf.get_y() + 2)
    pdf.cell(0, 5, sanitize_text(f"ESTADO DE ALERTA: [{semaforo.upper()}] - {checkpoint}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_xy(12, pdf.get_y())
    desc_alerta = f"Probabilidad Estimada de Reprobacion: {probabilidad_pct:.1f}% | Umbral Calibrado: {umbral_pct:.1f}%"
    pdf.cell(0, 5, sanitize_text(desc_alerta), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 2. Datos de Identificación Anonimizada
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 5, sanitize_text("1. DATOS DE IDENTIFICACION ACADEMICA (PRIVACIDAD PROTEGIDA)"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(20, 20, 20)
    pdf.set_draw_color(210, 210, 210)
    pdf.set_fill_color(248, 249, 250)

    col_w1, col_w2 = 60, 130
    h_row = 6

    def draw_kv(k, v):
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(col_w1, h_row, sanitize_text(f"  {k}"), border=1, fill=True)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(col_w2, h_row, sanitize_text(f"  {v}"), border=1, new_x="LMARGIN", new_y="NEXT")

    draw_kv("Identificador de Estudiante (Hash CUI):", student_id_anon)
    draw_kv("Asignatura:", curso)
    draw_kv("Docente Responsable:", docente)
    draw_kv("Hito de Evaluacion Activo:", f"{checkpoint} (Insumos completados)")
    
    if meta_nota_min is not None:
        meta_txt = f"{meta_nota_min:.1f} / 20" if meta_nota_min <= 20 else "IMPOSIBLE EN ORDINARIO (Requiere Sustitutorio)"
        draw_kv("Nota Minima en Pendientes para Aprobar (11):", meta_txt)
    else:
        draw_kv("Promedio Ponderado Acumulado Ordinario:", f"{promedio_acumulado:.2f} / 20")

    pdf.ln(4)

    # 3. Factores Explicativos de Riesgo (XAI - SHAP)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 5, sanitize_text("2. FACTORES EXPLICATIVOS DEL RIESGO (IA EXPLICABLE - SHAP)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 4, sanitize_text("Desglose cuantitativo en lenguaje llano de las causas que determinan la alerta:"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    if top_factors:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(230, 235, 245)
        pdf.cell(60, 5, sanitize_text("  Factor Identificado"), border=1, fill=True)
        pdf.cell(35, 5, sanitize_text("  Valor Observado"), border=1, fill=True)
        pdf.cell(35, 5, sanitize_text("  Efecto en Riesgo"), border=1, fill=True)
        pdf.cell(60, 5, sanitize_text("  Impacto en la Probabilidad"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        for f in top_factors[:5]:
            lbl = f.get("label", "Factor")
            val = str(f.get("value", "-"))
            dir_f = f.get("direction", "Riesgo")
            imp = f"{f.get('impact', 0.0):+.4f}"
            
            pdf.cell(60, 5, sanitize_text(f"  {lbl[:35]}"), border=1)
            pdf.cell(35, 5, sanitize_text(f"  {val}"), border=1)
            pdf.cell(35, 5, sanitize_text(f"  {dir_f}"), border=1)
            pdf.cell(60, 5, sanitize_text(f"  {imp}"), border=1, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.cell(0, 5, sanitize_text("No se registraron factores de riesgo criticos (estudiante en situacion regular)."), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # 4. Recomendaciones Pedagógicas y Plan de Acción
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 5, sanitize_text("3. ACCIONES DE TUTORIA Y NIVELACION RECOMENDADAS"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(20, 20, 20)
    if recommendations:
        for i, rec in enumerate(recommendations, start=1):
            pdf.multi_cell(0, 4.5, sanitize_text(f"  [{i}] {rec}"))
            pdf.ln(1)
    else:
        pdf.multi_cell(0, 4.5, sanitize_text("  - Mantener seguimiento regular del desempeno academico en las siguientes fases."))

    pdf.ln(4)

    # 5. Sección para Seguimiento del Tutor / Comité
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(0, 5, sanitize_text("4. REGISTRO Y CONFORMIDAD DE INTERVENCION TUTORIAL"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_draw_color(180, 180, 180)
    pdf.rect(10, pdf.get_y(), 190, 25)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.set_xy(12, pdf.get_y() + 2)
    pdf.cell(0, 4, sanitize_text("Observaciones y acuerdos de la sesion de tutoria con el estudiante:"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(22)

    # Líneas de firmas
    y_sig = pdf.get_y() + 5
    pdf.set_line_width(0.4)
    pdf.set_draw_color(100, 100, 100)
    pdf.line(25, y_sig, 85, y_sig)
    pdf.line(125, y_sig, 185, y_sig)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(25, y_sig + 1)
    pdf.cell(60, 4, sanitize_text("Firma del Docente / Tutor"), align="C")
    pdf.set_xy(125, y_sig + 1)
    pdf.cell(60, 4, sanitize_text("Firma de Conformidad del Estudiante"), align="C")

    # Retornar buffer de bytes
    return bytes(pdf.output())
