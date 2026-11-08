import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


# ---------- Datos ----------
def cargar_mina(ruta):
    raw = pd.read_excel(ruta, header=None)

    # Aplanar cabecera de 3 niveles
    h = raw.iloc[0:3].replace("", pd.NA)
    h.iloc[0] = h.iloc[0].ffill()   # sección (ESPERANZA, FLOTA CAMIONES...)
    h.iloc[1] = h.iloc[1].ffill()   # equipo / bloque
    nombres = ["|".join(str(x).strip() for x in h.iloc[:, c] if pd.notna(x))
               for c in range(raw.shape[1])]
    nombres[0:3] = ["fecha", "grupo", "turno"]

    df = raw.iloc[5:].copy()
    df.columns = nombres
    df = df[df["fecha"].astype(str) != "Total"]          # fuera fila Total
    df["fecha"] = pd.to_datetime(df["fecha"])
    cols_num = df.columns.difference(["fecha", "grupo", "turno"])
    df[cols_num] = df[cols_num].apply(pd.to_numeric, errors="coerce")
    return df.reset_index(drop=True)


# ---------- Cálculos con pandas ----------
def produccion_por_turno(df, top=5):
    """Los turnos individuales con más movimiento."""
    col = "ESPERANZA|Movimiento Mina|Total"
    return (df[["fecha", "grupo", "turno", col]]
            .rename(columns={col: "movimiento_tms"})
            .sort_values("movimiento_tms", ascending=False)
            .head(top))


def produccion_mensual_por_grupo(df):
    """Total del periodo por grupo y turno."""
    col = "ESPERANZA|Movimiento Mina|Total"
    return (df.groupby(["grupo", "turno"])[col]
              .sum()
              .reset_index()
              .rename(columns={col: "movimiento_total_tms"})
              .sort_values("movimiento_total_tms", ascending=False))


def disponibilidad_camiones(df):
    """Disponibilidad física = Hrs Disp / Hrs Nominal, por modelo de camión."""
    filas = []
    for col in df.columns:
        if col.startswith("FLOTA CAMIONES|") and col.endswith("|Hrs Disp"):
            modelo = col.split("|")[1]
            nominal = df[col.replace("Hrs Disp", "Hrs Nominal")].sum()
            filas.append({"camion": modelo,
                          "disponibilidad_pct": round(df[col].sum() / nominal * 100, 1)})
    return pd.DataFrame(filas).sort_values("disponibilidad_pct")


# ---------- Plantillas: una responsabilidad cada una ----------
# 1) ANALIZAR: responder la pregunta usando solo la tabla
plantilla_analisis = PromptTemplate.from_template(
    "Eres un analista de operaciones mina. Responde la pregunta usando "
    "SOLO los datos de la tabla. No inventes números ni hagas cálculos nuevos. "
    "Si la tabla no permite responder, dilo.\n\n"
    "Pregunta: {pregunta}\n\nDatos:\n{tabla}"
)

# 2) REVISAR: comprobar la respuesta contra la tabla
plantilla_revision = PromptTemplate.from_template(
    "Revisa esta respuesta contra la tabla. Corrige cualquier cifra, grupo "
    "o turno que no coincida con la tabla, y no llames 'total' a la cifra "
    "de un solo turno. Devuelve solo la respuesta final corregida.\n\n"
    "Pregunta: {pregunta}\n\nTabla:\n{tabla}\n\nRespuesta a revisar:\n{analisis}"
)

# 3) FORMATEAR: dejarla en viñetas cortas
plantilla_formato = PromptTemplate.from_template(
    "Convierte este texto en una lista de viñetas markdown de máximo 3 líneas, "
    "sin introducción y conservando las cifras exactas:\n\n{texto}"
)


# ---------- La cadena (se arma, no se ejecuta) ----------
def construir_cadena(modelo, df):
    def paso_calculo(entrada):                      # PASO 0: pandas
        tabla = produccion_mensual_por_grupo(df)
        return {
            "pregunta": entrada["pregunta"],
            "tabla": tabla.to_string(index=False),
        }

    paso_analisis = plantilla_analisis | modelo | StrOutputParser()

    return (
        RunnableLambda(paso_calculo)
        | RunnablePassthrough.assign(analisis=paso_analisis)   # 1. analizar
        | plantilla_revision | modelo | StrOutputParser()      # 2. revisar
        | (lambda r: {"texto": r})
        | plantilla_formato | modelo | StrOutputParser()       # 3. formato
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    df = cargar_mina("data/Enero.xlsx")
    cadena = construir_cadena(modelo, df)

    respuesta = cadena.invoke(
        {"pregunta": "¿Qué grupo y turno movió más toneladas en enero?"}
    )
    print(respuesta)