import os
import requests
from dotenv import load_dotenv

import time

import json
import re

load_dotenv()

# Constantes
MODELO = "gemini-3.6-flash"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

# Función para crear la solicitud
def armar_peticion(modelo, pregunta, system_instruction, response_schema=None):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}"
    body = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents":
            [{"parts": [{"text": pregunta}]}]
    }
    
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }


    return url, body


# Función que envía la petición (con reintentos en errores temporales)
def enviar_peticion(url, body, reintentos=3):
    if not API_KEY:
        raise RuntimeError("No se encontró GEMINI_API_KEY. Revisa tu archivo .env")

    for intento in range(1, reintentos + 1):
        try:
            respuesta = requests.post(url, json=body, timeout=30)
        except requests.exceptions.ConnectionError:
            raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos momentos.")
        except requests.exceptions.Timeout:
            raise RuntimeError("Se agotó el tiempo. Intenta de nuevo en unos momentos.")

        if respuesta.status_code == 200:
            try:
                return respuesta.json()
            except requests.exceptions.JSONDecodeError:
                raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

        # Errores temporales: esperar y reintentar
        if respuesta.status_code in (429, 500, 503) and intento < reintentos:
            espera = 2 ** intento  # 2s, 4s
            print(f"  Status {respuesta.status_code}, reintentando en {espera}s...")
            time.sleep(espera)
            continue

        # Error definitivo: mostramos el motivo que entrega Google
        raise RuntimeError(f"Error {respuesta.status_code}: {respuesta.text}")

# Función que procesa y extrae el dato
def extraer_texto(datos):  # Gemini
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no recibe el texto generado en el lugar definido.")


def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos.get("usageMetadata", {})
    tokens_entrada = uso.get("promptTokenCount", 0)
    tokens_salida = uso.get("candidatesTokenCount", 0)
    tokens_razonamiento = uso.get("thoughtsTokenCount", 0)  # si no existe, es 0
    costo = (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo


def parsear_respuesta_json(texto, claves_requeridas=None):
    """
    claves_requeridas = ["categoria", "nivel"]
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido")

    if claves_requeridas:
        faltantes = [clave for clave in claves_requeridas if clave not in datos]
        if faltantes:
            raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos


def obtener_dato_de_prueba(pregunta, modelo=MODELO):
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "categoria": {"type": "STRING"},
            "nivel": {"type": "NUMBER"}
        },
        "required": ["categoria", "nivel"]
    }

    system_instruction = "Eres un asistente amigable y respondes en máximo 2 palabras."
    url, body = armar_peticion(modelo, pregunta, system_instruction, response_schema)

    inicio = time.perf_counter()
    datos = enviar_peticion(url, body)
    latencia = time.perf_counter() - inicio
    print(f"Latencia: {latencia:.2f} segundos")

    costo = calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo de la petición: ${costo:.6f} USD")

    texto = extraer_texto(datos)
    return parsear_respuesta_json(texto, ["categoria", "nivel"])


if __name__ == "__main__":  # Solo se ejecuta si corres este archivo directamente, no en imports
    try:
        print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación: ", error)