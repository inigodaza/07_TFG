"""
El recorrido de la aplicación: de una bandeja de documentos a una decisión firme.

Qué demuestra
--------------
Que las cinco piezas del proyecto no son cinco programas: son un circuito. Un
documento entra por un lado y sale por el otro convertido en una decisión con
autor, con fecha y con rastro. Y que en medio hay tres cosas que hoy, en una
empresa, hace una persona a mano y con suerte:

    1  darse cuenta de que dos papeles del mismo pedido no dicen lo mismo
    2  saber a quién le toca decidir
    3  que la decisión quede guardada de forma que la próxima consulta la use

Las seis pantallas
-------------------
    BANDEJA     entran documentos y se leen uno a uno
    AVISO       aparece la incongruencia, con su tamaño
    PANEL       el sistema encamina la incidencia a la herramienta que le toca
    HERRAMIENTA la herramienta emite su salida y el evaluador la contrasta
    VALIDACION  alguien de la empresa decide, según lo que su puesto le permite
    CIERRE      se vuelve a preguntar por el pedido y ya responde otra cosa

Nada de esto está escrito a mano. La incidencia sale de leer los PDF, el
encaminado sale del tipo de incidencia, y quién puede cerrarla sale del
organigrama. Si mañana cambian los documentos, cambia el recorrido.

Una advertencia que se mantiene
--------------------------------
La salida del módulo de Juan **se le entrega** al sistema; no se va a buscar. Es
la frontera declarada del trabajo y no desaparece porque la demo la enseñe
bonita. En la pantalla se dice, en una línea, en el paso que corresponde.
"""

import re

from modulos import auditoria

# ---------------------------------------------------------------------------
# Las seis pantallas
# ---------------------------------------------------------------------------
PASOS = [
    ("bandeja", "Bandeja", "Los documentos entran y se leen"),
    ("aviso", "Aviso", "Algo no cuadra"),
    ("panel", "Panel", "A qué herramienta le toca"),
    ("herramienta", "Herramienta", "Qué dice el módulo"),
    ("validacion", "Validación", "Quién decide, y si puede"),
    ("cierre", "Cierre", "La decisión, guardada"),
]

CLAVES = [p[0] for p in PASOS]


def siguiente(paso):
    i = CLAVES.index(paso)
    return CLAVES[min(i + 1, len(CLAVES) - 1)]


def indice(paso):
    return CLAVES.index(paso) if paso in CLAVES else 0


# ---------------------------------------------------------------------------
# 1 · La bandeja
# ---------------------------------------------------------------------------

def _tipo(doc, clasificar=None):
    """El tipo ya anotado, o el que diga la regla del módulo."""
    return doc.get("tipo") or (clasificar or auditoria.clasificar)(doc["texto"])


def referencia(doc, clasificar=None):
    """
    Con qué pedido va este documento.

    Se usa el ISBN, que es lo que de verdad los une: aparece en el presupuesto,
    en el pedido del cliente y en la orden de fabricación, y no depende de cómo
    se haya llamado al fichero. Agrupar por nombre de fichero funcionaría en esta
    bandeja y fallaría en cuanto alguien renombrara un PDF.
    """
    t = _tipo(doc, clasificar)
    campos = (auditoria.campos_orden(doc["texto"]) if t == "orden"
              else auditoria.campos_cliente(doc["texto"]))
    if campos.get("isbn"):
        return _isbn_normal(campos["isbn"])
    # El mismo ISBN se imprime de dos maneras: «9782021621099» en un documento y
    # «978-2-0216-2109-9» en el otro. Agrupar por la cadena tal cual dejaba los
    # dos documentos del mismo pedido en grupos distintos, y entonces ninguno
    # tenía con qué contrastarse: el sistema decía «falta la orden» teniéndola
    # delante. Es el mismo número, y se compara como número.
    m = re.search(r"\b(?:\d[-\s]?){12}\d\b", doc.get("texto") or "")
    return (_isbn_normal(m.group(0)) if m
            else (doc.get("nombre") or "sin referencia"))


def _isbn_normal(v):
    """Sin guiones ni espacios: «978-2-0216-2109-9» → «9782021621099»."""
    return re.sub(r"[^\d]", "", str(v or "")) or str(v or "")


