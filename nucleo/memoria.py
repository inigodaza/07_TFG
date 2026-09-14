"""
Lo que el sistema recuerda de las decisiones ya tomadas.

Qué es «aprender», aquí
------------------------
No hay ningún modelo que se entrene. Lo que hay es **precedente**: cada vez que
alguien resuelve una incidencia, se guarda qué clase de incidencia era, qué se
decidió, quién lo decidió y cuándo. Cuando aparece otra de la misma clase, el
sistema la reconoce y ofrece lo que se hizo la vez anterior.

Esa distinción no es una modestia: es la diferencia entre algo que se puede
auditar y algo que no. Un precedente se puede abrir, leer y discutir —«esto lo
decidiste tú el martes, y así»— y una predicción de un modelo, no. En un sistema
cuyo argumento entero es que ninguna discrepancia se convierte en verdad sin
evidencia, meter una caja negra en el último paso sería contradecirse.

Qué se guarda y qué no
-----------------------
Se guarda la **clase** de la incidencia (qué campo, en qué dirección discrepaba)
y la decisión. No se guarda el documento ni su contenido: la memoria es un
registro de decisiones, no un archivo de documentación de cliente.

Dónde se guarda
----------------
En un JSON al lado de los datos de la demo. En un despliegue de verdad esto
sería la base de datos de la empresa o la propia ontología —que es donde Fabián
lo sitúa— y el fichero se sustituiría por una tabla sin tocar nada de lo demás:
todo lo que sabe el resto del sistema sobre la memoria son las cuatro funciones
de abajo.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

RUTA = Path(__file__).resolve().parent.parent / "demo" / "datos" / "memoria.json"

# Cuántos precedentes hacen falta para que el sistema se atreva a sugerir.
#
# Uno basta para **enseñar** el precedente («esto ya pasó»), pero no para
# proponer aplicarlo sin más: una sola vez es una anécdota. A partir de dos, la
# sugerencia se ofrece como atajo — y aun así hay que pulsarla, porque quien
# responde de la decisión sigue siendo la persona.
MINIMO_PARA_SUGERIR = 2


def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clase_de(discrepancia):
    """
    La «forma» de una incidencia, que es lo que permite reconocerla otra vez.

    Dos incidencias son de la misma clase si discrepa el mismo campo y en la
    misma dirección: la orden dice más que el cliente, o menos. Los valores
    concretos no entran —3.000 contra 30.000 y 800 contra 8.000 son el mismo
    problema— porque si entraran, no se repetiría ninguna nunca.
    """
    campo = discrepancia.get("campo")
    try:
        a = float(str(discrepancia.get("valor_cliente")).replace(".", "").replace(",", "."))
        b = float(str(discrepancia.get("valor_orden")).replace(".", "").replace(",", "."))
        sentido = "orden_mayor" if b > a else "orden_menor"
    except (TypeError, ValueError):
        sentido = "distinto"
    return f"{campo}:{sentido}"


def cargar(ruta=None):
    ruta = Path(ruta or RUTA)
    if not ruta.is_file():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return datos if isinstance(datos, list) else []


def registrar(discrepancia, decision, quien, pedido, propuesta_por=None,
              justificacion=None, evidencias=None, contexto=None,
              autorizados=None, diagnostico=None, es_criterio=False,
              valor_decidido=None, fase="cerrada", ruta=None):
    """
    Anota una decisión resuelta. Devuelve lo guardado.

    `decision` es la acción del operario: «aceptar» el valor del cliente,
    «dar_por_buena» la orden, «corregir» poniendo otro valor, o «escalar».

    `fase` distingue una PROPUESTA de un CIERRE
    -------------------------------------------
    Las dos son acciones y las dos dejan rastro. Antes sólo se anotaba el
    cierre, y eso dejaba fuera del registro justo lo que más cuesta reconstruir
    a los seis meses: que alguien miró la incidencia, dijo qué haría y por qué,
    y no pudo cerrarla. Una propuesta que no se anota es trabajo que no consta.

    Una propuesta nunca es criterio: no ha cerrado nada. Por eso no entra en
    `precedentes()` aunque se marcara.

    `es_criterio` separa dos cosas que antes iban juntas
    ----------------------------------------------------
    **Todo lo que se cierra se anota.** Eso es el historial: qué pasó, quién lo
    resolvió y cuándo, y sirve para poder mirar atrás.

    **Sólo lo que alguien marca como criterio vuelve.** Eso es la memoria: lo
    que el sistema ofrecerá la próxima vez que aparezca una incidencia de la
    misma clase.

    Antes se guardaba todo como criterio, y eso convertía cada decisión de un
    martes cualquiera en una regla para el futuro sin que nadie lo hubiera
    querido. Una excepción —«esta vez lo dejamos pasar»— es justamente lo
    contrario de un criterio, y el sistema no puede confundirlas: si las
    confunde, la segunda vez recomienda hacer una excepción, que es un
    contrasentido.

    Quien decide cuál de las dos cosas es no es el sistema: es la persona que
    cierra, y se le pregunta.

    Lo que se guarda son las dos columnas del guion de Fabián, y las dos hacen
    falta por razones distintas:

    **Registro trazable** —patrón, evidencias, decisión, justificación, persona
    y versión— es lo que permite auditar la decisión después. Sin la
    justificación, dentro de seis meses hay un número y nadie sabe por qué.

    **Contexto de reutilización** —cliente, producto, tipo de incidencia,
    condiciones, roles— es lo que permite saber si el criterio *aplica* a un caso
    nuevo. Un precedente sin contexto es una regla disfrazada: se acabaría
    aplicando donde no toca, que es peor que no tenerlo.

    La versión no es decorativa: si mañana se decide otra cosa para el mismo
    patrón, el criterio anterior no se borra. Se versiona, y se puede ver que
    cambió y cuándo.
    """
    ruta = Path(ruta or RUTA)
    registros = cargar(ruta)
    clase = clase_de(discrepancia)
    # La versión cuenta CRITERIOS de esta clase, no decisiones. Dos excepciones
    # seguidas no son «la versión 3 del criterio»: son dos veces que no hubo
    # criterio ninguno.
    version = sum(1 for r in registros
                  if r.get("clase") == clase and r.get("es_criterio")) + 1
    if fase != "cerrada":
        version = None          # una propuesta no versiona ningún criterio
    registro = {
        # --- Registro trazable
        "clase": clase,
        "campo": discrepancia.get("campo"),
        "etiqueta": discrepancia.get("etiqueta"),
        "pedido": pedido,
        "decision": decision,
        "justificacion": justificacion,
        "diagnostico": diagnostico,
        "valor_cliente": str(discrepancia.get("valor_cliente")),
        "valor_orden": str(discrepancia.get("valor_orden")),
        "evidencias": list(evidencias or []),
        "validada_por": quien,
        "propuesta_por": propuesta_por,
        "cuando": _ahora(),
        "fase": fase,
        "version": version,
        "valor_decidido": (None if valor_decidido is None
                           else str(valor_decidido)),
        # ¿Esto vuelve la próxima vez, o se queda como lo que pasó aquel día?
        # Una propuesta no vuelve nunca: todavía no ha decidido nada.
        "es_criterio": bool(es_criterio) and fase == "cerrada",
        # --- Contexto de reutilización
        "contexto": dict(contexto or {}),
        "autorizados": list(autorizados or []),
    }
    registros.append(registro)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(registros, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return registro


def precedentes(discrepancia, ruta=None, excepto=None):
    """
    Las veces que ya se resolvió una incidencia de esta misma clase.

    `excepto` saca de la lista el pedido que se está mirando. Sin eso, en cuanto
    se cierra una alarma su propio registro vuelve como «precedente» de sí misma
    — que es cierto y es inútil: un caso no se sienta precedente a sí mismo.

    Sólo cuentan los registros marcados como criterio. Una decisión cerrada como
    excepción está en el historial y **no** aquí: para eso se marcó como
    excepción.
    """
    clase = clase_de(discrepancia)
    return [r for r in cargar(ruta)
            if r.get("clase") == clase and r.get("es_criterio")
            and r.get("pedido") != excepto]


def historial(ruta=None):
    """
    Todo lo que se ha cerrado, lo más reciente primero.

    Es la otra mitad de `precedentes()`: aquí está **lo que pasó** —excepciones
    incluidas— y allí está **lo que se aprendió**. Son dos preguntas distintas y
    por eso son dos listas distintas; si fueran la misma, una de las dos
    pantallas del cierre sobraría.
    """
    return list(reversed(cargar(ruta)))


def sugerencia(discrepancia, ruta=None, contexto=None, excepto=None):
    """
    Qué se hizo las otras veces, y si hay bastante acuerdo para ofrecerlo.

    Devuelve `None` cuando no hay precedentes. Cuando los hay pero no coinciden
    entre sí, se dicen los dos números y **no se sugiere nada**: que el sistema
    recuerde no le da derecho a resolver el desacuerdo entre dos decisiones
    humanas anteriores.

    Si se pasa el `contexto` del caso actual, los precedentes cuyas condiciones
    de aplicación no se cumplen **se descartan y se dice por qué**. Es la
    diferencia entre recordar y aplicar a ciegas.
    """
    todos = precedentes(discrepancia, ruta, excepto=excepto)
    previos, descartados = [], []
    for r in todos:
        vale, por_que = aplica_a(r, contexto) if contexto else (True, "")
        (previos if vale else descartados).append(
            r if vale else {**r, "descartado_porque": por_que})
    if not previos:
        if descartados:
            return {"casos": 0, "descartados": descartados, "ofrecer": False,
                    "decision": None, "unanime": False, "reparto": {},
                    "ultimo": descartados[-1],
                    "motivo": ("Hay casos parecidos, pero sus condiciones de "
                               "aplicación no se cumplen aquí.")}
        return None
    cuenta = {}
    for r in previos:
        cuenta[r["decision"]] = cuenta.get(r["decision"], 0) + 1
    mayoritaria, n = max(cuenta.items(), key=lambda kv: kv[1])
    unanime = len(cuenta) == 1
    return {
        "casos": len(previos),
        "descartados": descartados,
        "decision": mayoritaria,
        "unanime": unanime,
        "reparto": cuenta,
        "ultimo": previos[-1],
        "ofrecer": unanime and len(previos) >= MINIMO_PARA_SUGERIR,
        "motivo": ("Se ha resuelto igual todas las veces."
                   if unanime else
                   "Se ha resuelto de formas distintas: el sistema lo enseña "
                   "pero no elige por nadie."),
    }


def aplica_a(registro, contexto):
    """
    ¿Este criterio vale para el caso que hay delante?

    Un precedente sin condiciones de aplicación es una regla disfrazada: se
    acabaría aplicando donde no toca. Aquí se comprueban las que el registro
    declaró — hoy el cliente y el tipo de documento — y **la ausencia de
    condición no bloquea**: un criterio que no declaró cliente vale para
    cualquiera, porque así se guardó.
    """
    guardado = registro.get("contexto") or {}
    for clave in ("cliente", "tipo_documento"):
        esperado, actual = guardado.get(clave), (contexto or {}).get(clave)
        if esperado and actual and esperado != actual:
            return False, (f"el criterio se guardó para {clave} «{esperado}» y "
                           f"este caso es «{actual}»")
    return True, "las condiciones con las que se guardó se cumplen"


def resumen(ruta=None):
    """Para el panel de memoria: cuánto sabe el sistema y de qué."""
    registros = cargar(ruta)
    cerradas = [r for r in registros if r.get("fase", "cerrada") == "cerrada"]
    propuestas = [r for r in registros if r.get("fase") == "propuesta"]
    criterios = [r for r in registros if r.get("es_criterio")]
    clases = {}
    for r in criterios:
        clases.setdefault(r["clase"], []).append(r)
    return {
        "acciones": len(registros),
        "decisiones": len(cerradas),
        "propuestas": len(propuestas),
        "criterios": len(criterios),
        "excepciones": len(cerradas) - len(criterios),
        "clases": len(clases),
        "ultimas": list(reversed(registros[-5:])),
        "ultimos_criterios": list(reversed(criterios[-5:])),
        "por_clase": {k: len(v) for k, v in clases.items()},
    }


def olvidar(ruta=None):
    """Borra la memoria. Existe para poder repetir la demostración limpia."""
    ruta = Path(ruta or RUTA)
    if ruta.is_file():
        ruta.unlink()
