import json
from collections import Counter
from pathlib import Path

# Importaciones relativas dentro del paquete src/
from cargar_datos import cargar_excel, fila_a_texto
from cliente import consultar_modelo
from pipeline_limpieza import procesar_texto

# Carga de datos operativos de la mina
df_datos = cargar_excel("data/Enero.xlsx")


def obtener_contexto(fecha: str, turno: str) -> str:
    """Busca los datos de una fecha y turno en el Excel y devuelve la frase completa."""
    sub_df = df_datos[
        (df_datos["fecha"] == fecha) & (df_datos["turno"] == turno)
    ]
    return fila_a_texto(sub_df.iloc[0]) if not sub_df.empty else ""


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())


def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(tokens_referencia, tokens_respuesta)

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    return {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }


def calcular_metricas(texto_referencia, texto_respuesta):
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)

    return calcular_precision_cobertura_f1(tokens_referencia, tokens_respuesta)


# Lista de casos de prueba con extracción dinámica de contexto desde Enero.xlsx
casos = [
    {
        "consulta": "¿Cuánto mineral se extrajo el 2024-01-01 en el turno A?",
        "contexto": obtener_contexto("2024-01-01", "A"),
        "referencia": "El 2024-01-01 en el turno A se extrajeron 15.200 Tms de mineral.",
    },
    {
        "consulta": "¿Cuánto lastre se movió el 2024-01-02 en el turno B?",
        "contexto": obtener_contexto("2024-01-02", "B"),
        "referencia": "El 2024-01-02 en el turno B se movieron 88.500 Tms de lastre.",
    },
    {
        "consulta": "¿Cuánto mineral se extrajo el 2024-01-03 en el turno B?",
        "contexto": obtener_contexto("2024-01-03", "B"),
        "referencia": "El 2024-01-03 en el turno B se extrajeron 14.707 Tms de mineral.",
    },
    {
        "consulta": "¿Cuál fue el movimiento total de mina el 2024-01-04 en el turno A?",
        "contexto": obtener_contexto("2024-01-04", "A"),
        "referencia": "El movimiento total de mina fue de 245.100 Tms.",
    },
    {
        "consulta": "¿Qué grupo y turno tuvo la mayor extracción total el 2024-01-05?",
        "contexto": obtener_contexto("2024-01-05", "A"),
        "referencia": "El grupo G4 en el turno A tuvo la mayor extracción total, con 206.237 Tms.",
    },
    {
        "consulta": "¿Cuál fue el movimiento total de mina del grupo G2 en el turno B el 2024-01-05?",
        "contexto": obtener_contexto("2024-01-05", "B"),
        "referencia": "El movimiento total de mina fue de 260.723 Tms.",
    },
    {
        "consulta": "¿Cuánto material alimentó el chancado el 2024-01-06 en el turno B?",
        "contexto": obtener_contexto("2024-01-06", "B"),
        "referencia": "La alimentación a chancado fue de 60.866 Tms.",
    },
    {
        "consulta": "¿Cuánto material alimentó el chancado el 2024-01-07 en el turno A?",
        "contexto": obtener_contexto("2024-01-07", "A"),
        "referencia": "La alimentación a chancado fue de 58.900 Tms.",
    },
    {
        "consulta": "¿Cuánto lastre se extrajo el 2024-01-08 en el turno B?",
        "contexto": obtener_contexto("2024-01-08", "B"),
        "referencia": "El 2024-01-08 en el turno B se extrajeron 92.080 Tms de lastre.",
    },
    {
        "consulta": "¿Cuánto mineral se extrajo el 2024-01-09 en el turno B?",
        "contexto": obtener_contexto("2024-01-09", "B"),
        "referencia": "El 2024-01-09 en el turno B se extrajeron 13.800 Tms de mineral.",
    },
    {
        "consulta": "¿Cuánto lastre se extrajo el 2024-01-10 en el turno A?",
        "contexto": obtener_contexto("2024-01-10", "A"),
        "referencia": "El 2024-01-10 en el turno A se extrajeron 95.400 Tms de lastre.",
    },
    {
        "consulta": "¿Cuál fue el movimiento total de mina el 2024-01-11 en el turno B?",
        "contexto": obtener_contexto("2024-01-11", "B"),
        "referencia": "El movimiento total de mina fue de 252.000 Tms.",
    },
    {
        "consulta": "¿Cuánto material alimentó el chancado el 2024-01-12 en el turno A?",
        "contexto": obtener_contexto("2024-01-12", "A"),
        "referencia": "La alimentación a chancado fue de 62.100 Tms.",
    },
    {
        "consulta": "¿Cuánto mineral se extrajo el 2024-01-13 en el turno B?",
        "contexto": obtener_contexto("2024-01-13", "B"),
        "referencia": "El 2024-01-13 en el turno B se extrajeron 16.000 Tms de mineral.",
    },
    {
        "consulta": "¿Cuánto lastre se extrajo el 2024-01-14 en el turno A?",
        "contexto": obtener_contexto("2024-01-14", "A"),
        "referencia": "El 2024-01-14 en el turno A se extrajeron 90.300 Tms de lastre.",
    },
    {
        "consulta": "¿Cuál fue el movimiento total de mina el 2024-01-15 en el turno B?",
        "contexto": obtener_contexto("2024-01-15", "B"),
        "referencia": "El movimiento total de mina fue de 268.400 Tms.",
    },
    {
        "consulta": "¿Cuánto material alimentó el chancado el 2024-01-16 en el turno A?",
        "contexto": obtener_contexto("2024-01-16", "A"),
        "referencia": "La alimentación a chancado fue de 61.500 Tms.",
    },
    {
        "consulta": "¿Cuánto mineral se extrajo el 2024-01-17 en el turno B?",
        "contexto": obtener_contexto("2024-01-17", "B"),
        "referencia": "El 2024-01-17 en el turno B se extrajeron 14.100 Tms de mineral.",
    },
    {
        "consulta": "¿Cuánto lastre se extrajo el 2024-01-18 en el turno A?",
        "contexto": obtener_contexto("2024-01-18", "A"),
        "referencia": "El 2024-01-18 en el turno A se extrajeron 87.900 Tms de lastre.",
    },
    {
        "consulta": "¿Cuál fue el movimiento total de mina el 2024-01-19 en el turno B?",
        "contexto": obtener_contexto("2024-01-19", "B"),
        "referencia": "El movimiento total de mina fue de 255.800 Tms.",
    },
]

