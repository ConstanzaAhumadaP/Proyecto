import logging
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    construir_paso_clasificacion,
    construir_enrutador,
    procesar_pregunta_seguro,
    MENSAJE_SIN_DATOS,
)

COL = "ESPERANZA|Movimiento Mina|Total"


def df_falso():
    return pd.DataFrame({
        "fecha": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
        "grupo": ["G1", "G2", "G1"],
        "turno": ["B", "A", "B"],
        COL: [100.0, 50.0, 200.0],
        "FLOTA CAMIONES|CAT 793 C|Hrs Disp": [10.0, 10.0, 10.0],
        "FLOTA CAMIONES|CAT 793 C|Hrs Nominal": [20.0, 20.0, 20.0],
    })


def modelo_falso_con(*respuestas):
    """Cada elemento es un texto (respuesta) o una excepción (fallo)."""
    m = MagicMock()
    m.side_effect = [
        r if isinstance(r, Exception) else AIMessage(content=r)
        for r in respuestas
    ]
    return m


def prompt_n(modelo, n):
    return modelo.call_args_list[n].args[0].to_string()


# ======== 1. Paso de clasificación (aislado) ========
def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Mensual \n")
    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"pregunta": "¿quién movió más?"}
    )
    assert resultado == "mensual"


@pytest.mark.parametrize("salida_del_modelo, esperado", [
    ("Turno.", "turno"),
    ("DISPONIBILIDAD\n", "disponibilidad"),
    ("otra", "otra"),
    ("no sé", "otra"),            # respuesta inesperada -> ruta segura
    ("", "otra"),                 # respuesta vacía -> ruta segura
])
def test_clasificacion_siempre_devuelve_una_categoria_valida(salida_del_modelo, esperado):
    modelo_falso = MagicMock(return_value=AIMessage(content=salida_del_modelo))
    resultado = construir_paso_clasificacion(modelo_falso).invoke({"pregunta": "?"})
    assert resultado == esperado


def test_clasificacion_le_pasa_la_pregunta_al_modelo():
    modelo_falso = MagicMock(return_value=AIMessage(content="otra"))
    construir_paso_clasificacion(modelo_falso).invoke({"pregunta": "PREGUNTA_X"})
    assert "PREGUNTA_X" in prompt_n(modelo_falso, 0)


# ======== 2. Fallback (aislado) ========
def test_cadena_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise ConnectionError("Error de red simulado")

    respaldo = RunnableLambda(lambda x: f"respaldo por: {x['error']}")
    cadena_segura = RunnableLambda(fallar_a_proposito).with_fallbacks(
        [respaldo], exception_key="error"
    )
    resultado = cadena_segura.invoke({"pregunta": "algo"})
    assert resultado == "respaldo por: Error de red simulado"   # el fallback recibe el error


# ======== 3. La clasificación decide la ruta ========
@pytest.mark.parametrize("categoria, debe_tener, no_debe_tener", [
    ("mensual", "movimiento_total_tms", "disponibilidad_pct"),
    ("turno", "movimiento_tms", "movimiento_total_tms"),
    ("disponibilidad", "disponibilidad_pct", "movimiento_tms"),
])
def test_la_categoria_elige_la_tabla_correcta(categoria, debe_tener, no_debe_tener):
    m = modelo_falso_con(categoria, "respuesta")
    resultado = construir_enrutador(m, df_falso()).invoke({"pregunta": "?"})

    assert resultado == "respuesta"
    assert m.call_count == 2                       # clasificar + analizar
    prompt_analisis = prompt_n(m, 1)
    assert debe_tener in prompt_analisis
    assert no_debe_tener not in prompt_analisis


def test_la_pregunta_original_llega_al_analisis():
    m = modelo_falso_con("mensual", "ok")
    construir_enrutador(m, df_falso()).invoke({"pregunta": "PREGUNTA_ORIGINAL"})
    assert "PREGUNTA_ORIGINAL" in prompt_n(m, 1)   # no se pierde entre pasos


def test_ruta_otra_responde_sin_llamar_al_analisis():
    m = modelo_falso_con("otra")
    resultado = construir_enrutador(m, df_falso()).invoke({"pregunta": "¿plan?"})
    assert resultado == MENSAJE_SIN_DATOS
    assert m.call_count == 1                       # solo clasificó


# ======== 4. Falla un paso: responde, no lanza excepción ========
def test_falla_la_clasificacion_y_el_flujo_responde():
    m = modelo_falso_con(ConnectionError("API caída"))
    resultado = construir_enrutador(m, df_falso()).invoke(
        {"pregunta": "¿Cómo está la disponibilidad de camiones?"}
    )
    assert "CAT 793 C" in resultado                # respaldo con datos reales


def test_falla_el_analisis_y_el_flujo_responde():
    m = modelo_falso_con("mensual", ConnectionError("API caída"))
    resultado = construir_enrutador(m, df_falso()).invoke(
        {"pregunta": "¿Qué grupo movió más en el mes?"}
    )
    assert "no pude generar el análisis" in resultado
    assert "300" in resultado                      # G1-B: 100 + 200


def test_el_error_original_queda_registrado(caplog):
    m = modelo_falso_con(ConnectionError("API caída"))
    with caplog.at_level(logging.WARNING):
        construir_enrutador(m, df_falso()).invoke({"pregunta": "grupo"})
    assert "API caída" in caplog.text


# ======== 5. Dos capas: falla el modelo Y falla el respaldo ========
def test_si_tambien_falla_el_respaldo_la_funcion_de_entrada_responde(caplog):
    df_roto = pd.DataFrame({"x": [1]})             # le faltan las columnas
    m = modelo_falso_con(ConnectionError("API caída"))
    cadena = construir_enrutador(m, df_roto)

    with caplog.at_level(logging.ERROR):
        resultado = procesar_pregunta_seguro(cadena, "¿Qué grupo movió más?")

    assert "No pudimos procesar" in resultado      # respuesta segura, no excepción
    assert "Error procesando pregunta" in caplog.text


def test_flujo_normal_pasa_por_la_funcion_de_entrada():
    m = modelo_falso_con("mensual", "G1 turno B")
    cadena = construir_enrutador(m, df_falso())
    assert procesar_pregunta_seguro(cadena, "¿quién?") == "G1 turno B"