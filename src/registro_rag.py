import json
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Permite importar prueba_embeddings y rag_indexer desde src/
sys.path.append(str(Path(__file__).resolve().parent))
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from prueba_embeddings import DIRECTORIO
from rag_indexer import cargar_vectorstore, buscar_similares, formatear_contexto

load_dotenv()

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


@contextmanager
def medir(tiempos, etapa):
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def registrar_consulta(pregunta, persist_directory=DIRECTORIO, k=3):
    """Corre una consulta RAG real usando las funciones de rag_indexer.py,
    midiendo tiempo por etapa y tokens reales de la respuesta del modelo."""
    tiempos = {}
    chat_model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

    with medir(tiempos, "embed_y_busqueda"):
        vectorstore = cargar_vectorstore(persist_directory=persist_directory)
        resultados = buscar_similares(vectorstore, pregunta, k=k)

    contexto, _citas = formatear_contexto(resultados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    with medir(tiempos, "generacion"):
        respuesta = chat_model.invoke(prompt)

    uso = respuesta.usage_metadata
    tokens = (
        {
            "input_tokens": uso.get("input_tokens"),
            "output_tokens": uso.get("output_tokens"),
            "total_tokens": uso.get("total_tokens"),
        }
        if uso
        else None
    )

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {etapa: round(s * 1000, 2) for etapa, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": tokens,
    }
    return registro


if __name__ == "__main__":
    preguntas = [
        # 1. Específicas de procedimiento_despacho.md
        "Resume todos los pasos y responsables del procedimiento de despacho",
        "¿Qué validaciones o documentos se exigen antes de autorizar un despacho?",
        # 2. Específicas de plan.docx
        "¿Cuáles son los objetivos y etapas principales del plan?",
        "¿Qué riesgos, plazos o recursos clave se definen en el plan?",
        # 3. Transversal (cruza ambos manuales)
        "¿Cómo se relaciona la planificación general con la ejecución del procedimiento de despacho?",
        # 4. Control negativo (fuera de los manuales, para comprobar que no inventa)
        "¿Cuál es el protocolo de reembolso de viáticos y vacaciones?",
    ]

    for pregunta in preguntas:
        for k_prueba in (3, 6):
            registro = registrar_consulta(pregunta, k=k_prueba)
            print(json.dumps(registro, indent=2, ensure_ascii=False))

            with open("registros_latencia_costo.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")

            time.sleep(4)