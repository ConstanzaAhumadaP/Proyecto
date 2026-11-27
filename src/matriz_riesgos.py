"""Bloque 32: riesgos del codigo actual y estado explicito de los controles."""
try:  #como paquete: python3 -m src.matriz_riesgos
    from .configuracion import DOCS, guardar_json
except ImportError:  #como script: python3 src/matriz_riesgos.py
    from configuracion import DOCS, guardar_json

RIESGOS = [
    {"id": "R1", "riesgo": "Un manual recuperado o la pregunta del usuario ordena ignorar las reglas y revelar el prompt",
     "probabilidad": 3, "impacto": 3,
     "justificacion": "Los manuales se indexan desde archivos que pueden editar varias personas y el usuario escribe texto libre; obedecer una orden escondida cambiaria las reglas del asistente.",
     "mitigacion": "Roles separados, delimitador <contexto> con escape de etiquetas, deteccion de patrones en la pregunta y en los fragmentos, bloqueo antes de buscar o llamar al modelo y descarte registrado; src/prevencion_prompt_inyection.py y src/logs_rag.py.",
     "supervision": "Quien mantiene el RAG revisa cada semana los eventos inyeccion_bloqueada y documento_descartado de rag_logs.jsonl; si un manual aparece descartado, revisa su texto y lo corrige o lo retira antes de reindexar.",
     "responsable": "Responsable de seguridad del equipo",
     "evidencia": "test_pregunta_con_ataque_se_bloquea_antes_de_buscar_o_llamar_al_modelo; test_manual_envenenado_se_descarta_no_se_cita_ni_llega_al_modelo; test_un_manual_no_puede_cerrar_la_etiqueta_contexto; test_documento_envenenado_se_descarta_y_el_limpio_se_conserva.",
     "estado": "Control integrado en el RAG y probado con un modelo falso. Faltan medirlo contra Gemini real, conectar la deteccion al agente y a registro_rag.py, y asignar persona. Los patrones se esquivan reformulando el ataque y un manual legitimo podria descartarse por error."},
    {"id": "R2", "riesgo": "Una respuesta entrega una cifra equivocada o inventada y alguien decide con ella (turno, produccion, disponibilidad)",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "Un modelo de lenguaje puede redactar bien un numero equivocado y en la operacion minera una cifra mala orienta decisiones de turno. Ya ocurrio en el desarrollo: una respuesta presento 260.722 Tms de un solo turno como si fuera el total del mes (1.964.892 Tms).",
     "mitigacion": "Los calculos los hace pandas y el modelo solo redacta; las herramientas del agente son de solo lectura y envuelven esas funciones; el prompt prohibe inventar y exige declarar cuando no hay datos (plan, ley de cobre); calculadora sin eval; src/agente_con_herramientas.py y src/agente_con_memoria.py.",
     "supervision": "Revision semanal de una muestra de trazas_agente.jsonl: se compara cada cifra de respuesta_final con la observacion de la herramienta y se marcan las respuestas sin herramienta (patrones de limites_autonomia.md).",
     "responsable": "Responsable funcional de operaciones",
     "evidencia": "test_agente_llama_a_la_herramienta_y_responde_con_su_resultado; test_las_herramientas_devuelven_datos_de_pandas; test_calcular_rechaza_lo_que_no_es_aritmetica.",
     "estado": "Controles probados con modelo falso; no se midio la tasa de error con Gemini real. El prompt solo pide no inventar y la comparacion entre la cifra y la observacion es manual: no hay verificacion automatica."},
    {"id": "R3", "riesgo": "El RAG responde con fragmentos poco relevantes y muestra una fuente que no respalda la respuesta",
     "probabilidad": 4, "impacto": 3,
     "justificacion": "La busqueda por similitud siempre devuelve los fragmentos mas cercanos, aunque no tengan relacion con la pregunta. En una corrida real, la pregunta de control sobre el pan amasado recupero 2 fragmentos y la respuesta mostro fuentes; ademas aparecieron fragmentos de ejemplo como fuente.",
     "mitigacion": "Umbral de distancia coseno, sin llamada al modelo si ningun fragmento es relevante, citas numeradas con fuente y pagina, IDs estables y --reiniciar para limpiar fragmentos de ejemplo, y un script de calibracion del umbral; src/logs_rag.py, src/rag_indexer.py y src/calibrar_umbral.py.",
     "supervision": "Antes de cambiar manuales o umbral se corre calibrar_umbral.py y se revisan sus preguntas con y sin respuesta; cada semana se revisan en el log las consultas cuyo retriever_end trajo fragmentos pero la respuesta dijo no tener informacion.",
     "responsable": "Responsable del RAG del equipo",
     "evidencia": "test_sin_fragmentos_relevantes_no_se_llama_al_modelo; test_buscar_similares_y_umbral; test_calibrar_encuentra_un_umbral_entre_preguntas_validas_e_invalidas; test_formatear_contexto_acepta_documents_y_tuplas_y_cita_la_pagina.",
     "estado": "El umbral 0.45 es provisorio y se observo demasiado permisivo: falta recalibrarlo con los manuales reales. No se valida que las citas [n] de la respuesta existan en el contexto ni que el contenido citado respalde la afirmacion; evaluador_rag.py mide la recuperacion con pocos casos."},
    {"id": "R4", "riesgo": "Se cambia el prompt de sistema sin revisar el efecto del cambio en sus restricciones",
     "probabilidad": 2, "impacto": 3,
     "justificacion": "El prompt define reglas como no inventar y no revelar instrucciones; borrar una linea las quita y nadie lo notaria leyendo las respuestas.",
     "mitigacion": "Registro con huella verificada de cada version, diff por lineas, pausa con interrupt hasta que una persona apruebe, aprobacion de la huella exacta revisada, activacion local atomica, version activa leida por el RAG y huella del prompt en cada evento llm_start del log; src/registro_prompts.py, src/grafo_supervision.py y src/logs_rag.py.",
     "supervision": "El responsable funcional revisa el diff y ejecuta las pruebas antes de aprobar; rechaza si el cambio quita restricciones. Un registro cuyo texto no coincide con su huella se rechaza al cargarlo.",
     "responsable": "Responsable funcional del equipo",
     "evidencia": "test_pausa_aprobacion_y_rechazo; test_huella_incorrecta_no_se_aprueba; test_activacion_persistida; test_el_log_registra_la_huella_del_prompt_de_sistema_para_auditar_la_version.",
     "estado": "Aprobacion de huella exacta y activacion local probadas. Pendientes: el prompt del agente y el de la cadena de tres pasos no pasan por el registro, InMemorySaver pierde las aprobaciones pendientes si se cierra el programa, no hay permisos por rol, y editar PROMPT_SYSTEM en el codigo sin registrarlo solo genera un aviso."},
    {"id": "R5", "riesgo": "Preguntas o datos de produccion quedan en claro en trazas y registros, o salen a un servicio externo",
     "probabilidad": 2, "impacto": 4,
     "justificacion": "Las preguntas pueden incluir nombres u otra informacion sensible; los manuales y las tablas de produccion se envian a la API de Gemini para calcular embeddings y respuestas, y los archivos de traza se pueden subir a git por error.",
     "mitigacion": "El log del RAG guarda huellas y largos en lugar de la pregunta, los fragmentos o la respuesta; los manuales de prueba son ficticios; src/logs_rag.py.",
     "supervision": "El custodio de datos revisa que trazas_agente.jsonl, registros_latencia_costo.jsonl, rag_logs.jsonl, error.log, chroma_db/ y local/ esten en .gitignore, y confirma con la empresa si los manuales o datos reales pueden usar un proveedor externo antes de cargarlos.",
     "responsable": "Custodio de datos del equipo",
     "evidencia": "test_el_log_no_guarda_la_pregunta_ni_la_respuesta_en_crudo; test_la_traza_registra_herramienta_argumentos_y_observacion.",
     "estado": "Solo el log del RAG esta minimizado. trazas_agente.jsonl y registros_latencia_costo.jsonl guardan la pregunta en texto, y la traza del agente tambien las observaciones de las herramientas. Pendiente minimizarlos, verificar el .gitignore y decidir el uso de un proveedor externo con datos reales."},
    {"id": "R6", "riesgo": "El asistente usa datos desactualizados o con otra estructura: un manual cambiado o borrado sin reindexar, o un Excel de otro mes con columnas distintas",
     "probabilidad": 3, "impacto": 3,
     "justificacion": "El indice solo cambia cuando se vuelve a correr el indexador, y cargar_mina depende de una cabecera de tres niveles y de nombres de columna fijos; un cambio silencioso produce respuestas con informacion antigua.",
     "mitigacion": "Indexador con IDs estables, huella por archivo, reemplazo de los fragmentos de un manual que cambio, deteccion de indexaciones incompletas y simulacion previa con --simular; cargar_mina elimina la fila Total y convierte los tipos; src/rag_indexer.py.",
     "supervision": "El responsable documental corre rag_indexer.py despues de cada cambio de manuales y revisa las lineas indexado y sin cambios; con cada Excel nuevo revisa la forma de la tabla antes de usarlo.",
     "responsable": "Responsable documental",
     "evidencia": "test_si_el_manual_cambia_se_reemplaza_lo_anterior; test_segunda_corrida_no_gasta_embeddings; test_indexacion_incompleta_se_detecta_y_se_rehace; test_indexar_carpeta_ignora_formatos_no_soportados.",
     "estado": "Reindexacion local probada. Pendientes: el indexador no elimina los fragmentos de un manual que se borra de data/manuales, no hay calendario de actualizacion y no hay pruebas ni validacion de columnas con un Excel distinto a Enero.xlsx."},
]


