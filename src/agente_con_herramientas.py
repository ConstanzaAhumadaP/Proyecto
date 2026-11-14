import ast
import operator

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from cadena_tres_pasos import (
    cargar_mina,
    produccion_por_turno,
    produccion_mensual_por_grupo,
    disponibilidad_camiones,
)

INSTRUCCIONES = (
    "Eres un asistente de operaciones mina. Responde usando SOLO los datos que "
    "entregan las herramientas. No tienes datos de plan minero, ley de cobre ni "
    "manuales: si te los piden, dilo claramente en vez de inventar. "
    "Responde en español, breve y con las cifras exactas de la herramienta."
)


# ---------- Calculadora segura (solo aritmética, sin eval) ----------
_OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _evaluar(nodo):
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.left), _evaluar(nodo.right))
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    raise ValueError("solo se permite aritmética simple (+ - * /)")


@tool
def calcular(expresion: str) -> str:
    """
    Evalúa una expresión aritmética simple, como '1964892.61 - 1691495.60'.
    Usar cuando la pregunta requiere restar, sumar, multiplicar o dividir cifras.
    """
    try:
        return str(_evaluar(ast.parse(expresion, mode="eval").body))
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        return f"No pude evaluar la expresión: {e}"


# ---------- Esquema de argumentos (lo que el modelo lee campo por campo) ----------
class ArgumentosMejoresTurnos(BaseModel):
    """Argumentos de la herramienta mejores_turnos."""
    cantidad: int = Field(
        default=5,
        description="Cuántos turnos devolver, de 1 a 20. Por defecto 5.",
    )


# ---------- Herramientas de datos (envuelven tus funciones de pandas) ----------
def construir_herramientas(df):
    """Las herramientas se arman con el df para poder inyectar uno falso en tests."""

    @tool
    def produccion_mensual() -> str:
        """
        Total de toneladas movidas en el periodo, por grupo y turno, ordenado de
        mayor a menor. Usar para: quién movió más en el mes, comparar grupos o turnos.
        """
        return produccion_mensual_por_grupo(df).to_string(index=False)

    @tool(args_schema=ArgumentosMejoresTurnos)
    def mejores_turnos(cantidad: int = 5) -> str:
        """
        Los turnos individuales (día + grupo + turno) con más toneladas movidas.
        Usar para: mejor turno, turno récord, días de mayor movimiento.
        """
        cantidad = max(1, min(int(cantidad), 20))
        return produccion_por_turno(df, top=cantidad).to_string(index=False)

    @tool
    def disponibilidad_flota() -> str:
        """
        Disponibilidad física (%) de cada modelo de camión en el periodo, de menor
        a mayor. Usar para preguntas sobre disponibilidad o estado de la flota.
        """
        return disponibilidad_camiones(df).round(1).to_string(index=False)

    return [produccion_mensual, mejores_turnos, disponibilidad_flota, calcular]


def extraer_texto(salida):
    """Gemini puede devolver el texto como lista de bloques; lo dejamos como str."""
    if isinstance(salida, str):
        return salida
    if isinstance(salida, list):
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in salida
        )
    return str(salida)


# ---------- El agente (se arma, no se ejecuta) ----------
def construir_agente(modelo, df, verbose=False):
    herramientas = construir_herramientas(df)

    prompt_agente = ChatPromptTemplate.from_messages([
        ("system", INSTRUCCIONES),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),   # pasos razonar-actuar-observar
    ])

    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=verbose,
        max_iterations=5,       # corta si el agente se queda dando vueltas
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    df = cargar_mina("data/Enero.xlsx")
    ejecutor = construir_agente(modelo, df, verbose=True)

    for pregunta in [
        "¿Qué grupo y turno movió más toneladas en enero?",
        "¿Cuántas toneladas más movió G1 turno B que G3 turno A?",
        "¿Cuánto nos desviamos del plan minero?",
    ]:
        print(f"\n> {pregunta}")
        resultado = ejecutor.invoke({"entrada": pregunta})
        print("Respuesta final:", extraer_texto(resultado["output"]))