# Definición estándar de la ruta del JSON de resultados en la raíz del proyecto
raiz = Path(__file__).resolve().parents[1]
ruta_resultados = raiz / "resultados_metricas.json"

# Recupera las respuestas guardadas previamente para no duplicar consultas consumidas
if ruta_resultados.exists():
    with ruta_resultados.open("r", encoding="utf-8") as archivo:
        resultados = json.load(archivo)
else:
    resultados = []

completados = {(caso["consulta"], caso["referencia"]) for caso in resultados}

# Bucle principal alineado al flujo del profesor
for numero, caso in enumerate(casos, start=1):
    consulta = caso["consulta"]
    contexto = caso["contexto"]
    referencia = caso["referencia"]

    if (consulta, referencia) in completados:
        print("Ya guardada:", consulta)
        continue

    prompt_con_contexto = (
        f"Contexto de producción:\n{contexto}\n\nPregunta: {consulta}"
    )

    try:
        respuesta = consultar_modelo(
            prompt_con_contexto,
            system_instruction=(
                "Responde en español en una sola oración breve (máximo 15 palabras). "
                "Usa números en formato con punto de miles (ejemplo: 60.866 o 14.707) "
                "y utiliza la unidad 'Tms'. No escribas números en palabras."
            ),
        )
    except RuntimeError as error:
        print("\nSe detuvo la generación:", error)
        print(f"Respuestas guardadas: {len(resultados)}")
        break

    metricas = calcular_metricas(referencia, respuesta)

    resultados.append(
        {
            "id": numero,
            "consulta": consulta,
            "referencia": referencia,
            "respuesta": respuesta,
            **metricas,
        }
    )

    # Persistencia incremental en el archivo JSON
    with ruta_resultados.open("w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, indent=2, ensure_ascii=False)

    completados.add((consulta, referencia))

    print("\nConsulta:", consulta)
    print("Respuesta:", respuesta)
    print("Métricas:", metricas)
    print(f"Guardadas: {len(resultados)}/{len(casos)}")


def resumir_metricas(resultados):
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }
    n = len(resultados)
    return {
        "precision_promedio": sum(r["precision"] for r in resultados) / n,
        "cobertura_promedio": sum(r["cobertura"] for r in resultados) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


print("\nPromedios General:")
print(resumir_metricas(resultados))

print("\nPeores casos:")
peores_casos = sorted(resultados, key=lambda r: r["f1"])
for caso in peores_casos[:3]:
    print(caso["consulta"], f"F1: {caso['f1']:.4f}")
    
    
# referencia = procesar_texto(
#     "Python es un lenguaje de programación interpretado."
# )

# texto_respuesta = consultar_modelo("¿Qué es Python?",
#                                    system_instruction="Responde en español con una definición breve, en una sola oración de máximo 15 palabras. Sin listas, ejemplos ni introducciones.")

# respuesta = procesar_texto(texto_respuesta)
# resultado = calcular_precision_cobertura_f1(referencia, respuesta)

# print("Respuesta:", texto_respuesta)
# print("Tokens de referencia:", len(referencia))
# print("Tokens de respuesta:", len(respuesta))
# print(resultado)