def puntaje_riesgo(probabilidad, impacto):
    if any(type(n) is not int or not 1 <= n <= 5 for n in (probabilidad, impacto)):
        raise ValueError("P e I deben ser enteros entre 1 y 5")
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [(probabilidad + 1, impacto), (probabilidad - 1, impacto),
               (probabilidad, impacto + 1), (probabilidad, impacto - 1)]
    return any(categoria_riesgo(p * i) != actual for p, i in vecinos if 1 <= p <= 5 and 1 <= i <= 5)


def completar_matriz():
    filas = []
    for riesgo in RIESGOS:
        fila = dict(riesgo)
        fila["puntaje"] = puntaje_riesgo(fila["probabilidad"], fila["impacto"])
        fila["categoria"] = categoria_riesgo(fila["puntaje"])
        fila["al_limite"] = esta_en_el_limite(fila["probabilidad"], fila["impacto"])
        filas.append(fila)
    return sorted(filas, key=lambda r: -r["puntaje"])


def main():
    filas = completar_matriz()
    guardar_json(DOCS / "matriz_riesgos.json", filas)
    lineas = ["# Matriz de riesgos del asistente de operaciones mina", "",
              "Estimaciones didacticas previas a los controles, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25. Los cortes son la convencion del programa.", "",
              "AL LIMITE indica que variar un punto en P o I cambia la categoria. Cada responsable es un rol que el equipo debe asignar a una persona. Los controles pendientes no se presentan como implementados.", "",
              "| ID | Riesgo | P | I | Puntaje | Categoria | AL LIMITE |",
              "|---|---|---:|---:|---:|---|---|"]
    for r in filas:
        lineas.append(f"| {r['id']} | {r['riesgo']} | {r['probabilidad']} | {r['impacto']} | {r['puntaje']} | {r['categoria']} | {'Si' if r['al_limite'] else 'No'} |")
    for r in filas:
        lineas.extend(["", f"## {r['id']} {r['riesgo']}", ""])
        for campo in ("justificacion", "mitigacion", "supervision", "responsable", "evidencia", "estado"):
            lineas.append(f"**{campo.capitalize()}**: {r[campo]}\n")
    (DOCS / "matriz_riesgos.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    for r in filas:
        print(r["id"], r["categoria"], r["puntaje"], "AL LIMITE" if r["al_limite"] else "")


if __name__ == "__main__":
    main()