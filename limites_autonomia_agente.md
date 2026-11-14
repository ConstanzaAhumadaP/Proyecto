# Límites de autonomía: Asistente de operaciones mina (agente con herramientas y memoria)

## Herramientas y nivel de riesgo

- produccion_mensual: bajo (solo lectura; calcula con pandas sobre el Excel ya cargado, no modifica datos ni llama a sistemas externos. Peor caso: una cifra mal interpretada)
- mejores_turnos: bajo (solo lectura; su único argumento, `cantidad`, está acotado de 1 a 20 en el código)
- disponibilidad_flota: bajo (solo lectura, sin argumentos; el riesgo es de interpretación, porque calcula Hrs Disp / Hrs Nominal y el área podría definir la disponibilidad distinto)
- calcular: bajo (cómputo puro sin efectos externos; usa `ast` y solo acepta + - * /, sin `eval`)

Solo lectura no significa sin riesgo: el riesgo real es que se tome una decisión con una cifra equivocada, por eso pesa más la revisión de trazas que la aprobación previa.

## Herramientas que requieren aprobación humana

- Ninguna de las herramientas actuales requiere aprobación humana, porque todas son de solo lectura y no hay nada que deshacer.
- produccion_mensual: no requiere aprobación (solo lee datos).
- mejores_turnos: no requiere aprobación (solo lee, y el código limita lo que el modelo puede pedir).
- disponibilidad_flota: no requiere aprobación (solo lee; el riesgo de interpretación se controla con la revisión de trazas).
- calcular: no requiere aprobación (no tiene efectos externos ni acceso a datos).
- Regla para herramientas futuras: solo lectura, sin aprobación; escritura reversible, aprobación según el caso; escritura irreversible con impacto económico, aprobación humana siempre, con timeout igual a denegado y registro de la decisión.

## Revisión de trazas

- Frecuencia: 100 % de las interacciones durante las primeras dos semanas y después de cualquier cambio de prompt, herramientas o modelo; luego, semanal sobre una muestra de 20 interacciones, más todas las que activen los patrones de abajo; e inmediata cuando alguien reporte una cifra que no cuadra.

- Qué se busca (en `trazas_agente.jsonl`, desde la raíz del proyecto):
  - Pregunta de datos respondida sin llamar a ninguna herramienta, porque el modelo pudo inventar cifras: `grep '"acciones": \[\]' trazas_agente.jsonl`
  - Preguntas sobre plan o ley de cobre, que no existen en los datos y deben responderse diciéndolo: `grep -i -E 'plan|ley' trazas_agente.jsonl`
  - La misma herramienta 3 o más veces en una pregunta, posible bucle: `grep -E '"herramienta": "([a-z_]+)".*"herramienta": "\1".*"herramienta": "\1"' trazas_agente.jsonl`
  - Límite de iteraciones alcanzado: `grep -i 'stopped due to' trazas_agente.jsonl`
  - `cantidad` fuera de rango (0, negativa o mayor a 20): `grep -E '"cantidad": (-|0[,}]|2[1-9]|[3-9][0-9]|[0-9]{3,})' trazas_agente.jsonl`
  - Calculadora que rechazó una expresión, por error del modelo o intento de colar código: `grep 'No pude evaluar' trazas_agente.jsonl`
  - Cifras en `respuesta_final` que no aparecen en `observacion` (revisión manual en la muestra semanal)

## Qué hacer ante un comportamiento inesperado

- 1. Contener: si falla una herramienta, desactivarla quitándola de la lista que devuelve `construir_herramientas` (por ejemplo, `return [produccion_mensual, mejores_turnos, calcular]`). Si el problema es general, atender con `src/enrutamiento_mina.py`, donde el modelo solo clasifica y las respuestas salen de rutas fijas.
- 2. Ubicar la interacción en `trazas_agente.jsonl` por `session_id` y `timestamp`: qué herramienta eligió, con qué argumentos y qué devolvió.
- 3. Diagnosticar y ajustar: herramienta equivocada, corregir las descripciones (docstrings); argumentos extraños, corregir la `description` del campo en `ArgumentosMejoresTurnos`; cifras sin respaldo, reforzar `INSTRUCCIONES`; bucle, revisar descripciones que se solapan (no subir `max_iterations` para taparlo); cifra incorrecta de una herramienta, corregir la función de pandas.
- 4. Reproducir el caso con una prueba en `src/test_agentes.py` usando el modelo falso, y confirmar que falla antes del arreglo.
- 5. Verificar: correr `pytest -v` y repetir la pregunta con Gemini real.
- 6. Reactivar la herramienta o el agente y revisar el 100 % de las trazas durante los días siguientes.
- 7. Registrar qué ocurrió, la causa y el cambio, para que el patrón entre en la revisión periódica.






