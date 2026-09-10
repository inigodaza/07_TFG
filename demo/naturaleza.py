"""
Qué capa actúa en cada pantalla: IA, reglas o persona.

De dónde sale
--------------
Del customer journey de Fabián del 9/09/2026, cuya regla de diseño técnico es:

    «La IA interpreta lo ambiguo. El componente determinista garantiza permisos,
     estados, trazabilidad y ejecución. La persona autorizada conserva la
     decisión final.»

Y su corolario, que es lo que de verdad hay que defender delante de un cliente:
**no se trata de poner IA en todo**. La propuesta gana credibilidad cuando usa IA
para comprender ambigüedad y conserva mecanismos deterministas donde están en
juego la autoridad, la trazabilidad y la ejecución.

Por qué esto vive en un fichero y no en la interfaz
----------------------------------------------------
Porque es una **afirmación sobre el sistema**, no una decoración. Decir «esta
pantalla la resuelve la IA» cuando en realidad la resuelve una expresión regular
sería exactamente la clase de cosa que este bloque existe para detectar. Estando
aquí se puede comprobar desde `pruebas.py` que lo que la pantalla dice de sí
misma coincide con lo que hace el código.

Una nota incómoda, y a propósito
---------------------------------
Hoy casi todo el sistema es determinista. El modo asistido con IA existe
—`nucleo/llm.py`— pero está **vetado sobre los documentos de Juan**, que son
datos reales de cliente de GraphyCems. Así que las etiquetas de abajo distinguen
tres cosas que es tentador confundir:

    ACTÚA        la capa interviene hoy, en esta demo, con estos datos
    DISPONIBLE   está implementada y se activa con una clave, pero aquí no corre
    PREVISTA     es donde iría, y todavía no está

Marcar como «IA» algo que hoy resuelve una regla haría la demo más vendible y la
conversación con Fabián más pobre: él está intentando decidir dónde poner IA, y
para eso necesita saber dónde NO hace falta.
"""

IA = "IA"
DETERMINISTA = "Determinista"
HUMANA = "Humana"

ACTUA = "actúa"
DISPONIBLE = "disponible"
PREVISTA = "prevista"

