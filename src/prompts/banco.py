BANCO_DE_PROMPT = [
    {
        "nombre": "desviacion_produccion",
        "system_instruction": (
            "Eres un asistente especializado en análisis de operaciones mineras. "
            "Calcula la desviación porcentual como (real - meta) / meta * 100. "
            "Si el valor real es menor que la meta, la desviación es NEGATIVA y debes usar signo negativo. "
            "El campo es_negativa debe ser true solo si la desviación es negativa. "
            "Explica brevemente el resultado. "
            "Si faltan datos, indícalo y no inventes información."
        ),
        "ejemplo_usuario": (
            "Una planta procesa 1.000 toneladas por hora. "
            "La meta es de 1.200 toneladas por hora."
        ),
        "claves_esperadas": ["desviacion_porcentual", "es_negativa", "explicacion"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "desviacion_porcentual": {"type": "NUMBER"},
                "es_negativa": {"type": "BOOLEAN"},
                "explicacion": {"type": "STRING"},
            },
            "required": ["desviacion_porcentual", "es_negativa", "explicacion"],
        },
    },
    {
        "nombre": "clasificar_incidente",
        "system_instruction": (
            "Clasificas incidentes operacionales de una faena minera por tipo y severidad."
        ),
        "ejemplo_usuario": "El chancador primario se detuvo 40 minutos por falla eléctrica.",
        "claves_esperadas": ["categoria", "severidad"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria": {
                    "type": "STRING",
                    "enum": ["falla_electrica", "falla_mecanica", "falla_operacional", "otro"],
                },
                "severidad": {"type": "NUMBER"},
            },
            "required": ["categoria", "severidad"],
        },
    },
    {
        "nombre": "extraer_datos_reporte",
        "system_instruction": (
            "Extraes datos de reportes de turno en una faena minera. "
            "Si un dato no aparece en el texto, usa null y no inventes información."
        ),
        "ejemplo_usuario": (
            "Turno B: el molino SAG operó 10 horas con 3 detenciones. "
            "Se procesaron 11.500 toneladas."
        ),
        "claves_esperadas": ["equipo", "horas_operacion", "detenciones", "toneladas"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "equipo": {"type": "STRING"},
                "horas_operacion": {"type": "NUMBER"},
                "detenciones": {"type": "NUMBER"},
                "toneladas": {"type": "NUMBER"},
            },
            "required": ["equipo", "horas_operacion", "detenciones", "toneladas"],
        },
    },
]