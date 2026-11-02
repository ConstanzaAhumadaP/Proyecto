import pandas as pd

# Definición de las 12 columnas principales del reporte Excel
COLUMNAS = [
    "fecha",
    "grupo",
    "turno",
    "mineral_tms",
    "marginal_tms",
    "lastre_tms",
    "extraccion_total_tms",
    "remanejo_tms",
    "movimiento_total_tms",
    "chancado_tms",
    "fase10_tms",
    "fase4_tms",
]

COLUMNAS_NUMERICAS = COLUMNAS[3:]


def _a_numero(serie):
    """Convierte a número float/int de forma segura, limpiando texto con puntos o comas."""
    if serie.dtype == object:
        serie = (
            serie.astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
    return pd.to_numeric(serie, errors="coerce").fillna(0)


def cargar_excel(ruta, filas_encabezado=4):
    """Lee el xlsx de producción y devuelve un DataFrame limpio."""
    df = pd.read_excel(
        ruta,
        skiprows=filas_encabezado,  # Salta las 4 filas de títulos combinados
        header=None,
        names=COLUMNAS,
        usecols=range(len(COLUMNAS)),  # Carga solo las primeras 12 columnas
    )

    # Convertir fecha y filtrar filas que no sean fechas válidas (p. ej. la fila 'Total')
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

    # Limpiar y convertir columnas numéricas
    for col in COLUMNAS_NUMERICAS:
        df[col] = _a_numero(df[col])

    return df


def miles(n):
    """Formatea números enteros utilizando el punto como separador de miles."""
    return f"{int(round(n)):,}".replace(",", ".")


def fila_a_texto(f):
    """Construye el texto resumen de cada fila."""
    return (
        f"Fecha {f['fecha']}, grupo {f['grupo']}, turno {f['turno']}: "
        f"mineral {miles(f['mineral_tms'])} Tms, "
        f"lastre {miles(f['lastre_tms'])} Tms, "
        f"extracción total {miles(f['extraccion_total_tms'])} Tms, "
        f"remanejo {miles(f['remanejo_tms'])} Tms, "
        f"movimiento total {miles(f['movimiento_total_tms'])} Tms, "
        f"alimentación a chancado {miles(f['chancado_tms'])} Tms, "
        f"fase 10 {miles(f['fase10_tms'])} Tms, "
        f"fase 4 {miles(f['fase4_tms'])} Tms."
    )


def cargar_fragmentos(ruta):
    df = cargar_excel(ruta)
    return [fila_a_texto(f) for _, f in df.iterrows()]


if __name__ == "__main__":
    fragmentos = cargar_fragmentos("data/Enero.xlsx")
    print("Filas cargadas:", len(fragmentos))
    if fragmentos:
        print("Primera fila:\n", fragmentos[0])
        print("Última fila:\n", fragmentos[-1])