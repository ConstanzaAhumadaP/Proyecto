from unittest.mock import MagicMock

import pandas as pd
from langchain_core.messages import AIMessage

from cadena_tres_pasos import construir_cadena, produccion_mensual_por_grupo

COL = "ESPERANZA|Movimiento Mina|Total"


def df_falso():
    """Mini tabla inventada: no depende del Excel ni de la API."""
    return pd.DataFrame({
        "fecha": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
        "grupo": ["G1", "G2", "G1"],
        "turno": ["B", "A", "B"],
        COL: [100.0, 50.0, 200.0],
    })


def modelo_falso_con(*respuestas):
    modelo = MagicMock()
    modelo.side_effect = [AIMessage(content=r) for r in respuestas]
    return modelo


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = modelo_falso_con(
        "G1 turno B movió más.",          # 1. analizar
        "G1 turno B movió 300 Tms.",      # 2. revisar
        "- G1 turno B: 300 Tms",          # 3. formato
    )
    cadena = construir_cadena(modelo_falso, df_falso())
    resultado = cadena.invoke({"pregunta": "¿Quién movió más?"})

    assert modelo_falso.call_count == 3
    assert "G1" in resultado
    assert resultado.startswith("-")      # salió en viñetas


def test_pandas_entrega_la_tabla_correcta():
    tabla = produccion_mensual_por_grupo(df_falso())
    primera = tabla.iloc[0]
    assert (primera["grupo"], primera["turno"]) == ("G1", "B")
    assert primera["movimiento_total_tms"] == 300.0     # 100 + 200


def test_paso_1_recibe_la_tabla_de_pandas():
    modelo_falso = modelo_falso_con("a", "b", "c")
    construir_cadena(modelo_falso, df_falso()).invoke({"pregunta": "?"})

    prompt_analisis = modelo_falso.call_args_list[0].args[0].to_string()
    assert "300" in prompt_analisis       # G1-B sumado
    assert "G1" in prompt_analisis and "G2" in prompt_analisis


def test_paso_2_recibe_respuesta_del_paso_1_y_la_tabla():
    modelo_falso = modelo_falso_con("RESPUESTA_DEL_PASO_1", "b", "c")
    construir_cadena(modelo_falso, df_falso()).invoke({"pregunta": "?"})

    prompt_revision = modelo_falso.call_args_list[1].args[0].to_string()
    assert "RESPUESTA_DEL_PASO_1" in prompt_revision    # la salida viaja
    assert "300" in prompt_revision                     # y la tabla también


def test_paso_3_recibe_solo_el_texto_revisado():
    modelo_falso = modelo_falso_con("a", "TEXTO_REVISADO", "c")
    construir_cadena(modelo_falso, df_falso()).invoke({"pregunta": "?"})

    prompt_formato = modelo_falso.call_args_list[2].args[0].to_string()
    assert "TEXTO_REVISADO" in prompt_formato