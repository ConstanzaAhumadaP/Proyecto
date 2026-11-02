import consumir_gemini
import time

def evaluar_modelo(nombre_modelo, pregunta, precio_entrada, precio_salida, repeticiones=4):
    """
    Ejecuta 'repeticiones' veces la misma petición para un modelo específico.
    Calcula e imprime Latencia, Costo y Respuesta de cada intento,
    además del promedio de latencia al final.
    """
    print("=" * 70)
    print(f" EVALUANDO MODELO: {nombre_modelo}")
    print("=" * 70)
    
    latencias = []
    costos = []

    for i in range(1, repeticiones + 1):
        print(f"\n--- Intento {i} de {repeticiones} ({nombre_modelo}) ---")
        
        # 1. Armar petición (puedes pasar el modelo si tu función lo requiere)
        system_instruction = (
            "Eres un asistente especializado en producción y operación de mina a cielo abierto. "
            "Analizas extracción de mineral, lastre, movimiento total, remanejo y alimentación a chancado, "
            "medidos en Tms por turno y grupo. "
            "Identifica desviaciones respecto al plan y explica sus posibles causas operacionales. "
            "Si faltan datos, indícalo explícitamente y no inventes información. "
            "Responde de forma clara, técnica y concisa, usando siempre la unidad Tms."
        )

        

        url, body = consumir_gemini.armar_peticion(
            nombre_modelo, pregunta, system_instruction
        )

        # 2. Medir latencia
        inicio = time.perf_counter()
        datos = consumir_gemini.enviar_peticion(url, body)
        fin = time.perf_counter()
        
        latencia = fin - inicio
        latencias.append(latencia)
        
        # 3. Calcular costo
        costo = consumir_gemini.calcular_costo(datos, precio_entrada, precio_salida)
        costos.append(costo)
        
        # 4. Extraer respuesta
        respuesta = consumir_gemini.extraer_texto(datos)
        
        # 5. Imprimir resultados de la petición actual
        print(f"Latencia:  {latencia:.2f} segundos")
        print(f"Costo:     ${costo:.6f} USD")
        print(f"Respuesta: {respuesta}")

    # Resumen acumulado del modelo
    latencia_promedio = sum(latencias) / len(latencias)
    costo_total = sum(costos)
    
    print("\n" + "-" * 40)
    print(f" RESUMEN {nombre_modelo}:")
    print(f" Latencia promedio: {latencia_promedio:.2f} segundos")
    print(f" Costo acumulado ({repeticiones} peticiones): ${costo_total:.6f} USD")
    print("-" * 40 + "\n")


pregunta_prueba = (
    "El 2024-01-05, en el turno A, el grupo G4 registró una extracción total de "
    "206.237 Tms. La meta del plan para ese turno es de 200.000 Tms. "
    "Calcula la desviación porcentual respecto a la meta, indica si es positiva "
    "o negativa y explica brevemente el resultado."
)

modelos = [
    {
        "nombre": "gemini-3.6-flash",
        "precio_entrada": 0.00000075,
        "precio_salida": 0.00000375
    },
    {
         "nombre": "gemini-3.5-flash-lite",
         "precio_entrada": 0.0000003,
         "precio_salida": 0.0000025
    },
    {
         "nombre": "gemini-3.1-flash-lite",
         "precio_entrada": 0.00000025,
         "precio_salida": 0.0000015
    }
]

# Procesar los modelos consecutivamente
for config in modelos:
    evaluar_modelo(
        nombre_modelo=config["nombre"],
        pregunta=pregunta_prueba,
        precio_entrada=config["precio_entrada"],
        precio_salida=config["precio_salida"],
        repeticiones=4
    )