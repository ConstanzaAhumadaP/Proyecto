import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from cadena_tres_pasos import cargar_mina
from agente_con_herramientas import (
    INSTRUCCIONES,
    construir_herramientas,
    extraer_texto,
)

RUTA_TRAZAS = "trazas_agente.jsonl"


# ---------- Trazabilidad: qué herramientas usó el agente en cada pregunta ----------
def registrar_traza(session_id, entrada, resultado, ruta=None):
    """Agrega una línea JSON por pregunta, con las herramientas que se llamaron."""
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": resultado.get("output", ""),
    }
    with open(ruta or RUTA_TRAZAS, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")


# ---------- El agente con memoria (se arma, no se ejecuta) ----------
def construir_agente_con_memoria(modelo, df, verbose=False):
    herramientas = construir_herramientas(df)

    prompt_agente = ChatPromptTemplate.from_messages([
        ("system", INSTRUCCIONES),
        MessagesPlaceholder("chat_history"),       # <- lo que se dijo antes
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    ejecutor_agente = AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=verbose,
        max_iterations=5,
        return_intermediate_steps=True,            # necesario para la traza
    )

    # La memoria exige que la salida sea texto: normalizamos antes de guardarla
    limpiar_salida = RunnableLambda(
        lambda d: {**d, "output": extraer_texto(d["output"])}
    )
    cadena_agente = ejecutor_agente | limpiar_salida

    historiales = {}                               # una conversación por session_id

    def obtener_historial(session_id):
        if session_id not in historiales:
            historiales[session_id] = InMemoryChatMessageHistory()
        return historiales[session_id]

    return RunnableWithMessageHistory(
        cadena_agente,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )


def preguntar(agente, entrada, session_id, ruta_traza=None):
    """Invoca el agente en una sesión, registra la traza y devuelve el texto."""
    resultado = agente.invoke(
        {"entrada": entrada},
        config={"configurable": {"session_id": session_id}},
    )
    registrar_traza(session_id, entrada, resultado, ruta=ruta_traza)
    return resultado["output"]


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    df = cargar_mina("data/Enero.xlsx")
    agente = construir_agente_con_memoria(modelo, df, verbose=True)

    print("\n--- Conversación de ana ---")
    print(preguntar(agente, "¿Qué grupo y turno movió más toneladas en enero?", "ana"))
    print(preguntar(agente, "¿Y cuál quedó en segundo lugar? ¿Cuántas toneladas menos?", "ana"))

    print("\n--- Otra sesión (no recuerda nada) ---")
    print(preguntar(agente, "¿Y cuál quedó en segundo lugar?", "luis"))