def numero_de_orden(docs, clasificar=None):
    """
    El número de O.F. del pedido, que es como lo llama la gente.

    Agrupar por ISBN es lo correcto —es lo que de verdad une los tres
    documentos— pero enseñar «pedido 9780000000024» en un aviso no lo entiende
    nadie. El número de orden se saca de la propia orden de fabricación; si no
    aparece, se devuelve `None` y la pantalla usa la referencia técnica en vez de
    inventarse una.
    """
    for d in docs:
        if _tipo(d, clasificar) != "orden":
            continue
        m = re.search(r"O\.?\s?F\.?\s*N?[ºo°]?\s*(\d{4,})",
                      d.get("texto") or "", re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def referencias(doc, clasificar=None):
    """
    TODOS los ISBN que menciona un documento, no sólo el primero.

    Lo descubrió el pedido de Cambridge: la orden de compra es de un **pack** y
    cita tres ISBN —el del pack y los dos libros que contiene—, mientras que la
    orden de fabricación es de uno solo de ellos. Agrupando por el primero que
    aparece, los dos documentos del mismo trabajo caían en grupos distintos y el
    sistema decía «falta la orden» teniéndola delante.

    Se filtran por prefijo 978/979, que es lo que hace que un número de trece
    cifras sea un ISBN y no una referencia cualquiera.
    """
    vistos, salida = set(), []
    campos = auditoria.campos_orden(doc["texto"]) \
        if _tipo(doc, clasificar) == "orden" \
        else auditoria.campos_cliente(doc["texto"])
    for bruto in [campos.get("isbn")] + re.findall(
            r"\b(?:\d[-\s]?){12}\d\b", doc.get("texto") or ""):
        n = _isbn_normal(bruto)
        if n and n.startswith(("978", "979")) and n not in vistos:
            vistos.add(n)
            salida.append(n)
    return salida


def agrupar(docs, clasificar=None):
    """
    Los documentos repartidos por pedido, conservando el orden de llegada.

    Dos documentos van juntos si **comparten algún ISBN**, no si coinciden en el
    primero. Es como lo haría una persona: mira si hablan del mismo libro.
    """
    grupos, claves = {}, {}
    for d in docs:
        refs = referencias(d, clasificar)
        destino = next((claves[r] for r in refs if r in claves), None)
        if destino is None:
            destino = refs[0] if refs else (d.get("nombre") or "sin referencia")
            grupos[destino] = []
        for r in refs:
            claves[r] = destino
        grupos[destino].append(d)
    return grupos


def procesar(docs, clasificar=None, modo="determinista"):
    """
    Lee la bandeja pedido a pedido y devuelve qué ha encontrado en cada uno.

    Cada entrada lleva el estado del pedido y, si lo hay, las discrepancias que
    **el sistema ha deducido leyendo los documentos** — no una lista escrita a
    mano. Los estados posibles son tres, y los tres son respuestas:

        limpio       se ha podido contrastar y todo cuadra
        incidencia   se ha podido contrastar y algo no cuadra
        incompleto   falta documentación para poder contrastar

    «Incompleto» no es un fallo del sistema: es el sistema diciendo que con lo
    que tiene delante no puede afirmar nada, que es exactamente lo que hace este
    proyecto en todo lo demás.
    """
    salida = []
    for ref, grupo in agrupar(docs, clasificar).items():
        orden = numero_de_orden(grupo, clasificar)
        entrada = {
            "referencia": ref,
            "orden_de_fabricacion": orden,
            # Lo que se enseña: el número de O.F. si lo hay, y si no la
            # referencia técnica, sin disimular que lo es.
            "etiqueta": f"O.F. {orden}" if orden else f"ISBN {ref}",
            "documentos": [{"nombre": d.get("nombre"),
                            "tipo": _tipo(d, clasificar),
                            "paginas": d.get("paginas"),
                            "via": d.get("via")} for d in grupo],
            "n": len(grupo),
        }
        try:
            esperados, contexto = auditoria.verdad_de_campo(grupo, modo)
        except ValueError as e:
            entrada.update({"estado": "incompleto", "motivo": str(e),
                            "discrepancias": [], "contexto": None})
            salida.append(entrada)
            continue
        entrada.update({
            "estado": "incidencia" if esperados else "limpio",
            "motivo": "", "discrepancias": esperados, "contexto": contexto,
            "grupo": grupo,
        })
        salida.append(entrada)
    return salida


ORDEN_SEVERIDAD = {"critica": 0, "alta": 1, "media": 2, "menor": 3}


def primera_incidencia(resultados):
    """El primer pedido que no cuadra, y la discrepancia más grave que tiene."""
    for r in resultados:
        if r["estado"] == "incidencia":
            peor = sorted(r["discrepancias"],
                          key=lambda d: ORDEN_SEVERIDAD.get(
                              d.get("severidad_esperada"), 9))[0]
            return {**r, "principal": peor}
    return None


# ---------------------------------------------------------------------------
# 2 · El encaminado
# ---------------------------------------------------------------------------
# Qué herramienta atiende cada clase de incidencia. Está aquí, a la vista y en
# una tabla, en vez de repartido por la interfaz: encaminar es una decisión del
# sistema y tiene que poder discutirse y comprobarse como cualquier otra.
HERRAMIENTAS = [
    {"id": "auditoria", "nombre": "Auditoría de pedidos",
     "responsable": "Juan Salas",
     "atiende": "discrepancia entre documentos del mismo pedido",
     "clases": ("discrepancia_documental",)},
    {"id": "vigencia", "nombre": "Vigencia documental",
     "responsable": "Martín de Lucas",
     "atiende": "contratos y anexos que caducan o se prorrogan",
     "clases": ("vencimiento",)},
    {"id": "similitud", "nombre": "Similitud de proyectos",
     "responsable": "Álvaro Subias",
     "atiende": "trabajos parecidos ya hechos en el histórico",
     "clases": ("presupuesto_nuevo",)},
    {"id": "contradicciones", "nombre": "Contradicciones y validación",
     "responsable": "Mencía Viñuelas",
     "atiende": "decisiones humanas sobre conflictos ya detectados",
     "clases": ("validacion",)},
]


def clase_de(incidencia):
    """Qué clase de incidencia es. Hoy sólo se produce una, y se dice."""
    return "discrepancia_documental" if incidencia else None


def encaminar(incidencia):
    """
    A qué herramienta va esta incidencia, y por qué.

    Devuelve `(herramienta, motivo)`. Que el sistema elija —en vez de que elija
    la persona— es la mitad del valor: quien recibe el aviso no tiene por qué
    saber cuál de las cinco herramientas le corresponde a lo que le acaba de
    saltar.
    """
    clase = clase_de(incidencia)
    for h in HERRAMIENTAS:
        if clase in h["clases"]:
            campos = ", ".join(sorted({d["etiqueta"]
                                       for d in incidencia["discrepancias"]}))
            return h, (f"La incidencia es una discrepancia entre la orden de "
                       f"fabricación y la documentación de cliente del mismo "
                       f"pedido ({campos}). De eso se ocupa «{h['nombre']}».")
    return None, "No hay ninguna herramienta declarada para esta clase de incidencia."


# ---------------------------------------------------------------------------
# 3 · El tamaño del problema
# ---------------------------------------------------------------------------

# Los campos que cuentan EJEMPLARES. Sólo de ésos tiene sentido decir «tantos
# de más» y «tantas veces lo pedido».
CAMPOS_CONTABLES = ("cantidad",)


def impacto(discrepancia, coste_unitario=None):
    """
    Cuánto es «no cuadra», en unidades y, si alguien lo aporta, en dinero.

    Sólo para los campos que cuentan ejemplares. Un gramaje de 250 donde se
    pidieron 240 **no son «10 unidades de más»** ni «una vez lo pedido»: son
    diez gramos por metro cuadrado, y la resta no significa nada parecido. La
    versión anterior lo calculaba igual para cualquier campo numérico y sacaba
    frases que no querían decir nada — que es peor que no decir nada, porque
    parecen un dato.

    El coste unitario **no se inventa**: llega vacío y sólo aparece si quien mira
    la demo lo escribe. Un número de euros sacado de la nada convertiría una
    demostración en un folleto, y el primero que preguntara de dónde sale se
    llevaría por delante todo lo demás.
    """
    if (discrepancia.get("campo") or "") not in CAMPOS_CONTABLES:
        return None
    try:
        a = float(str(discrepancia.get("valor_cliente")).replace(".", "").replace(",", "."))
        b = float(str(discrepancia.get("valor_orden")).replace(".", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    if a == b:
        return None
    exceso = b - a
    out = {
        "pedido": a, "ordenado": b, "exceso": exceso,
        "veces": round(b / a, 1) if a else None,
        "porcentaje": round(100 * exceso / a, 1) if a else None,
    }
    if coste_unitario:
        try:
            out["coste"] = round(abs(exceso) * float(coste_unitario), 2)
        except (TypeError, ValueError):
            pass
    return out
