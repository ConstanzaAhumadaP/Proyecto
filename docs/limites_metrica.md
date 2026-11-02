# Límites de la métrica de evaluación

## Qué mide

La métrica de evaluación (F1-score basado en solapamiento de tokens) compara gramaticalmente el texto generado por el LLM contra el texto de referencia, contando únicamente la cantidad de palabras en común que comparten ambas oraciones sin interpretar el significado o la precisión de los datos.

## Modos de falla conocidos

* **Falso Positivo por Solapamiento Gramatical (F1 Alto con Error Factual):** Ocurre cuando la estructura sintáctica de la oración coincide casi perfectamente con la referencia, pero la cifra numérica o el dato clave es completamente erróneo. La métrica asigna un puntaje sobresaliente porque la mayoría de los tokens de relleno coinciden.
  * *Ejemplo concreto (Caso ID 14):* Para la consulta sobre la extracción de mineral el 2024-01-13 en el turno B, el modelo respondió *"El 2024-01-13 en el turno B se extrajeron 653 Tms de mineral."* frente a la referencia oficial de *16.000 Tms*. A pesar del error grave en la cifra extraída, la métrica asignó un **F1: 0.917**.

* **Falso Negativo por Variación Sintáctica (F1 Bajo con Respuesta Correcta):** Ocurre cuando el modelo entrega la información numérica y el grupo exacto desde la base de datos, pero utiliza sinónimos o una redacción distinta a la plantilla de referencia.
  * *Ejemplo concreto (Caso ID 5):* Para la consulta de mayor extracción el 2024-01-05, el modelo respondió *"El grupo G4 y turno A logró una extracción total de 206.237 Tms."* mientras que la referencia decía *"El grupo G4 en el turno A tuvo la mayor extracción total, con 206.237 Tms."*. La respuesta fue 100% correcta y verídica, pero la métrica la penalizó reduciéndola a un **F1: 0.643**.

## Muestra revisada

Se auditaron manualmente **10 casos** sobre el total de 20 consultas del dataset. La selección se realizó mediante un muestreo por extremos (*stratified edge sampling*): los **5 casos con menor F1** y los **5 casos con mayor F1** registrados en `resultados_metricas.json`, garantizando el análisis de falsos positivos y falsos negativos de la métrica.

## Recomendación de uso

Solo se debe confiar en el puntaje de la métrica automática para evaluar la fluidez o similitud gramatical en texto libre. Cuando el sistema evalúe tareas de extracción de datos tabulares (Excel/SQL) o precisión numérica crítica, la métrica basada en tokens **nunca debe ser el único criterio de validación**, siendo indispensable incorporar auditorías *Human-in-the-Loop* (HITL) o validadores deterministas de entidades numéricas.