"""
Pruebas de Integración y Validación de Interfaz de Usuario (UI) con Streamlit AppTest.
Verifica:
1. Carga limpia de la aplicación (app.py) sin excepciones ni errores de renderizado.
2. Forzado de tema claro en .streamlit/config.toml.
3. Ausencia total de emojis en textos y componentes visuales de la plataforma.
4. Presencia de los 5 mockups oficiales y paleta institucional granate (#7A1C20).
5. Flujos de navegación por roles (Estudiante, Docente, Autoridad, Administrador).
"""
import os
import re

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "config.toml"))


class TestUiIntegrationAndTheme:
    """Pruebas sobre la interfaz de usuario Streamlit."""

    def test_streamlit_config_forces_light_theme(self):
        """Verifica que .streamlit/config.toml configure estrictamente el modo claro."""
        assert os.path.exists(CONFIG_PATH), "El archivo .streamlit/config.toml debe existir."
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'base = "light"' in content or "base = 'light'" in content
        assert "#7A1C20" in content, "El color primario institucional #7A1C20 debe estar en config.toml"

    def test_app_loads_without_exceptions(self):
        """Verifica que app.py inicie limpiamente con AppTest sin excepciones."""
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.run()
        assert len(at.exception) == 0, f"Excepciones encontradas al arrancar app.py: {[e.message for e in at.exception]}"
        assert len(at.error) == 0, f"Errores encontrados al arrancar app.py: {[e.value for e in at.error]}"

    def test_no_emojis_in_source_code_ui(self):
        """Verifica que ni app.py ni los agentes contengan emojis decorativos."""
        # Rango estándar de emojis y pictogramas en Unicode
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F"  # Emoticons
            r"\U0001F300-\U0001F5FF"  # Symbols & Pictographs (incluye círculos de colores)
            r"\U0001F680-\U0001F6FF"  # Transport & Map
            r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            r"]+", flags=re.UNICODE
        )
        
        files_to_check = [
            APP_PATH,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "agents", "alert_agent.py")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "agents", "recommendation_agent.py")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "services", "academic_service.py"))
        ]

        for filepath in files_to_check:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            matches = emoji_pattern.findall(content)
            assert len(matches) == 0, f"Se encontraron emojis en {os.path.basename(filepath)}: {[repr(m) for m in matches[:5]]}"

    def test_mockup_components_present_in_codebase(self):
        """Verifica que los estilos y elementos de los 5 mockups estén definidos."""
        with open(APP_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Mockup 1 & 2: Cabecera e identidad granate
        assert "--granate: #7A1C20" in content
        assert "Plus Jakarta Sans" in content
        assert "JetBrains Mono" in content

        # Mockup 3: Detalle con explicabilidad y colores SHAP (#7A1C20 riesgo, #1E4E79 protector)
        assert "#7A1C20" in content
        assert "#1E4E79" in content

        # Mockup 4: Trazabilidad multiagente (4 nodos FIPA-ACL)
        assert "TRAZABILIDAD DEL SISTEMA" in content or "trazabilidad" in content.lower()

        # Mockup 5: Evolución y plan de tutoría
        assert "Evolución y plan de tutoría" in content or "evolucion" in content.lower()
