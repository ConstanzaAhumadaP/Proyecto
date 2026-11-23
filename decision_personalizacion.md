# Decisión fundamentada de estrategia de personalización: Sistema de análisis de producción mensual

## 1. El problema

El proyecto consiste en desarrollar un sistema que permita analizar la
producción mensual a partir de archivos Excel, obteniendo información
detallada del rendimiento de cada operador y de los diferentes grupos de
trabajo.

Actualmente, la información se encuentra distribuida en archivos
correspondientes a distintos períodos, por lo que se necesita un sistema
que permita consultar, comparar y analizar los resultados de producción,
identificar diferencias de rendimiento, detectar desviaciones y generar
reportes que faciliten la toma de decisiones.

Uno de los principales desafíos es mantener la información actualizada
cada mes, incorporando los nuevos archivos Excel sin tener que modificar
o entrenar nuevamente el modelo.

## 2. Resultado del método de decisión

Para determinar la estrategia más adecuada, se evaluaron las cinco
preguntas del método de decisión:

-   **Información que cambia seguido: True.** Los datos de producción se
    actualizan mensualmente mediante nuevos archivos Excel que contienen
    información de operadores, grupos y resultados de producción.
-   **Problemas de formato o tono: False.** No se ha identificado
    todavía evidencia de incumplimientos en al menos 3 de 20 respuestas
    del sistema.
-   **Dataset grande y de calidad: False.** No se dispone actualmente de
    un conjunto de al menos 200 ejemplos etiquetados y revisados
    específicamente para entrenar el modelo.
-   **Presupuesto limitado o necesidad de iterar rápido: False
    (provisional).** No se ha establecido todavía un límite de dos
    intentos de entrenamiento ni una necesidad demostrada de obtener
    resultados en menos de un día.
-   **Necesidad de múltiples variantes: False.** El sistema necesita
    analizar distintos operadores y grupos, pero no requiere mantener
    modelos diferentes para cada uno.

**Resultado de la evaluación:**

  Técnica                   Puntaje
  ---------------------- ----------
  RAG                      3 puntos
  Fine-tuning completo     0 puntos
  PEFT                     0 puntos

**Técnica ganadora: RAG.**

## 3. Técnica elegida y por qué

La estrategia seleccionada es RAG (Retrieval-Augmented Generation),
porque permite trabajar con información que se actualiza constantemente
sin necesidad de realizar un nuevo entrenamiento del modelo cada vez que
se incorpora un archivo mensual.

Esta técnica resulta adecuada para el proyecto porque permite consultar
información histórica y actual de producción, facilitando preguntas
sobre el rendimiento de operadores, comparaciones entre grupos,
evolución mensual y detección de variaciones en los resultados.

Además, permite incorporar nuevos documentos y mantener actualizada la
información disponible para las consultas.

Para obtener resultados confiables, la solución se complementará con
Python y Pandas para procesar los archivos Excel, realizar los cálculos
de producción y obtener indicadores de rendimiento. RAG se utilizará
como mecanismo de consulta de información, mientras que los cálculos y
comparaciones se realizarán mediante operaciones estructuradas y
verificables.

Se descarta inicialmente el fine-tuning completo y PEFT porque el
principal desafío del proyecto no es modificar el comportamiento del
modelo, sino permitirle trabajar con información de producción que
cambia mensualmente.

## 4. Qué necesitaría para ejecutarla

Para implementar esta estrategia se necesita:

-   Contar con los archivos Excel mensuales de producción.
-   Identificar y organizar los campos correspondientes a operadores,
    grupos, fechas y cantidades producidas.
-   Definir una estructura de almacenamiento que permita consultar tanto
    la información actual como el histórico mensual.
-   Implementar un proceso automatizado en Python para leer, validar y
    procesar los archivos Excel.
-   Preparar la información para que pueda ser consultada por el sistema
    mediante RAG.
-   Definir indicadores de rendimiento, productividad y comparaciones
    entre operadores y grupos.

Como primera etapa, se trabajará con los archivos mensuales disponibles,
que corresponden a **\[completar cantidad real de archivos\]**, y se
incorporarán nuevos archivos a medida que se generen los períodos de
producción.

No será necesario preparar inicialmente un dataset de 200 ejemplos
etiquetados ni realizar un entrenamiento completo del modelo, ya que la
prioridad es mantener actualizada la información y facilitar su consulta
y análisis.

**Conclusión:** RAG es la estrategia más adecuada para este proyecto
porque permite incorporar información mensual de producción, consultar
datos históricos y actuales y generar análisis de rendimiento sin tener
que reentrenar el modelo cada vez que se actualizan los archivos.
