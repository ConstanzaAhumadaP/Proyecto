import logging
import re
import unicodedata
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch, RunnablePassthrough, RunnableLambda
)

from cadena_tres_pasos import (
    cargar_mina,
    produccion_por_turno,
    produccion_mensual_por_grupo,
    disponibilidad_camiones,
    plantilla_analisis,
)

logger = logging.getLogger(__name__)

CATEGORIAS = ("mensual", "turno", "disponibilidad")   # todo lo demás -> "otra"

MENSAJE_SIN_DATOS = (
    "No tengo datos cargados para responder eso (por ejemplo plan minero, "
    "ley de cobre o manuales). Puedo responder sobre producción por grupo "
    "y turno, mejores turnos individuales y disponibilidad de camiones."
)

# ---------- Clasificación ----------
plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica la pregunta de operaciones mina en UNA categoría. "
    "Responde solo con esa palabra.\n"
    "- mensual: total del periodo por grupo y turno (quién movió más en el mes)\n"
    "- turno: los mejores turnos individuales o un día en particular\n"
    "- disponibilidad: disponibilidad o estado de la flota de camiones\n"
    "- otra: cualquier otra cosa (plan minero, ley de cobre, manuales, etc.)\n\n"
    "Pregunta: {pregunta}"
)


def normalizar(texto):
    """Si el modelo responde algo inesperado, cae en 'otra' (nunca inventa ruta)."""
    texto = texto.strip().lower()
    for categoria in CATEGORIAS:
        if categoria in texto:
            return categoria
    return "otra"


def construir_paso_clasificacion(modelo):
    """Paso 1 del enrutador: pregunta -> 'mensual' | 'turno' | 'disponibilidad' | 'otra'."""
    return plantilla_clasificacion | modelo | StrOutputParser() | normalizar


# ---------- Clasificación SIN LLM (para el fallback) ----------
PALABRAS_CLAVE = (                      # el orden decide en caso de empate
    ("disponibilidad", ("disponib", "camion", "flota")),
    ("mensual", ("mensual", "enero", "total", "grupo", "periodo", "mes")),
    ("turno", ("turno", "dia", "mejores", "top")),
)

FUNCIONES = {
    "mensual": produccion_mensual_por_grupo,
    "turno": produccion_por_turno,
    "disponibilidad": disponibilidad_camiones,
}


def clasificar_por_palabras(pregunta):
    """Clasifica con palabras clave: funciona aunque el LLM esté caído."""
    sin_tildes = unicodedata.normalize("NFD", pregunta.lower())
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    palabras = re.findall(r"\w+", sin_tildes)
    for categoria, raices in PALABRAS_CLAVE:
        if any(p.startswith(r) for p in palabras for r in raices):
            return categoria
    return "otra"


# ---------- El enrutador (se arma, no se ejecuta) ----------
def construir_enrutador(modelo, df):
    paso_clasificacion = construir_paso_clasificacion(modelo)

    def cadena_con_datos(calcular):
        """pandas calcula -> LLM analiza (misma estructura para cada ruta)."""
        def preparar(x):
            return {
                "pregunta": x["pregunta"],
                "tabla": calcular(df).to_string(index=False),
            }
        return RunnableLambda(preparar) | plantilla_analisis | modelo | StrOutputParser()

    bifurcacion = RunnableBranch(
        (lambda x: x["clasificacion"] == "mensual",
         cadena_con_datos(produccion_mensual_por_grupo)),
        (lambda x: x["clasificacion"] == "turno",
         cadena_con_datos(produccion_por_turno)),
        (lambda x: x["clasificacion"] == "disponibilidad",
         cadena_con_datos(disponibilidad_camiones)),
        RunnableLambda(lambda x: MENSAJE_SIN_DATOS),     # else: sin LLM
    )

    def respaldo_con_datos(x):
        """Si Gemini falla, pandas igual puede responder: entrega la tabla."""
        logger.warning("Cadena principal falló. Activando respaldo con datos, Error: %s",
                       x.get("error"))
        categoria = clasificar_por_palabras(x["pregunta"])
        if categoria == "otra":
            return MENSAJE_SIN_DATOS
        tabla = FUNCIONES[categoria](df).to_string(index=False)
        return ("En este momento no pude generar el análisis con IA, "
                "pero estos son los datos calculados directamente:\n\n" + tabla)

    enrutamiento = RunnablePassthrough.assign(clasificacion=paso_clasificacion) | bifurcacion
    return enrutamiento.with_fallbacks(
        [RunnableLambda(respaldo_con_datos)], exception_key="error"
    )


def procesar_pregunta_seguro(cadena, pregunta):
    try:
        return cadena.invoke({"pregunta": pregunta})
    except Exception as error:
        logger.error("Error procesando pregunta: %s", error)
        return ("No pudimos procesar tu consulta en este momento. "
                "Intenta de nuevo más tarde o consulta al equipo de planificación.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="error.log", filemode="a", encoding="utf-8", force=True,
    )
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    df = cargar_mina("data/Enero.xlsx")
    enrutador = construir_enrutador(modelo, df)

    for pregunta in [
        "¿Qué grupo y turno movió más toneladas en enero?",
        "¿Cuáles fueron los 5 turnos con más movimiento?",
        "¿Cómo estuvo la disponibilidad de los camiones?",
        "¿Cuánto nos desviamos del plan minero?",
    ]:
        print(f"\n> {pregunta}")
        print(procesar_pregunta_seguro(enrutador, pregunta))