# Las nueve pantallas del guion de Fabián, con la capa que las resuelve.
#
# `capas` es una lista de (capa, estado, qué hace). El orden importa: primero la
# que manda en esa pantalla.
PANTALLAS = {
    "vigilancia": {
        "n": 0, "titulo": "El sistema trabaja en segundo plano",
        "capas": [
            (DETERMINISTA, ACTUA,
             "El flujo es programado: agrupa por pedido, compara valores "
             "exactos y decide si hay incidencia."),
            (IA, DISPONIBLE,
             "El modo asistido puede leer documentos que la regla no sabe "
             "interpretar. Vetado sobre los documentos de Juan por ser datos "
             "reales de cliente."),
        ]},
    "sesion": {
        "n": 1, "titulo": "Entrada y contexto del usuario",
        "capas": [
            (DETERMINISTA, ACTUA,
             "Identidad, rol y permisos salen de la ontología de Pablo. No se "
             "infieren: se leen."),
        ]},
    "procesamiento": {
        "n": 2, "titulo": "Entrada y procesamiento",
        "capas": [
            (DETERMINISTA, ACTUA,
             "Clasifica por señales del contenido, extrae campos y controla "
             "estados y trazabilidad."),
            (IA, DISPONIBLE,
             "Extrae de documentos con formato desconocido cuando la regla se "
             "abstiene."),
        ]},
    "alerta": {
        "n": 3, "titulo": "Alerta",
        "capas": [
            (DETERMINISTA, ACTUA,
             "La comparación de valores exactos es una regla, y tiene que "
             "serlo: de aquí sale una acusación sobre el trabajo de alguien."),
            (IA, PREVISTA,
             "Ayudaría cuando los datos o el contexto son ambiguos — dos "
             "documentos que dicen lo mismo con otras palabras."),
        ]},
    "panel": {
        "n": 4, "titulo": "Dashboard de la incidencia",
        "capas": [
            (DETERMINISTA, ACTUA,
             "Consolida estados y encamina la incidencia a la herramienta que "
             "le corresponde, según una tabla que se puede discutir."),
        ]},
    "evidencia": {
        "n": 5, "titulo": "Evidencia y diagnóstico",
        "capas": [
            (DETERMINISTA, ACTUA,
             "El fragmento citado se localiza en el texto del documento y se "
             "comprueba que está: la evidencia no se parafrasea."),
            (IA, PREVISTA,
             "Ésta es la pantalla donde más aportaría: explicar por qué dos "
             "afirmaciones se contradicen, y distinguir un error de un cambio "
             "documentado."),
        ]},
    "autoridad": {
        "n": 6, "titulo": "Autoridad y permisos",
        "capas": [
            (DETERMINISTA, ACTUA,
             "Autoridad, permisos y escalado salen de reglas explícitas sobre "
             "la ontología. Aquí la IA no pinta nada, y meterla sería un "
             "problema de seguridad, no una mejora."),
        ]},
    "decision": {
        "n": 7, "titulo": "Decisión y captura del criterio",
        "capas": [
            (HUMANA, ACTUA,
             "Decide una persona con autoridad, y justifica. El sistema no "
             "decide por nadie."),
            (DETERMINISTA, ACTUA,
             "Comprueba el permiso, registra y ejecuta."),
            (IA, PREVISTA,
             "Asistencia: redactar la justificación o proponer la corrección, "
             "siempre para que una persona la acepte o la cambie."),
        ]},
    "memoria": {
        "n": 8, "titulo": "Cierre, memoria y aprendizaje",
        "capas": [
            (DETERMINISTA, ACTUA,
             "El registro, el versionado y la recuperación del precedente son "
             "deterministas: se busca por la forma del caso, no por parecido."),
            (HUMANA, ACTUA,
             "La recomendación no se aplica sola. La decisión final sigue "
             "siendo de la persona autorizada."),
            (IA, PREVISTA,
             "Recuperar casos equivalentes que no comparten la forma exacta "
             "pero sí el problema."),
        ]},
}

# Qué significa cada estado, para poder explicarlo en pantalla sin repetirse.
GLOSA_ESTADO = {
    ACTUA: "interviene en esta demo, con estos datos",
    DISPONIBLE: "implementado y activable con una clave; aquí no corre",
    PREVISTA: "es donde iría; todavía no está",
}

GLOSA_CAPA = {
    IA: "comprende documentos, relaciona significados y propone",
    DETERMINISTA: "ejecuta reglas, compara valores exactos, aplica permisos y "
                  "registra estados",
    HUMANA: "valida decisiones, justifica excepciones y asume responsabilidad",
}


def de(clave):
    """La ficha de una pantalla, o `None` si no está declarada."""
    return PANTALLAS.get(clave)


def capas_de(clave, solo_activas=False):
    ficha = PANTALLAS.get(clave) or {}
    capas = ficha.get("capas", [])
    return [c for c in capas if c[1] == ACTUA] if solo_activas else capas


def resumen():
    """
    Cuántas pantallas resuelve cada capa hoy. Es el dato que contesta la
    pregunta de Fabián —dónde hace falta IA— con números en vez de con opinión.
    """
    cuenta = {IA: 0, DETERMINISTA: 0, HUMANA: 0}
    for ficha in PANTALLAS.values():
        for capa, estado, _ in ficha["capas"]:
            if estado == ACTUA:
                cuenta[capa] += 1
    return {
        "pantallas": len(PANTALLAS),
        "por_capa": cuenta,
        "ia_prevista": sum(1 for f in PANTALLAS.values()
                           for c, e, _ in f["capas"]
                           if c == IA and e == PREVISTA),
        "ia_disponible": sum(1 for f in PANTALLAS.values()
                             for c, e, _ in f["capas"]
                             if c == IA and e == DISPONIBLE),
    }
