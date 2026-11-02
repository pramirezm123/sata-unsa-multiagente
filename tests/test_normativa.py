"""
Pruebas de cumplimiento de la Normativa Académica Oficial de la UNSA (EPIS).
Verifica:
1. El examen sustitutorio reemplaza ÚNICAMENTE el examen parcial más bajo (min(EP1, EP2, EP3)).
2. Las evaluaciones continuas (EC1, EC2, EC3) están blindadas y NUNCA se reemplazan.
3. Regla de redondeo de notas: 10.5 aprueba (se redondea a 11), mientras que 10.49 reprueba (10).
4. Casos borde: empates en parciales, nota requerida > 20 (inviable), nota < 0 (ya aprobado).
5. Cálculo del promedio ponderado final con distintas configuraciones de ponderación de sílabo.
"""
from src.services.academic_service import calcular_simulacion_sustitutorio


class TestNormativaUNSA:
    """Reglas normativas del reglamento de evaluación UNSA."""

    def test_sustitutorio_replaces_only_lowest_partial(self):
        """Verifica que se reemplace min(EP1, EP2, EP3), nunca las continuas."""
        # EC1=15 (15%), EP1=05 (15%), EC2=15 (20%), EP2=12 (20%), EC3=15 (15%), EP3=10 (15%)
        # Promedio ordinario: 15*0.15 + 5*0.15 + 15*0.20 + 12*0.20 + 15*0.15 + 10*0.15 = 2.25 + 0.75 + 3.0 + 2.4 + 2.25 + 1.5 = 12.15 (Aprobado)
        # Probemos con un caso desaprobado:
        # EC1=10 (15%), EP1=04 (15%), EC2=10 (20%), EP2=09 (20%), EC3=10 (15%), EP3=06 (15%)
        # El menor parcial es EP1=04.
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        res = calcular_simulacion_sustitutorio(
            ec1=10.0, ep1=4.0,
            ec2=10.0, ep2=9.0,
            ec3=10.0, ep3=6.0,
            pesos=pesos
        )
        assert res["aplica"] is True
        assert res["parcial_a_reemplazar"] == "EP1"
        assert res["nota_reemplazada"] == 4.0

    def test_sustitutorio_never_replaces_continuous_evaluation_even_if_lower(self):
        """Aun si una continua es 0.0 y un examen parcial es 08.0, solo se reemplaza el parcial."""
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        res = calcular_simulacion_sustitutorio(
            ec1=0.0, ep1=8.0,  # EC1 es 0 pero es continua, no se reemplaza
            ec2=10.0, ep2=9.0,
            ec3=10.0, ep3=10.0,
            pesos=pesos
        )
        assert res["aplica"] is True
        assert res["parcial_a_reemplazar"] == "EP1"
        assert res["nota_reemplazada"] == 8.0

    def test_rounding_threshold_10_5_is_approved(self):
        """Un promedio ordinario de 10.5 ya está aprobado y no requiere sustitutorio."""
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        # Notas idénticas de 10.5 en todo dan promedio exacto de 10.5
        res = calcular_simulacion_sustitutorio(
            ec1=10.5, ep1=10.5,
            ec2=10.5, ep2=10.5,
            ec3=10.5, ep3=10.5,
            pesos=pesos
        )
        assert res["aplica"] is False
        assert res["ya_aprobo"] is True
        assert res["promedio_ordinario"] == 10.5

    def test_rounding_threshold_10_49_is_failed(self):
        """Un promedio ordinario de 10.49 está desaprobado y amerita sustitutorio."""
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        # Promedio 10.49
        res = calcular_simulacion_sustitutorio(
            ec1=10.49, ep1=10.49,
            ec2=10.49, ep2=10.49,
            ec3=10.49, ep3=10.49,
            pesos=pesos
        )
        assert res["aplica"] is True
        assert res["ya_aprobo"] is False
        assert res["promedio_ordinario"] == 10.49

    def test_tie_breaking_favors_higher_weight_partial(self):
        """Si hay empate en la nota más baja, se reemplaza la que tenga mayor ponderación para beneficiar al estudiante."""
        # EP1 (15%) = 06, EP2 (20%) = 06. Reemplazar EP2 de 20% otorga mayor recuperación.
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        res = calcular_simulacion_sustitutorio(
            ec1=10.0, ep1=6.0,
            ec2=10.0, ep2=6.0,
            ec3=10.0, ep3=12.0,
            pesos=pesos
        )
        assert res["aplica"] is True
        assert res["parcial_a_reemplazar"] == "EP2", "En empate, debe favorecer el parcial de mayor peso (20% vs 15%)."

    def test_mathematically_impossible_sustitutorio_detected(self):
        """Si la nota necesaria en sustitutorio excede 20, es matemáticamente inalcanzable."""
        # Estudiante con notas en 0 o 1
        pesos = {"EC1": 15, "EP1": 15, "EC2": 20, "EP2": 20, "EC3": 15, "EP3": 15}
        res = calcular_simulacion_sustitutorio(
            ec1=2.0, ep1=2.0,
            ec2=2.0, ep2=2.0,
            ec3=2.0, ep3=2.0,
            pesos=pesos
        )
        assert res["aplica"] is True
        assert res["es_viable"] is False
        assert res["nota_minima_requerida"] is None
        assert "Matemáticamente inalcanzable" in res["mensaje"]

    def test_different_syllabus_weight_distribution(self):
        """Syllabus con ponderaciones no estándar (ej. 10-20-10-20-10-30)."""
        custom_weights = {"EC1": 10, "EP1": 20, "EC2": 10, "EP2": 20, "EC3": 10, "EP3": 30}
        res = calcular_simulacion_sustitutorio(
            ec1=12.0, ep1=6.0,
            ec2=12.0, ep2=7.0,
            ec3=12.0, ep3=5.0,
            pesos=custom_weights
        )
        assert res["aplica"] is True
        assert res["parcial_a_reemplazar"] == "EP3"
        assert res["peso_parcial"] == 30
