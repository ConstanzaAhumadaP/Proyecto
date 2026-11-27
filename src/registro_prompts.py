import difflib
import hashlib
import json
from datetime import datetime, timezone

try:  #como paquete: python3 -m src.registro_prompts
    from .configuracion import DOCS, LOCAL, guardar_json
    from .prevencion_prompt_inyection import PROMPT_SYSTEM
except ImportError:  #como script: python3 src/registro_prompts.py
    from configuracion import DOCS, LOCAL, guardar_json
    from prevencion_prompt_inyection import PROMPT_SYSTEM

NOMBRE = "asistente_mina"
AUTOR = "equipo de operaciones mina"
MODELO = "gemini-3.5-flash-lite"

#Primera version del prompt del RAG, la que tenia logs_rag.py antes de agregar la defensa contra inyeccion
PROMPT_V1 = """Eres un asistente de operaciones mina. Responde usando SOLO el contexto de los manuales.
Cita la fuente de cada afirmación con su número entre corchetes, como [1].
Si el contexto no alcanza para responder, dilo explícitamente en vez de inventar."""
#Segunda version: la que hoy define prevencion_prompt_inyection.py
PROMPT_V2 = PROMPT_SYSTEM
ARCHIVO_REGISTRO = DOCS / "registro_prompts.json"
ARCHIVO_ACTIVO = LOCAL / "prompt_activo.json"


def huella_prompt(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


class RegistroDePrompts:
    def __init__(self):
        self.versiones = []

    def registrar(self, nombre, texto, autor, nota, modelo=MODELO):
        version = {"nombre": nombre, "huella": huella_prompt(texto), "texto": texto,
                   "autor": autor, "fecha": datetime.now(timezone.utc).isoformat(),
                   "nota": nota, "modelo": modelo,
                   "parametros": {"temperature": "fija del modelo: el parametro se ignora"}}
        self.versiones.append(version)
        return version

    def ultima(self, nombre):
        return next((v for v in reversed(self.versiones) if v["nombre"] == nombre), None)


def crear_registro():
    registro = RegistroDePrompts()
    registro.registrar(NOMBRE, PROMPT_V1, AUTOR, "Base: solo contexto de los manuales, citas y abstencion")
    registro.registrar(NOMBRE, PROMPT_V2, AUTOR, "Defensa ante instrucciones dentro de los manuales (prevencion_prompt_inyection.py)")
    return registro


def cargar_registro():
    if not ARCHIVO_REGISTRO.exists():
        return crear_registro()
    registro = RegistroDePrompts()
    registro.versiones = json.loads(ARCHIVO_REGISTRO.read_text(encoding="utf-8"))
    if not registro.versiones or any(v["huella"] != huella_prompt(v["texto"]) for v in registro.versiones):
        raise ValueError("El registro de prompts no coincide con sus huellas")
    return registro


def agregar_version(texto, autor=AUTOR, nota=""):
    """Registra un prompt nuevo. Queda PENDIENTE de aprobacion: no pasa a ser el activo."""
    registro = cargar_registro()
    ultima = registro.ultima(NOMBRE)
    if ultima and ultima["huella"] == huella_prompt(texto):
        return ultima
    version = registro.registrar(NOMBRE, texto, autor, nota)
    guardar_json(ARCHIVO_REGISTRO, registro.versiones)
    return version


def obtener_activa(ruta=None):
    registro = cargar_registro()
    archivo = ruta or ARCHIVO_ACTIVO
    huella = (json.loads(archivo.read_text(encoding="utf-8"))["huella"]
              if archivo.exists() else registro.versiones[0]["huella"])
    version = next((v for v in registro.versiones if v["huella"] == huella), None)
    if version is None:
        raise ValueError("La version activa no existe en el registro")
    return version


def diff_prompts(anterior, nueva):
    return "\n".join(difflib.unified_diff(anterior.splitlines(), nueva.splitlines(),
                                        fromfile="prompt_anterior", tofile="prompt_nuevo", lineterm=""))


def main():
    registro = cargar_registro()
    guardar_json(ARCHIVO_REGISTRO, registro.versiones)
    if len(registro.versiones) >= 2:
        v1, v2 = registro.versiones[-2:]
        diferencia = diff_prompts(v1["texto"], v2["texto"])
        (DOCS / "diff_prompts.txt").write_text(diferencia, encoding="utf-8")
        print(diferencia)
    print("Ultima registrada:", registro.ultima(NOMBRE)["huella"])
    print("Activa:", obtener_activa()["huella"])
    if huella_prompt(PROMPT_SYSTEM) != registro.ultima(NOMBRE)["huella"]:
        print("AVISO: el prompt del codigo cambio y no esta registrado. Usa agregar_version(...)")


if __name__ == "__main__":
    main()